from __future__ import annotations

from pathlib import Path
from typing import Any

from ytsum.config import Config, load_config
from ytsum.models import TranscriptResult, Video
from ytsum.summarize import summarize_video


def test_load_config_nested_paths(tmp_path: Path) -> None:
    config_file = tmp_path / "ytsum.yaml"
    config_file.write_text(
        """
provider: openai
output_language: es
caption_langs: [en, es]
db_path: data/state.db
delivery:
  targets: [markdown, html]
  markdown_dir: reports
yt_dlp:
  cookiefile: cookies.txt
""",
        encoding="utf-8",
    )
    cfg = load_config(config_file)
    assert cfg.provider == "openai"
    assert cfg.output_language == "es"
    assert cfg.caption_langs == ["en", "es"]
    assert cfg.db_path == Path("data/state.db")
    assert cfg.delivery.targets == ["markdown", "html"]
    assert cfg.delivery.markdown_dir == Path("reports")
    assert cfg.yt_dlp.cookiefile == Path("cookies.txt")


def test_summarize_video_success_and_failure(monkeypatch: Any) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    video = Video(id="v1", url="https://youtu.be/abc123abc12")
    cfg = Config()

    def getter(*_: Any, **__: Any) -> TranscriptResult:
        return TranscriptResult(
            title="Python API tutorial",
            channel="Dev",
            duration=60,
            language="en",
            transcript="Install the package and call the API.",
        )

    def summarizer(prompt: str, **kwargs: Any) -> str:
        assert "Python API tutorial" in prompt
        assert kwargs["api_key"] == "test-key"
        return "summary"

    result = summarize_video(video, cfg, transcript_getter=getter, llm_summarizer=summarizer)
    assert result.success is True
    assert result.video_type == "tech"
    assert result.summary == "summary"

    def failing_getter(*_: Any, **__: Any) -> TranscriptResult:
        return TranscriptResult("", "", 0, "", "", "no_captions")

    failed = summarize_video(
        video, cfg, transcript_getter=failing_getter, llm_summarizer=summarizer
    )
    assert failed.success is False
    assert "no_captions" in failed.error_message


def test_video_serialization() -> None:
    video = Video.from_dict(
        {
            "id": "v1",
            "url": "https://youtu.be/abc123abc12",
            "title": "Title",
            "channel": "Channel",
            "is_short": True,
        }
    )
    assert video.to_dict()["is_short"] is True
