from __future__ import annotations

import json

import pytest

from ytsum.models import SummaryResult


@pytest.fixture
def json3_blob() -> str:
    return json.dumps(
        {
            "events": [
                {"segs": [{"utf8": "Hello"}]},
                {"aAppend": 1, "segs": [{"utf8": "Hello wor"}]},
                {"segs": [{"utf8": "Hello world"}]},
                {"segs": [{"utf8": "Hello world"}]},
                {"segs": [{"utf8": "Next"}, {"utf8": " point"}]},
                {"segs": [{"utf8": "\n"}]},
            ]
        }
    )


@pytest.fixture
def summary_result() -> SummaryResult:
    return SummaryResult(
        id="abc123",
        title="Build a CLI",
        channel="Example Channel",
        url="https://www.youtube.com/watch?v=abc123abc12",
        is_short=False,
        video_type="tech",
        summary="## Summary\n**Useful** demo\n- first point\n- second point",
        success=True,
    )
