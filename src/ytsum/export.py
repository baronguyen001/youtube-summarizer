"""Export the stored summary library to a portable JSON or CSV file (stdlib only)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

EXPORT_FIELDS = ["id", "title", "channel", "url", "video_type", "processed_at", "summary"]


def _row(summary: dict[str, Any]) -> dict[str, Any]:
    return {field: summary.get(field, "") for field in EXPORT_FIELDS}


def to_json(summaries: list[dict[str, Any]]) -> str:
    return json.dumps([_row(item) for item in summaries], ensure_ascii=False, indent=2)


def to_csv(summaries: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for item in summaries:
        writer.writerow(_row(item))
    return buffer.getvalue()


def write(summaries: list[dict[str, Any]], out_path: str | Path, *, fmt: str = "json") -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = to_csv(summaries) if fmt == "csv" else to_json(summaries)
    path.write_text(text, encoding="utf-8")
    return path
