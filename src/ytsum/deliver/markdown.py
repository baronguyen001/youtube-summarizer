from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ytsum.models import SummaryResult


def write(results: list[SummaryResult], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = directory / f"youtube_summary_{stamp}.md"
    lines = [
        "# YouTube Summary Digest",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for index, result in enumerate(results, 1):
        lines.extend(
            [
                f"## {index}. {result.title or result.id}",
                "",
                f"- Channel: {result.channel or 'unknown'}",
                f"- URL: {result.url}",
                f"- Type: {result.video_type}",
                f"- Status: {'success' if result.success else 'failed'}",
                "",
                result.summary.strip() if result.success else f"Error: {result.error_message}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
