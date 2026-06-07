from __future__ import annotations

from pathlib import Path

from ytsum.models import SummaryResult
from ytsum.store import (
    get_failed_videos,
    get_recent_summaries,
    get_summary_stats,
    init_db,
    is_processed,
    save_run_log,
    save_video,
)


def test_store_dedup_attempts_and_permanent_fail(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    init_db(db)

    fail = SummaryResult(
        id="v1",
        title="Private",
        channel="Chan",
        url="https://youtu.be/private",
        is_short=False,
        video_type="general",
        summary="",
        success=False,
        error_message="private video",
    )
    save_video(db, fail)
    assert get_failed_videos(db) == []

    retryable = SummaryResult(
        id="v2",
        title="Transient",
        channel="Chan",
        url="https://youtu.be/transient",
        is_short=False,
        video_type="tech",
        summary="",
        success=False,
        error_message="http 503",
    )
    save_video(db, retryable)
    save_video(db, retryable)
    failed = get_failed_videos(db, max_attempts=4)
    assert [video.id for video in failed] == ["v2"]

    success = SummaryResult(
        id="v2",
        title="Transient",
        channel="Chan",
        url="https://youtu.be/transient",
        is_short=False,
        video_type="tech",
        summary="done",
        success=True,
    )
    save_video(db, success)
    assert is_processed(db, "v2") is True
    assert get_summary_stats(db)["tech"] == {"total": 1, "success": 1}
    save_run_log(db, total=1, success=1, fail=0, telegram_sent=False)
    recent = get_recent_summaries(db)
    assert recent[0]["id"] == "v2"


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    init_db(db)
    init_db(db)
    assert db.exists()
