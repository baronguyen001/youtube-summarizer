from typing import Any

from ytsum import textsim


def _make_row(
    row_id: str,
    title: str,
    summary: str = "",
    processed_at: str = "2024-01-01T00:00:00",
) -> dict[str, Any]:
    return {
        "id": row_id,
        "title": title,
        "channel": "",
        "url": f"http://example.com/{row_id}",
        "video_type": "video",
        "summary": summary,
        "processed_at": processed_at,
    }


def test_keywords_by_id_top_one() -> None:
    rows = [
        _make_row("s1", "alpha alpha", "shared shared"),
        _make_row("s2", "beta beta", "shared shared"),
        _make_row("s3", "gamma gamma", "shared shared"),
    ]
    result = textsim.keywords_by_id(rows, top=1)
    assert result == {"s1": ["alpha"], "s2": ["beta"], "s3": ["gamma"]}


def test_keywords_by_id_top_two() -> None:
    rows = [
        _make_row("s1", "alpha alpha", "shared shared"),
        _make_row("s2", "beta beta", "shared shared"),
    ]
    result = textsim.keywords_by_id(rows, top=2)
    assert result["s1"] == ["alpha", "shared"]
    assert result["s2"] == ["beta", "shared"]


def test_keywords_by_id_top_zero_and_negative() -> None:
    rows = [_make_row("s1", "alpha alpha", "shared shared")]
    assert textsim.keywords_by_id(rows, top=0) == {"s1": []}
    assert textsim.keywords_by_id(rows, top=-3) == {"s1": []}


def test_keywords_by_id_empty() -> None:
    assert textsim.keywords_by_id([], top=5) == {}


def test_keywords_by_id_duplicate_id_last_wins() -> None:
    rows = [_make_row("s1", "alpha"), _make_row("s1", "beta")]
    assert textsim.keywords_by_id(rows, top=1) == {"s1": ["beta"]}


def test_keywords_by_id_builds_tfidf_once() -> None:
    calls: list[int] = []
    original = textsim.build_tfidf

    def counting(docs: list[list[str]]) -> list[dict[str, float]]:
        calls.append(1)
        return original(docs)

    textsim.build_tfidf = counting
    try:
        textsim.keywords_by_id([_make_row("a", "x"), _make_row("b", "y")], top=1)
        textsim.keywords_by_id([], top=5)
    finally:
        textsim.build_tfidf = original
    assert len(calls) == 2


def _related_rows() -> list[dict[str, Any]]:
    return [
        _make_row("a", "alpha beta", "", "2024-01-01T00:00:00"),
        _make_row("b", "alpha gamma", "", "2024-01-03T00:00:00"),
        _make_row("c", "beta delta", "", "2024-01-02T00:00:00"),
        _make_row("d", "alpha beta epsilon", "", "2024-01-04T00:00:00"),
    ]


def test_related_map_ordering_and_self_exclusion() -> None:
    rows = _related_rows()
    result = textsim.related_map(rows, top=3)
    assert list(result.keys()) == ["a", "b", "c", "d"]
    assert [item["id"] for item in result["a"]] == ["d", "b", "c"]
    assert all(item["id"] != "a" for item in result["a"])


def test_related_map_top_two() -> None:
    rows = _related_rows()
    result = textsim.related_map(rows, top=2)
    assert [item["id"] for item in result["a"]] == ["d", "b"]


def test_related_map_top_zero() -> None:
    rows = _related_rows()
    result = textsim.related_map(rows, top=0)
    assert all(items == [] for items in result.values())


def test_related_map_single_row() -> None:
    result = textsim.related_map([_make_row("only", "alpha")], top=3)
    assert result == {"only": []}


def test_related_map_empty() -> None:
    assert textsim.related_map([], top=3) == {}


def test_related_map_drops_zero_similarity() -> None:
    rows = _related_rows() + [_make_row("e", "zeta eta")]
    result = textsim.related_map(rows, top=10)
    for source_id, items in result.items():
        assert all(item["id"] != source_id for item in items)
        assert all(item["similarity"] > 0.0 for item in items)
    assert "e" not in [item["id"] for item in result["a"]]


def test_related_map_builds_tfidf_once() -> None:
    calls: list[int] = []
    original = textsim.build_tfidf

    def counting(docs: list[list[str]]) -> list[dict[str, float]]:
        calls.append(1)
        return original(docs)

    textsim.build_tfidf = counting
    try:
        textsim.related_map(_related_rows(), top=2)
        textsim.related_map([_make_row("z", "foo")], top=2)
    finally:
        textsim.build_tfidf = original
    assert len(calls) == 2


def test_related_map_entry_keys_and_types() -> None:
    rows = _related_rows()
    result = textsim.related_map(rows, top=1)
    entry = result["a"][0]
    assert set(entry.keys()) == {"id", "title", "url", "similarity"}
    assert isinstance(entry["similarity"], float)
    assert entry["similarity"] > 0.0
