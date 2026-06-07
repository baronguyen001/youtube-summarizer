from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Video:
    id: str
    url: str
    title: str = ""
    channel: str = ""
    is_short: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Video:
        return cls(
            id=str(data.get("id", "")),
            url=str(data.get("url", "")),
            title=str(data.get("title", "")),
            channel=str(data.get("channel", "")),
            is_short=bool(data.get("is_short", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TranscriptResult:
    title: str
    channel: str
    duration: int
    language: str
    transcript: str
    error: str = ""


@dataclass(slots=True)
class SummaryResult:
    id: str
    title: str
    channel: str
    url: str
    is_short: bool
    video_type: str
    summary: str
    success: bool
    error_message: str = ""

    @classmethod
    def failure(cls, video: Video, message: str, video_type: str = "general") -> SummaryResult:
        return cls(
            id=video.id,
            title=video.title,
            channel=video.channel,
            url=video.url,
            is_short=video.is_short,
            video_type=video_type,
            summary="",
            success=False,
            error_message=message,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
