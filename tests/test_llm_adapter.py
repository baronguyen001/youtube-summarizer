from __future__ import annotations

from typing import Any

import pytest

from ytsum import llm


class FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._body = body or {}
        self.text = str(self._body)
        self.ok = 200 <= status_code < 300

    def json(self) -> dict[str, Any]:
        return self._body


def test_provider_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_gemini(text: str, **kwargs: Any) -> str:
        calls.append(f"{text}:{kwargs['model']}")
        return "summary"

    monkeypatch.setattr(llm, "_summarize_gemini", fake_gemini)
    assert (
        llm.summarize(
            "prompt",
            provider="gemini",
            model=None,
            api_key="key",
            system="sys",
            max_output_tokens=10,
            temperature=0.1,
        )
        == "summary"
    )
    assert calls == ["prompt:gemini-2.5-flash-lite"]


def test_summarize_rejects_missing_key() -> None:
    with pytest.raises(RuntimeError, match="Missing API key"):
        llm.summarize(
            "prompt",
            provider="gemini",
            model=None,
            api_key="",
            system="sys",
            max_output_tokens=10,
            temperature=0.1,
        )


def test_summarize_rejects_unknown_provider() -> None:
    with pytest.raises(RuntimeError, match="Unsupported provider"):
        llm.summarize(
            "prompt",
            provider="other",
            model=None,
            api_key="key",
            system="sys",
            max_output_tokens=10,
            temperature=0.1,
        )


def test_gemini_rest_extracts_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*_: Any, **__: Any) -> dict[str, Any]:
        return {"candidates": [{"content": {"parts": [{"text": "done"}]}}]}

    monkeypatch.setattr(llm, "_post_with_retries", fake_post)
    assert (
        llm._summarize_gemini_rest(
            "prompt",
            model="gemini-test",
            api_key="key",
            system="sys",
            max_output_tokens=10,
            temperature=0.1,
            gemini_thinking_budget=0,
            max_retries=1,
            timeout=1,
        )
        == "done"
    )


def test_post_with_retries_handles_rate_limit_and_5xx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        FakeResponse(429, {"error": {"message": "slow"}}),
        FakeResponse(503, {"error": {"message": "retry"}}),
        FakeResponse(200, {"ok": True}),
    ]
    sleeps: list[float] = []

    def fake_post(*_: Any, **__: Any) -> FakeResponse:
        return responses.pop(0)

    monkeypatch.setattr(llm.requests, "post", fake_post)
    data = llm._post_with_retries(
        "https://example.test",
        {"prompt": "x"},
        api_key="secret",
        timeout=1,
        max_retries=3,
        sleep=sleeps.append,
    )
    assert data == {"ok": True}
    assert sleeps == [20, 20]


def test_post_with_retries_scrubs_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*_: Any, **__: Any) -> FakeResponse:
        return FakeResponse(400, {"error": "bad secret-key"})

    monkeypatch.setattr(llm.requests, "post", fake_post)
    with pytest.raises(RuntimeError) as error:
        llm._post_with_retries(
            "https://example.test",
            {},
            api_key="secret-key",
            timeout=1,
            max_retries=0,
            sleep=lambda _: None,
        )
    assert "secret-key" not in str(error.value)
