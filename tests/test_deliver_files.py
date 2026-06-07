from __future__ import annotations

from pathlib import Path

from ytsum.config import Config, DeliveryConfig
from ytsum.deliver import dispatch
from ytsum.deliver.markdown import write as write_markdown
from ytsum.deliver.stdout import render
from ytsum.models import SummaryResult


def test_markdown_stdout_and_dispatch(
    tmp_path: Path,
    capsys: object,
    summary_result: SummaryResult,
) -> None:
    md_path = write_markdown([summary_result], tmp_path)
    assert "Build a CLI" in md_path.read_text(encoding="utf-8")

    render([summary_result])
    captured = capsys.readouterr()
    assert "Build a CLI" in captured.out

    cfg = Config(
        delivery=DeliveryConfig(
            targets=["markdown", "html"], markdown_dir=tmp_path, html_dir=tmp_path
        )
    )
    outputs = dispatch([summary_result], cfg)
    assert outputs["markdown"].endswith(".md")
    assert outputs["html"].endswith(".html")
