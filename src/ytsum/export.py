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


def _tags_for(summary: dict[str, Any], tags: dict[str, list[str]]) -> list[str]:
    return tags.get(str(summary.get("id", "")), [])


def to_json(
    summaries: list[dict[str, Any]],
    *,
    tags: dict[str, list[str]] | None = None,
) -> str:
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        row = _row(summary)
        if tags is not None:
            row["tags"] = _tags_for(summary, tags)
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False, indent=2)


def to_csv(
    summaries: list[dict[str, Any]],
    *,
    tags: dict[str, list[str]] | None = None,
) -> str:
    fieldnames = EXPORT_FIELDS if tags is None else [*EXPORT_FIELDS, "tags"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for summary in summaries:
        row = _row(summary)
        if tags is not None:
            row["tags"] = ";".join(_tags_for(summary, tags))
        writer.writerow(row)
    return buffer.getvalue()


def write(
    summaries: list[dict[str, Any]],
    out_path: str | Path,
    *,
    fmt: str = "json",
    tags: dict[str, list[str]] | None = None,
) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = to_csv(summaries, tags=tags) if fmt == "csv" else to_json(summaries, tags=tags)
    # newline="" keeps the CSV writer's own CRLF endings intact; without it Windows
    # translates them to CRCRLF, which readers surface as blank rows between records.
    path.write_text(text, encoding="utf-8", newline="")
    return path
