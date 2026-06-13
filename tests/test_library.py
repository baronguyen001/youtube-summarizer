from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from ytsum import export
from ytsum.deliver import digest
from ytsum.models import SummaryResult
from ytsum.store import get_summaries, save_video, search_summaries


def _seed(db: Path) -> None:
    rows = [
        SummaryResult(
            id="v1",
            title="Build a Python CLI",
            channel="DevChan",
            url="https://youtu.be/v1",
            is_short=False,
            video_type="tutorial",
            summary="## Steps\n- install python\n- run the cli",
            success=True,
        ),
        SummaryResult(
            id="v2",
            title="AI model news for <devs>",
            channel="TechChan",
            url="https://youtu.be/v2",
            is_short=False,
            video_type="tech",
            summary="**Gemini** and claude updates for developers",
            success=True,
        ),
        SummaryResult(
            id="v3",
            title="Market crash analysis",
            channel="FinChan",
            url="https://youtu.be/v3",
            is_short=False,
            video_type="finance",
            summary="stocks fell; the fed raised rates",
            success=True,
        ),
    ]
    for row in rows:
        save_video(db, row)


def test_get_summaries_returns_whole_library(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _seed(db)
    summaries = get_summaries(db)
    assert {row["id"] for row in summaries} == {"v1", "v2", "v3"}
    assert all("url" in row for row in summaries)
    # days filter still works (everything was stored "now").
    assert len(get_summaries(db, days=7)) == 3


def test_search_ranks_title_over_body_and_scores(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _seed(db)
    hits = search_summaries(db, "python")
    assert [row["id"] for row in hits] == ["v1"]
    assert hits[0]["score"] == 3 * 1 + 1  # title hit (x3) + body hit
    assert search_summaries(db, "developers")[0]["id"] == "v2"
    assert search_summaries(db, "   ") == []
    assert search_summaries(db, "nonexistentterm") == []
    assert len(search_summaries(db, "the", limit=1)) <= 1


def test_digest_html_groups_and_escapes(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _seed(db)
    html = digest.render_html(get_summaries(db))
    assert "ytsum Library Digest" in html
    assert "3 summaries" in html
    assert "tutorial (1)" in html and "tech (1)" in html and "finance (1)" in html
    assert "&lt;devs&gt;" in html  # title escaped, no raw tag
    assert "<devs>" not in html


def test_digest_markdown_and_write(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _seed(db)
    out = digest.write(get_summaries(db), tmp_path / "d.md", fmt="markdown")
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# ytsum Library Digest")
    assert "## tutorial (1)" in text
    assert "](https://youtu.be/v1)" in text


def test_digest_empty_library(tmp_path: Path) -> None:
    assert "No summaries stored yet." in digest.render_html([])
    assert "_No summaries stored yet._" in digest.render_markdown([])


def test_export_json_and_csv_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _seed(db)
    summaries = get_summaries(db)

    parsed = json.loads(export.to_json(summaries))
    assert len(parsed) == 3
    assert set(parsed[0]) == set(export.EXPORT_FIELDS)

    reader = list(csv.DictReader(io.StringIO(export.to_csv(summaries))))
    assert {row["id"] for row in reader} == {"v1", "v2", "v3"}
    assert reader[0]["summary"]  # multi-line summary survives CSV quoting

    path = export.write(summaries, tmp_path / "out.csv", fmt="csv")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("id,title,channel")
