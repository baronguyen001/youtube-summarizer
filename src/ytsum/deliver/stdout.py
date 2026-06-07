from __future__ import annotations

from ytsum.models import SummaryResult


def render(results: list[SummaryResult]) -> None:
    for index, result in enumerate(results, 1):
        status = "OK" if result.success else "FAIL"
        print(f"\n[{index}] {status} {result.title or result.id}")
        if result.channel:
            print(f"Channel: {result.channel}")
        print(f"URL: {result.url}")
        print(f"Type: {result.video_type}")
        if result.success:
            print(result.summary.strip())
        else:
            print(f"Error: {result.error_message}")
