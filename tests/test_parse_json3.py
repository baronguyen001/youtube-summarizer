from __future__ import annotations

from ytsum.transcript import _parse_json3, _pick_caption_track


def test_parse_json3_skips_append_and_collapses_duplicate(json3_blob: str) -> None:
    assert _parse_json3(json3_blob) == "Hello Hello world Next point"


def test_pick_caption_track_prefers_manual_json3() -> None:
    info = {
        "subtitles": {
            "en": [
                {"ext": "vtt", "url": "manual-vtt"},
                {"ext": "json3", "url": "manual-json"},
            ]
        },
        "automatic_captions": {"en": [{"ext": "json3", "url": "auto-json"}]},
    }
    track = _pick_caption_track(info, ["en"])
    assert track is not None
    assert track.url == "manual-json"
    assert track.is_auto is False
