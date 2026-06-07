from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yt_dlp

from ytsum.models import Video

YOUTUBE_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})")


def from_url(url: str, *, title: str = "", channel: str = "") -> Video:
    return Video(
        id=_video_id(url), url=url, title=title, channel=channel, is_short="/shorts/" in url
    )


def from_file(path: str | Path) -> list[Video]:
    videos: list[Video] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        videos.append(from_url(value))
    return videos


def from_playlist(url: str, *, limit: int | None = None) -> list[Video]:
    return _flat_extract(url, limit=limit)


def from_channel(url_or_handle: str, *, limit: int | None = None) -> list[Video]:
    target = _normalize_channel(url_or_handle)
    return _flat_extract(target, limit=limit)


def _flat_extract(url: str, *, limit: int | None) -> list[Video]:
    opts: dict[str, Any] = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    if limit:
        opts["playlistend"] = limit
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries", []) if isinstance(info, dict) else []
    return [_video_from_entry(entry) for entry in entries if isinstance(entry, dict)]


def _video_from_entry(entry: dict[str, Any]) -> Video:
    url = str(entry.get("url") or entry.get("webpage_url") or "")
    if url and not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"
    return Video(
        id=str(entry.get("id") or _video_id(url)),
        url=url,
        title=str(entry.get("title") or ""),
        channel=str(entry.get("channel") or entry.get("uploader") or ""),
        is_short="/shorts/" in url,
    )


def _video_id(url: str) -> str:
    match = YOUTUBE_ID_RE.search(url)
    if match:
        return match.group(1)
    cleaned = url.rstrip("/").split("/")[-1]
    return cleaned[:64] or "unknown"


def _normalize_channel(value: str) -> str:
    if value.startswith("http"):
        return value
    if value.startswith("@"):
        return f"https://www.youtube.com/{value}/videos"
    return value


def unique(videos: Iterable[Video]) -> list[Video]:
    seen: set[str] = set()
    result: list[Video] = []
    for video in videos:
        if video.id in seen:
            continue
        seen.add(video.id)
        result.append(video)
    return result
