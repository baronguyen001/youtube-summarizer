from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

from ytsum import store

ATOM = "http://www.w3.org/2005/Atom"
YT = "http://www.youtube.com/xml/schemas/2015"
MEDIA = "http://search.yahoo.com/mrss/"
NAMESPACES = {"atom": ATOM, "yt": YT, "media": MEDIA}


def parse_feed(xml_text: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml_text)
    channel = _text(root.find("atom:author/atom:name", NAMESPACES)) or _text(
        root.find("atom:title", NAMESPACES)
    )
    entries: list[dict[str, str]] = []
    for entry in root.findall("atom:entry", NAMESPACES):
        video_id = _text(entry.find("yt:videoId", NAMESPACES))
        title = _text(entry.find("atom:title", NAMESPACES)) or _text(
            entry.find("media:group/media:title", NAMESPACES)
        )
        entries.append(
            {
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                "published": _text(entry.find("atom:published", NAMESPACES)),
            }
        )
    return entries


def feed_url_for(channel: str) -> str:
    parsed = urlparse(channel)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return channel
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"


def fetch_feed(url: str, *, timeout: int = 15) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def unseen(entries: list[dict[str, Any]], db_path: str | Path) -> list[dict[str, Any]]:
    return [
        entry
        for entry in entries
        if not store.is_processed(db_path, str(entry.get("video_id", "")))
    ]


def _text(element: ElementTree.Element[str] | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()
