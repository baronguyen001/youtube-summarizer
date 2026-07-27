from datetime import datetime
from pathlib import Path
from typing import Any

from ytsum.deliver import digest


def _row(id_: str, title: str, summary: str = "summary text") -> dict[str, Any]:
    return {
        "id": id_,
        "title": title,
        "channel": "Channel",
        "url": f"u{id_}",
        "processed_at": "2025-01-01",
        "summary": summary,
        "type": "Video",
    }


def test_html_includes_related_block() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<div class="related">Related: <a href="u2">Two</a> (0.5000)</div>' in html


def test_html_without_related_has_no_related_block() -> None:
    rows = [_row("v1", "One")]
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5))
    assert '<div class="related">' not in html


def test_html_missing_id_in_mapping_has_no_related() -> None:
    rows = [_row("v1", "One")]
    related = {"other": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<div class="related">' not in html


def test_html_empty_related_list_renders_nothing() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": []}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<div class="related">' not in html


def test_html_escapes_related_title() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "<b>Bold</b>", "url": "u2", "similarity": 0.5}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<a href="u2">&lt;b&gt;Bold&lt;/b&gt;</a> (0.5000)' in html
    assert "<b>Bold</b>" not in html


def test_html_multiple_related_keep_order_and_four_decimals() -> None:
    rows = [_row("v1", "One")]
    related = {
        "v1": [
            {"id": "v2", "title": "Two", "url": "u2", "similarity": 0.4213},
            {"id": "v3", "title": "Three", "url": "u3", "similarity": 0.31},
        ]
    }
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert (
        '<div class="related">Related: <a href="u2">Two</a> (0.4213), '
        '<a href="u3">Three</a> (0.3100)</div>' in html
    )


def test_markdown_includes_related_line() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert "**Related:** [Two](u2) (0.5000)" in md


def test_markdown_without_related_has_no_related_line() -> None:
    rows = [_row("v1", "One")]
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5))
    assert "**Related:**" not in md


def test_markdown_missing_id_in_mapping_has_no_related() -> None:
    rows = [_row("v1", "One")]
    related = {"other": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert "**Related:**" not in md


def test_markdown_empty_related_list_has_no_related() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": []}
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert "**Related:**" not in md


def test_html_related_title_falls_back_to_id() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "url": "u2", "similarity": 0.25}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<div class="related">Related: <a href="u2">v2</a> (0.2500)</div>' in html


def test_html_related_title_falls_back_to_untitled() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"url": "u2", "similarity": 0.25}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert '<div class="related">Related: <a href="u2">untitled</a> (0.2500)</div>' in html


def test_markdown_related_title_falls_back_to_id_then_untitled() -> None:
    rows = [_row("v1", "One")]
    related = {
        "v1": [
            {"id": "v2", "url": "u2", "similarity": 0.1},
            {"url": "u3", "similarity": 0.2},
        ]
    }
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert "**Related:** [v2](u2) (0.1000), [untitled](u3) (0.2000)" in md


def test_similarity_renders_four_decimal_places() -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    html = digest.render_html(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    md = digest.render_markdown(rows, generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related)
    assert "(0.5000)" in html
    assert "(0.5000)" in md


def test_write_html_forwards_related(tmp_path: Path) -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    out = tmp_path / "digest.html"
    result = digest.write(
        rows, out, fmt="html", generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related
    )
    assert result == out
    text = out.read_text(encoding="utf-8")
    assert '<div class="related">Related: <a href="u2">Two</a> (0.5000)</div>' in text


def test_write_markdown_forwards_related(tmp_path: Path) -> None:
    rows = [_row("v1", "One")]
    related = {"v1": [{"id": "v2", "title": "Two", "url": "u2", "similarity": 0.5}]}
    out = tmp_path / "digest.md"
    result = digest.write(
        rows, out, fmt="markdown", generated_at=datetime(2026, 1, 2, 3, 4, 5), related=related
    )
    assert result == out
    text = out.read_text(encoding="utf-8")
    assert "**Related:** [Two](u2) (0.5000)" in text
