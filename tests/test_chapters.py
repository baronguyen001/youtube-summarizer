"""Tests for ytsum.chapters."""

from __future__ import annotations

import pytest

from ytsum import chapters


def test_split_sentences_blank_and_whitespace() -> None:
    assert chapters.split_sentences("") == []
    assert chapters.split_sentences("   \n\t  ") == []


def test_split_sentences_normal() -> None:
    assert chapters.split_sentences("A one. B two. C three.") == [
        "A one.",
        "B two.",
        "C three.",
    ]


def test_split_sentences_mixed_punctuation_and_no_trailing() -> None:
    assert chapters.split_sentences("Hello! Are you there? No") == [
        "Hello!",
        "Are you there?",
        "No",
    ]


def test_build_chapters_rejects_zero_chapters() -> None:
    with pytest.raises(ValueError, match="chapters must be at least 1"):
        chapters.build_chapters("A.", chapters=0)


def test_build_chapters_rejects_empty_transcript() -> None:
    with pytest.raises(ValueError, match="transcript is empty"):
        chapters.build_chapters("", chapters=2)


def test_build_chapters_no_duration() -> None:
    result = chapters.build_chapters("A. B. C.", chapters=3)
    expected = [
        {
            "index": 1,
            "title": "A",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "A.",
            "char_count": 2,
        },
        {
            "index": 2,
            "title": "B",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "B.",
            "char_count": 2,
        },
        {
            "index": 3,
            "title": "C",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "C.",
            "char_count": 2,
        },
    ]
    assert result == expected


def test_build_chapters_more_chapters_than_sentences() -> None:
    result = chapters.build_chapters(
        "Sentence one. Sentence two. Sentence three.",
        chapters=99,
    )
    expected = [
        {
            "index": 1,
            "title": "Sentence one",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "Sentence one.",
            "char_count": 13,
        },
        {
            "index": 2,
            "title": "Sentence two",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "Sentence two.",
            "char_count": 13,
        },
        {
            "index": 3,
            "title": "Sentence three",
            "timestamp": "00:00",
            "start": 0,
            "end": 0,
            "text": "Sentence three.",
            "char_count": 15,
        },
    ]
    assert result == expected


def test_build_chapters_drops_empty_buckets() -> None:
    result = chapters.build_chapters(
        "A one. B two. C three.",
        duration=30,
        chapters=3,
    )
    expected = [
        {
            "index": 1,
            "title": "A one",
            "timestamp": "00:00",
            "start": 0,
            "end": 18,
            "text": "A one. B two.",
            "char_count": 13,
        },
        {
            "index": 2,
            "title": "C three",
            "timestamp": "00:18",
            "start": 18,
            "end": 30,
            "text": "C three.",
            "char_count": 8,
        },
    ]
    assert result == expected


def test_build_chapters_duration_rounding_and_last_end() -> None:
    result = chapters.build_chapters(
        "Hello world today. Goodbye.",
        duration=100,
        chapters=2,
    )
    expected = [
        {
            "index": 1,
            "title": "Hello world today",
            "timestamp": "00:00",
            "start": 0,
            "end": 69,
            "text": "Hello world today.",
            "char_count": 18,
        },
        {
            "index": 2,
            "title": "Goodbye",
            "timestamp": "01:09",
            "start": 69,
            "end": 100,
            "text": "Goodbye.",
            "char_count": 8,
        },
    ]
    assert result == expected


def test_build_chapters_single_chapter() -> None:
    result = chapters.build_chapters(
        "Part one. Part two. Part three.",
        duration=60,
        chapters=1,
    )
    expected = [
        {
            "index": 1,
            "title": "Part one",
            "timestamp": "00:00",
            "start": 0,
            "end": 60,
            "text": "Part one. Part two. Part three.",
            "char_count": 31,
        },
    ]
    assert result == expected


def test_format_timestamp_under_hour() -> None:
    assert chapters.format_timestamp(0) == "00:00"
    assert chapters.format_timestamp(65) == "01:05"


def test_format_timestamp_over_hour() -> None:
    assert chapters.format_timestamp(3600) == "1:00:00"
    assert chapters.format_timestamp(3725) == "1:02:05"


def test_format_timestamp_negative_is_clamped() -> None:
    assert chapters.format_timestamp(-5) == "00:00"


def test_make_title_short_unchanged() -> None:
    assert chapters._make_title("Hello world.") == "Hello world"
    assert chapters._make_title("No punctuation") == "No punctuation"


def test_make_title_long_with_space() -> None:
    sentence = "The quick brown fox jumps over the lazy dog repeatedly today now."
    expected = "The quick brown fox jumps over the lazy dog repeatedly..."
    assert chapters._make_title(sentence) == expected


def test_make_title_long_without_space() -> None:
    expected = "A" * 57 + "..."
    assert chapters._make_title("A" * 70) == expected


def test_make_title_empty_after_punctuation_removal() -> None:
    assert chapters._make_title(".") == ""


def test_render_outline_empty() -> None:
    assert chapters.render_outline([]) == ""


def test_render_outline_non_empty() -> None:
    chapter_list = [
        {"index": 1, "timestamp": "00:00", "title": "Intro"},
        {"index": 10, "timestamp": "01:05", "title": "Outro"},
    ]
    expected = " 1. [00:00] Intro\n10. [01:05] Outro"
    assert chapters.render_outline(chapter_list) == expected
