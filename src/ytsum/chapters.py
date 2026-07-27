"""Split a transcript into deterministic, evenly sized chapters (stdlib only)."""

from __future__ import annotations

import re
from typing import Any

_SENTENCE_RE = re.compile(r"(?<=[.!?])(?=\s|$)")


def split_sentences(text: str) -> list[str]:
    """Split *text* into stripped sentences, dropping empty fragments."""
    if not text.strip():
        return []
    parts = _SENTENCE_RE.split(text)
    return [part.strip() for part in parts if part.strip()]


def format_timestamp(seconds: int) -> str:
    """Return a timestamp clamped to non-negative seconds."""
    total = max(0, seconds)
    if total < 3600:
        minutes = total // 60
        secs = total % 60
        return f"{minutes:02d}:{secs:02d}"
    hours = total // 3600
    remaining = total % 3600
    minutes = remaining // 60
    secs = remaining % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _make_title(sentence: str, *, limit: int = 60) -> str:
    """Return a short title derived from *sentence*."""
    text = sentence.strip()
    if text and text[-1] in {".", "!", "?"}:
        text = text[:-1]
    if len(text) <= limit:
        return text
    cut = text[: limit - 3]
    last_space = cut.rfind(" ")
    if last_space != -1:
        cut = cut[:last_space].rstrip()
    return f"{cut}..."


def build_chapters(
    transcript: str,
    *,
    duration: int = 0,
    chapters: int = 5,
) -> list[dict[str, Any]]:
    """Split *transcript* into deterministic chapters."""
    if chapters < 1:
        raise ValueError("chapters must be at least 1")
    sentences = split_sentences(transcript)
    if not sentences:
        raise ValueError("transcript is empty")

    lengths = [len(sentence) for sentence in sentences]
    total = sum(lengths)
    before: list[int] = [0]
    for length in lengths[:-1]:
        before.append(before[-1] + length)

    buckets: list[list[int]] = [[] for _ in range(chapters)]
    for index, offset in enumerate(before):
        bucket_index = min(chapters - 1, (offset * chapters) // total)
        buckets[bucket_index].append(index)

    merged: list[tuple[list[int], int, int]] = []
    for bucket in buckets:
        if not bucket:
            continue
        c_start = before[bucket[0]]
        c_end = before[bucket[-1]] + lengths[bucket[-1]]
        merged.append((bucket, c_start, c_end))

    result: list[dict[str, Any]] = []
    last_index = len(merged)
    for idx, (bucket, c_start, c_end) in enumerate(merged, start=1):
        start = 0
        end = 0
        if duration > 0:
            start = round(c_start / total * duration)
            end = duration if idx == last_index else round(c_end / total * duration)
        text = " ".join(sentences[sentence_index] for sentence_index in bucket)
        chapter: dict[str, Any] = {
            "index": idx,
            "title": _make_title(sentences[bucket[0]]),
            "timestamp": format_timestamp(start),
            "start": start,
            "end": end,
            "text": text,
            "char_count": len(text),
        }
        result.append(chapter)
    return result


def render_outline(chapter_list: list[dict[str, Any]]) -> str:
    """Render a concise outline of *chapter_list*."""
    if not chapter_list:
        return ""
    lines = [
        f"{chapter['index']:>2}. [{chapter['timestamp']}] {chapter['title']}"
        for chapter in chapter_list
    ]
    return "\n".join(lines)
