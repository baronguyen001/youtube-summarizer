from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "to",
    "was",
    "we",
    "what",
    "when",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^0-9a-z]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def build_tfidf(docs: list[list[str]]) -> list[dict[str, float]]:
    idf = _idf(docs)
    return [_normalized_tfidf(doc, idf) for doc in docs]


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(term, 0.0) for term, value in a.items())


def related_summaries(
    summaries: list[dict[str, Any]],
    *,
    target_id: str | None = None,
    query: str | None = None,
    top: int = 5,
) -> list[dict[str, Any]]:
    docs = [_summary_tokens(row) for row in summaries]
    vectors = build_tfidf(docs)
    if target_id is not None:
        target_index = _find_summary_index(summaries, target_id)
        target_vector = vectors[target_index]
        ranked = [
            (_with_similarity(row, cosine(target_vector, vectors[index])), row)
            for index, row in enumerate(summaries)
            if index != target_index
        ]
    elif query is not None:
        query_vector = _normalized_tfidf(tokenize(query), _idf(docs))
        ranked = [
            (_with_similarity(row, cosine(query_vector, vector)), row)
            for row, vector in zip(summaries, vectors, strict=True)
        ]
    else:
        raise ValueError("target_id or query is required")
    return _rank(ranked)[: max(0, top)]


def library_keywords(
    summaries: list[dict[str, Any]],
    *,
    top: int = 15,
) -> list[tuple[str, float]]:
    totals: dict[str, float] = {}
    for vector in build_tfidf([_summary_tokens(row) for row in summaries]):
        for term, weight in vector.items():
            totals[term] = totals.get(term, 0.0) + weight
    return [
        (term, round(weight, 4))
        for term, weight in sorted(totals.items(), key=lambda item: (-item[1], item[0]))[
            : max(0, top)
        ]
    ]


def summary_keywords(
    summaries: list[dict[str, Any]],
    target_id: str,
    *,
    top: int = 10,
) -> list[tuple[str, float]]:
    target_index = _find_summary_index(summaries, target_id)
    vector = build_tfidf([_summary_tokens(row) for row in summaries])[target_index]
    return [
        (term, round(weight, 4))
        for term, weight in sorted(vector.items(), key=lambda item: (-item[1], item[0]))[
            : max(0, top)
        ]
    ]


def _summary_tokens(row: dict[str, Any]) -> list[str]:
    return tokenize(f"{row.get('title', '')} {row.get('channel', '')} {row.get('summary', '')}")


def _idf(docs: list[list[str]]) -> dict[str, float]:
    doc_count = len(docs)
    document_frequency: Counter[str] = Counter()
    for doc in docs:
        document_frequency.update(set(doc))
    return {
        term: math.log((1 + doc_count) / (1 + frequency)) + 1
        for term, frequency in document_frequency.items()
    }


def _normalized_tfidf(doc: list[str], idf: dict[str, float]) -> dict[str, float]:
    if not doc:
        return {}
    counts = Counter(doc)
    total = sum(counts.values())
    vector = {term: (count / total) * idf[term] for term, count in counts.items() if term in idf}
    norm = math.sqrt(sum(weight * weight for weight in vector.values()))
    if norm == 0.0:
        return {}
    return {term: weight / norm for term, weight in vector.items()}


def _find_summary_index(summaries: list[dict[str, Any]], target_id: str) -> int:
    for index, row in enumerate(summaries):
        if str(row.get("id", "")) == target_id:
            return index
    raise ValueError(f"summary id not found: {target_id}")


def _with_similarity(row: dict[str, Any], similarity: float) -> dict[str, Any]:
    return {**row, "similarity": round(similarity, 4)}


def _rank(
    scored: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[dict[str, Any]]:
    ranked = sorted(scored, key=lambda pair: str(pair[1].get("id", "")))
    ranked.sort(key=lambda pair: str(pair[1].get("processed_at", "")), reverse=True)
    ranked.sort(key=lambda pair: float(pair[0]["similarity"]), reverse=True)
    return [item for item, _ in ranked]


def keywords_by_id(summaries: list[dict[str, Any]], *, top: int = 5) -> dict[str, list[str]]:
    """Top distinctive terms per summary id, building the tf-idf matrix only once."""
    vectors = build_tfidf([_summary_tokens(row) for row in summaries])
    result: dict[str, list[str]] = {}
    for row, vector in zip(summaries, vectors, strict=True):
        row_id = str(row.get("id", ""))
        if top <= 0:
            result[row_id] = []
            continue
        ranked = sorted(vector.items(), key=lambda item: (-item[1], item[0]))
        result[row_id] = [term for term, _ in ranked[:top]]
    return result


def related_map(
    summaries: list[dict[str, Any]],
    *,
    top: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """Related summaries for every id, building the tf-idf matrix only once."""
    vectors = build_tfidf([_summary_tokens(row) for row in summaries])
    result: dict[str, list[dict[str, Any]]] = {}
    for row in summaries:
        result[str(row.get("id", ""))] = []
    if top <= 0:
        return result
    for i, row_i in enumerate(summaries):
        candidates: list[tuple[float, dict[str, Any]]] = []
        for j, row_j in enumerate(summaries):
            if i == j:
                continue
            rounded = round(cosine(vectors[i], vectors[j]), 4)
            if rounded <= 0.0:
                continue
            candidates.append((rounded, row_j))
        candidates.sort(key=lambda cand: str(cand[1].get("id", "")))
        candidates.sort(key=lambda cand: str(cand[1].get("processed_at", "")), reverse=True)
        candidates.sort(key=lambda cand: cand[0], reverse=True)
        result[str(row_i.get("id", ""))] = [
            {
                "id": str(candidate.get("id", "")),
                "title": str(candidate.get("title", "")),
                "url": str(candidate.get("url", "")),
                "similarity": score,
            }
            for score, candidate in candidates[:top]
        ]
    return result
