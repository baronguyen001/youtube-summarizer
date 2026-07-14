from __future__ import annotations

import math
from typing import Any

import pytest

from ytsum.textsim import (
    build_tfidf,
    cosine,
    library_keywords,
    related_summaries,
    summary_keywords,
    tokenize,
)


def _summaries() -> list[dict[str, Any]]:
    return [
        {
            "id": "vid-a",
            "title": "Python packaging workflow",
            "channel": "Dev Lessons",
            "url": "https://www.youtube.com/watch?v=vid-a",
            "video_type": "tech",
            "summary": "Build wheels, run ruff, run mypy, and release packages.",
            "processed_at": "2026-01-03T12:00:00",
        },
        {
            "id": "vid-b",
            "title": "Python testing guide",
            "channel": "Dev Lessons",
            "url": "https://www.youtube.com/watch?v=vid-b",
            "video_type": "tech",
            "summary": "Use pytest coverage with ruff and mypy for deterministic tests.",
            "processed_at": "2026-01-02T12:00:00",
        },
        {
            "id": "vid-c",
            "title": "Kitchen garden recipe",
            "channel": "Home Lab",
            "url": "https://www.youtube.com/watch?v=vid-c",
            "video_type": "general",
            "summary": "Tomatoes, basil, and soup recipes from a small garden.",
            "processed_at": "2026-01-04T12:00:00",
        },
    ]


def test_tokenize_lowercases_splits_and_drops_stopwords() -> None:
    assert tokenize("The QUICK, a/b test in Python 3!") == ["quick", "test", "python"]


def test_build_tfidf_returns_l2_normalized_sparse_vectors() -> None:
    vectors = build_tfidf([["alpha", "alpha", "beta"], ["beta", "gamma"]])

    assert set(vectors[0]) == {"alpha", "beta"}
    assert vectors[0]["alpha"] > vectors[0]["beta"]
    assert math.isclose(math.sqrt(sum(weight * weight for weight in vectors[0].values())), 1.0)
    assert build_tfidf([[]]) == [{}]


def test_cosine_uses_sparse_dot_product() -> None:
    assert cosine({"a": 0.6, "b": 0.8}, {"b": 0.5, "c": 0.5}) == pytest.approx(0.4)
    assert cosine({}, {"b": 0.5}) == 0.0


def test_related_summaries_by_id_excludes_target_and_ranks_similar_docs() -> None:
    related = related_summaries(_summaries(), target_id="vid-a", top=2)

    assert [row["id"] for row in related] == ["vid-b", "vid-c"]
    assert related[0]["similarity"] > related[1]["similarity"]
    assert all(row["id"] != "vid-a" for row in related)


def test_related_summaries_by_query_uses_corpus_idf_and_top_n() -> None:
    related = related_summaries(_summaries(), query="basil tomato recipe", top=1)

    assert [row["id"] for row in related] == ["vid-c"]
    assert related[0]["similarity"] > 0


def test_related_summaries_ties_by_processed_at_desc_then_id_asc() -> None:
    rows = [
        {**_summaries()[0], "id": "vid-b", "processed_at": "2026-01-01T00:00:00"},
        {**_summaries()[1], "id": "vid-a", "processed_at": "2026-01-01T00:00:00"},
        {**_summaries()[2], "id": "vid-c", "processed_at": "2026-01-02T00:00:00"},
    ]

    related = related_summaries(rows, query="unmatched", top=3)

    assert [row["id"] for row in related] == ["vid-c", "vid-a", "vid-b"]


def test_related_summaries_validates_required_and_missing_target() -> None:
    with pytest.raises(ValueError, match="required"):
        related_summaries(_summaries())
    with pytest.raises(ValueError, match="vid-missing"):
        related_summaries(_summaries(), target_id="vid-missing")
    assert related_summaries(_summaries(), query="python", top=0) == []


def test_library_keywords_ranks_summed_weights_deterministically() -> None:
    terms = library_keywords(_summaries(), top=20)

    assert len(terms) == 20
    assert terms == sorted(terms, key=lambda item: (-item[1], item[0]))
    assert any(term == "python" for term, _ in terms)
    assert len(library_keywords(_summaries(), top=5)) == 5
    assert library_keywords([], top=5) == []


def test_summary_keywords_returns_terms_for_target_and_validates_id() -> None:
    terms = summary_keywords(_summaries(), "vid-c", top=4)

    assert len(terms) == 4
    assert terms == sorted(terms, key=lambda item: (-item[1], item[0]))
    assert any(term in {"basil", "recipe", "garden"} for term, _ in terms)
    assert summary_keywords(_summaries(), "vid-c", top=0) == []
    with pytest.raises(ValueError, match="vid-missing"):
        summary_keywords(_summaries(), "vid-missing")
