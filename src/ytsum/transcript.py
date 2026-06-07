from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import requests
import yt_dlp

from ytsum.models import TranscriptResult


@dataclass(frozen=True, slots=True)
class CaptionTrack:
    url: str
    language: str
    is_auto: bool


def get_transcript(
    video_url: str,
    *,
    caption_langs: Sequence[str] = ("en",),
    cookiefile: str | None = None,
    request_timeout: int = 30,
    max_retries: int = 2,
) -> TranscriptResult:
    try:
        info = _extract_info(video_url, caption_langs=caption_langs, cookiefile=cookiefile)
    except Exception as exc:
        return TranscriptResult("", "", 0, "", "", str(exc)[:200])
    title = str(info.get("title", ""))
    channel = str(info.get("channel", "") or info.get("uploader", ""))
    duration = int(info.get("duration") or 0)
    track = _pick_caption_track(info, caption_langs)
    if track is None:
        return TranscriptResult(title, channel, duration, "", "", "no_captions")
    text = _fetch_subtitle_requests(
        track.url,
        timeout=request_timeout,
        max_retries=max_retries,
        cookiefile=cookiefile,
    )
    if text:
        return TranscriptResult(title, channel, duration, track.language, text, "")
    return TranscriptResult(title, channel, duration, track.language, "", "http_429")


def _extract_info(
    video_url: str,
    *,
    caption_langs: Sequence[str],
    cookiefile: str | None,
) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": list(caption_langs),
        "subtitlesformat": "json3",
        "quiet": True,
        "no_warnings": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    if not isinstance(info, dict):
        raise RuntimeError("yt-dlp returned no video info")
    return info


def _pick_caption_track(info: dict[str, Any], langs: Sequence[str]) -> CaptionTrack | None:
    for is_auto, collection_name in ((False, "subtitles"), (True, "automatic_captions")):
        collection = info.get(collection_name, {})
        if not isinstance(collection, dict):
            continue
        for lang in langs:
            entries = collection.get(lang)
            if not entries:
                continue
            best = _prefer_json3(entries)
            if best:
                url = str(best.get("url", ""))
                if url:
                    return CaptionTrack(url=url, language=lang, is_auto=is_auto)
    return None


def _prefer_json3(entries: Any) -> dict[str, Any] | None:
    if not isinstance(entries, list):
        return None
    for entry in entries:
        if isinstance(entry, dict) and entry.get("ext") == "json3":
            return entry
    for entry in entries:
        if isinstance(entry, dict):
            return entry
    return None


def _fetch_subtitle_requests(
    url: str,
    *,
    timeout: int = 30,
    max_retries: int = 2,
    cookiefile: str | None = None,
) -> str | None:
    cookies = _load_cookiefile(cookiefile) if cookiefile else None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout, cookies=cookies)
        except requests.RequestException:
            return None
        if response.status_code == 200:
            return _parse_json3(response.text)
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(2 * (attempt + 1))
            continue
        return None
    return None


def _load_cookiefile(cookiefile: str | None) -> requests.cookies.RequestsCookieJar | None:
    del cookiefile
    return None


def _parse_json3(text: str) -> str:
    """Parse YouTube JSON3 subtitle into plain text.

    Skip auto-caption sliding-window events (aAppend=1) to dedupe about half of the noise:
    YouTube emits intermediate append events and final events for the same speech, and keeping
    only final events materially reduces LLM input tokens.
    """
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return ""

    texts = []
    last_chunk = ""
    for event in data.get("events", []):
        if event.get("aAppend") == 1:
            continue
        chunk_parts = []
        for seg in event.get("segs", []):
            t = seg.get("utf8", "").strip()
            if t and t != "\n":
                chunk_parts.append(t)
        if not chunk_parts:
            continue
        chunk = " ".join(chunk_parts)
        if chunk == last_chunk:
            continue
        texts.append(chunk)
        last_chunk = chunk
    return " ".join(texts)
