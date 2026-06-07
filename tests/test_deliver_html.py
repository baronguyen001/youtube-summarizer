from __future__ import annotations

from pathlib import Path

from ytsum.deliver.html import _markdown_to_html, write
from ytsum.models import SummaryResult


def test_markdown_to_html_escapes_and_formats() -> None:
    html = _markdown_to_html("## Head\n**bold**\n- <tag>")
    assert "<h4>Head</h4>" in html
    assert "<strong>bold</strong>" in html
    assert "&lt;tag&gt;" in html


def test_write_html_digest(tmp_path: Path, summary_result: SummaryResult) -> None:
    path = write([summary_result], tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "YouTube Summary Digest" in text
    assert "Build a CLI" in text
