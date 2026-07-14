from __future__ import annotations

from pathlib import Path
from typing import Any

from ytsum.feeds import feed_url_for, fetch_feed, parse_feed, unseen
from ytsum.models import SummaryResult
from ytsum.store import init_db, save_video


def test_parse_feed_extracts_entries_in_feed_order() -> None:
    xml_text = Path("examples/sample_feed.xml").read_text(encoding="utf-8")

    entries = parse_feed(xml_text)

    assert [entry["video_id"] for entry in entries] == ["feedvideo01", "feedvideo02", ""]
    assert entries[0] == {
        "video_id": "feedvideo01",
        "title": "Build Offline Summaries",
        "channel": "Example Feed Channel",
        "url": "https://www.youtube.com/watch?v=feedvideo01",
        "published": "2026-01-03T10:00:00+00:00",
    }
    assert entries[2]["title"] == ""
    assert entries[2]["url"] == ""


def test_parse_feed_uses_feed_title_when_author_is_missing() -> None:
    xml_text = """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
          xmlns:media="http://search.yahoo.com/mrss/"
          xmlns="http://www.w3.org/2005/Atom">
      <title>Fallback Channel</title>
      <entry>
        <yt:videoId>fallback01</yt:videoId>
        <media:group><media:title>Media Title</media:title></media:group>
      </entry>
    </feed>
    """

    assert parse_feed(xml_text) == [
        {
            "video_id": "fallback01",
            "title": "Media Title",
            "channel": "Fallback Channel",
            "url": "https://www.youtube.com/watch?v=fallback01",
            "published": "",
        }
    ]


def test_feed_url_for_accepts_full_url_and_channel_ids() -> None:
    full_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCabcdefghijklmnopqrstuv"

    assert feed_url_for(full_url) == full_url
    assert (
        feed_url_for("UCabcdefghijklmnopqrstuv")
        == "https://www.youtube.com/feeds/videos.xml?channel_id=UCabcdefghijklmnopqrstuv"
    )
    assert feed_url_for("custom-channel") == (
        "https://www.youtube.com/feeds/videos.xml?channel_id=custom-channel"
    )


def test_fetch_feed_uses_requests_get_without_live_network(monkeypatch: Any) -> None:
    calls: list[tuple[str, int]] = []

    class Response:
        text = "<feed />"

        def raise_for_status(self) -> None:
            calls.append(("raise", 0))

    def fake_get(url: str, *, timeout: int) -> Response:
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("ytsum.feeds.requests.get", fake_get)

    assert fetch_feed("https://example.test/feed.xml", timeout=3) == "<feed />"
    assert calls == [("https://example.test/feed.xml", 3), ("raise", 0)]


def test_unseen_filters_successfully_processed_videos(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    init_db(db)
    save_video(
        db,
        SummaryResult(
            id="feedvideo01",
            title="Build Offline Summaries",
            channel="Example Feed Channel",
            url="https://www.youtube.com/watch?v=feedvideo01",
            is_short=False,
            video_type="tech",
            summary="Stored summary",
            success=True,
        ),
    )
    entries = parse_feed(Path("examples/sample_feed.xml").read_text(encoding="utf-8"))

    assert [entry["video_id"] for entry in unseen(entries, db)] == ["feedvideo02", ""]
