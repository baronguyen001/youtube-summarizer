from pathlib import Path
from typing import Any

from ytsum import export


def _summary(row_id: str, title: str = "T") -> dict[str, Any]:
    return {
        "id": row_id,
        "title": title,
        "channel": "C",
        "url": "http://example.com",
        "video_type": "video",
        "processed_at": "2024-01-01T00:00:00",
        "summary": "S",
    }


def test_to_json_without_tags_matches_legacy_output() -> None:
    rows = [_summary("v1")]
    expected = (
        "[\n"
        "  {\n"
        '    "id": "v1",\n'
        '    "title": "T",\n'
        '    "channel": "C",\n'
        '    "url": "http://example.com",\n'
        '    "video_type": "video",\n'
        '    "processed_at": "2024-01-01T00:00:00",\n'
        '    "summary": "S"\n'
        "  }\n"
        "]"
    )
    assert export.to_json(rows) == expected


def test_to_json_with_tags_appends_tags_column() -> None:
    rows = [_summary("v1"), _summary("v2")]
    tags = {"v1": ["foo", "bar"], "v2": []}
    out = export.to_json(rows, tags=tags)
    assert '"tags": [\n      "foo",\n      "bar"\n    ]' in out
    assert '"tags": []' in out
    assert out.index('"summary"') < out.index('"tags"')


def test_to_json_with_missing_tags_is_empty_list() -> None:
    rows = [_summary("v1")]
    out = export.to_json(rows, tags={"other": ["x"]})
    assert '"tags": []' in out


def test_to_csv_without_tags_matches_legacy_output() -> None:
    rows = [_summary("v1")]
    expected = (
        "id,title,channel,url,video_type,processed_at,summary\r\n"
        "v1,T,C,http://example.com,video,2024-01-01T00:00:00,S\r\n"
    )
    assert export.to_csv(rows) == expected


def test_to_csv_with_tags_appends_column_and_joins() -> None:
    rows = [_summary("v1"), _summary("v2")]
    tags = {"v1": ["foo", "bar"], "v2": []}
    out = export.to_csv(rows, tags=tags)
    assert out.startswith("id,title,channel,url,video_type,processed_at,summary,tags\r\n")
    lines = out.strip().split("\r\n")
    assert lines[1] == "v1,T,C,http://example.com,video,2024-01-01T00:00:00,S,foo;bar"
    assert lines[2] == "v2,T,C,http://example.com,video,2024-01-01T00:00:00,S,"


def test_to_csv_with_missing_tags_is_empty_string() -> None:
    rows = [_summary("v1")]
    out = export.to_csv(rows, tags={"other": ["x"]})
    assert out.split("\r\n")[1].endswith(",")


def test_write_json_uses_no_tags_by_default(tmp_path: Path) -> None:
    rows = [_summary("v1")]
    path = export.write(rows, tmp_path / "out.json")
    expected = (
        "[\n"
        "  {\n"
        '    "id": "v1",\n'
        '    "title": "T",\n'
        '    "channel": "C",\n'
        '    "url": "http://example.com",\n'
        '    "video_type": "video",\n'
        '    "processed_at": "2024-01-01T00:00:00",\n'
        '    "summary": "S"\n'
        "  }\n"
        "]"
    )
    assert path.read_text(encoding="utf-8") == expected


def test_write_csv_forwards_tags(tmp_path: Path) -> None:
    rows = [_summary("v1")]
    tags = {"v1": ["x"]}
    path = export.write(rows, tmp_path / "out.csv", fmt="csv", tags=tags)
    # Read bytes: the CSV writer's CRLF endings must survive to disk unchanged,
    # otherwise Windows doubles the CR and readers see a blank row per record.
    raw = path.read_bytes()
    assert raw.startswith(b"id,title,channel,url,video_type,processed_at,summary,tags\r\n")
    assert raw.endswith(b"v1,T,C,http://example.com,video,2024-01-01T00:00:00,S,x\r\n")
    assert b"\r\r\n" not in raw


def test_export_fields_not_mutated() -> None:
    export.to_csv([_summary("v1")], tags={"v1": ["x"]})
    assert export.EXPORT_FIELDS == [
        "id",
        "title",
        "channel",
        "url",
        "video_type",
        "processed_at",
        "summary",
    ]
