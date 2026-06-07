from __future__ import annotations

from datetime import datetime

from ytsum import store
from ytsum.config import Config
from ytsum.deliver import dispatch
from ytsum.models import SummaryResult, Video
from ytsum.summarize import summarize_video


def run(videos: list[Video], cfg: Config, *, dry_run: bool = False) -> list[SummaryResult]:
    if not dry_run:
        store.init_db(cfg.db_path)
    run_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    results: list[SummaryResult] = []
    for video in videos:
        if not dry_run and store.is_processed(cfg.db_path, video.id):
            continue
        result = summarize_video(video, cfg)
        results.append(result)
        if not dry_run:
            store.save_video(cfg.db_path, result, run_session=run_session)
    if results and not dry_run:
        success = sum(1 for item in results if item.success)
        store.save_run_log(
            cfg.db_path,
            total=len(results),
            success=success,
            fail=len(results) - success,
            telegram_sent="telegram" in cfg.delivery.targets,
        )
    if results:
        dispatch(results, cfg)
    return results
