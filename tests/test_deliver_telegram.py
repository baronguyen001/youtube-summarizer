from __future__ import annotations

from typing import Any

from ytsum.deliver.telegram import _clean_for_telegram, _split_message, send_all
from ytsum.models import SummaryResult


class FakeResponse:
    status_code = 200

    def json(self) -> dict[str, Any]:
        return {"ok": True}


def test_split_message_respects_limit() -> None:
    chunks = _split_message("a" * 5000, limit=1000)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_clean_for_telegram_escapes_html() -> None:
    assert _clean_for_telegram("## Title\n**<danger>**") == "Title\n&lt;danger&gt;"


def test_send_all_posts_header_and_video(summary_result: SummaryResult) -> None:
    payloads: list[dict[str, Any]] = []

    def post(_: str, **kwargs: Any) -> FakeResponse:
        payloads.append(kwargs["json"])
        return FakeResponse()

    assert send_all(
        [summary_result], token="token", chat_id="chat", post=post, sleep=lambda _: None
    )
    assert len(payloads) == 2
    assert payloads[0]["chat_id"] == "chat"
    assert "Build a CLI" in payloads[1]["text"]
