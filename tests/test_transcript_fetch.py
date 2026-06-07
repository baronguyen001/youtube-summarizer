from __future__ import annotations

from typing import Any

import pytest

from ytsum import transcript


class FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_fetch_subtitle_requests_retries_429(
    monkeypatch: pytest.MonkeyPatch,
    json3_blob: str,
) -> None:
    responses = [FakeResponse(429), FakeResponse(200, json3_blob)]
    sleeps: list[float] = []

    def fake_get(*_: Any, **__: Any) -> FakeResponse:
        return responses.pop(0)

    monkeypatch.setattr(transcript.requests, "get", fake_get)
    monkeypatch.setattr(transcript.time, "sleep", sleeps.append)
    text = transcript._fetch_subtitle_requests("https://caption.test", max_retries=1)
    assert text == "Hello Hello world Next point"
    assert sleeps == [2]


def test_get_transcript_no_captions(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_extract(*_: Any, **__: Any) -> dict[str, Any]:
        return {"title": "No captions", "channel": "Example", "duration": 12}

    monkeypatch.setattr(transcript, "_extract_info", fake_extract)
    result = transcript.get_transcript("https://youtu.be/abc123abc12")
    assert result.error == "no_captions"
    assert result.title == "No captions"


def test_get_transcript_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_extract(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "title": "Captioned",
            "channel": "Example",
            "duration": 42,
            "subtitles": {"en": [{"ext": "json3", "url": "caption-url"}]},
        }

    def fake_fetch(url: str, **_: Any) -> str:
        assert url == "caption-url"
        return "clean transcript"

    monkeypatch.setattr(transcript, "_extract_info", fake_extract)
    monkeypatch.setattr(transcript, "_fetch_subtitle_requests", fake_fetch)
    result = transcript.get_transcript("https://youtu.be/abc123abc12")
    assert result.error == ""
    assert result.transcript == "clean transcript"
    assert result.language == "en"
