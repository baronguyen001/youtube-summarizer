from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ytsum.models import SummaryResult, Video

MAX_RETRY_ATTEMPTS = 4

PERMANENT_ERROR_PATTERNS = (
    "no_captions",
    "video unavailable",
    "removed by the uploader",
    "is not available",
    "private video",
    "members-only",
    "this video is private",
    "video has been removed",
    "copyright claim",
)


def init_db(path: str | Path) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                url TEXT,
                is_short INTEGER DEFAULT 0,
                video_type TEXT DEFAULT '',
                success INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',
                error_message TEXT,
                processed_at TEXT,
                run_session TEXT,
                attempts INTEGER DEFAULT 0,
                permanent_fail INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT,
                total_videos INTEGER,
                success_count INTEGER,
                fail_count INTEGER,
                telegram_sent INTEGER DEFAULT 0
            )
            """
        )
        _migrate_videos(conn)
        conn.commit()


def _migrate_videos(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(videos)").fetchall()}
    migrations = {
        "summary": "ALTER TABLE videos ADD COLUMN summary TEXT DEFAULT ''",
        "video_type": "ALTER TABLE videos ADD COLUMN video_type TEXT DEFAULT ''",
        "attempts": "ALTER TABLE videos ADD COLUMN attempts INTEGER DEFAULT 0",
        "permanent_fail": "ALTER TABLE videos ADD COLUMN permanent_fail INTEGER DEFAULT 0",
    }
    for column, statement in migrations.items():
        if column not in existing:
            conn.execute(statement)
            if column == "attempts":
                conn.execute("UPDATE videos SET attempts = 1 WHERE success = 0")
    if "permanent_fail" not in existing:
        for pattern in PERMANENT_ERROR_PATTERNS:
            conn.execute(
                """
                UPDATE videos SET permanent_fail = 1
                WHERE success = 0 AND LOWER(COALESCE(error_message,'')) LIKE ?
                """,
                (f"%{pattern}%",),
            )


def is_processed(path: str | Path, video_id: str) -> bool:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT success FROM videos WHERE id = ?", (video_id,)).fetchone()
    return row is not None and row[0] == 1


def save_video(path: str | Path, result: SummaryResult, run_session: str = "") -> None:
    init_db(path)
    with sqlite3.connect(path) as conn:
        prev = conn.execute("SELECT attempts FROM videos WHERE id = ?", (result.id,)).fetchone()
        prev_attempts = int(prev[0]) if prev else 0
        attempts = 0 if result.success else prev_attempts + 1
        permanent = 0 if result.success else int(_is_permanent_error(result.error_message))
        conn.execute(
            """
            INSERT OR REPLACE INTO videos
            (id, title, channel, url, is_short, video_type, success, summary,
             error_message, processed_at, run_session, attempts, permanent_fail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.id,
                result.title,
                result.channel,
                result.url,
                int(result.is_short),
                result.video_type,
                int(result.success),
                result.summary if result.success else "",
                "" if result.success else result.error_message,
                datetime.now().isoformat(timespec="seconds"),
                run_session,
                attempts,
                permanent,
            ),
        )
        conn.commit()


def get_failed_videos(
    path: str | Path,
    *,
    limit: int = 20,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
) -> list[Video]:
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, title, channel, url, is_short FROM videos
            WHERE success = 0
              AND COALESCE(permanent_fail, 0) = 0
              AND COALESCE(attempts, 0) < ?
            ORDER BY processed_at DESC
            LIMIT ?
            """,
            (max_attempts, limit),
        ).fetchall()
    return [
        Video(
            id=str(row["id"]),
            url=str(row["url"]),
            title=str(row["title"] or ""),
            channel=str(row["channel"] or ""),
            is_short=bool(row["is_short"]),
        )
        for row in rows
    ]


def save_run_log(
    path: str | Path,
    *,
    total: int,
    success: int,
    fail: int,
    telegram_sent: bool,
) -> None:
    init_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO run_logs (run_at, total_videos, success_count, fail_count, telegram_sent)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                total,
                success,
                fail,
                int(telegram_sent),
            ),
        )
        conn.commit()


def get_summaries(path: str | Path, *, days: int | None = None) -> list[dict[str, Any]]:
    """Return successful summaries, newest first. ``days=None`` returns the whole library."""
    init_db(path)
    where = "WHERE success = 1 AND summary != ''"
    params: tuple[Any, ...] = ()
    if days is not None:
        where += " AND processed_at >= datetime('now', ?)"
        params = (f"-{int(days)} days",)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT id, title, channel, url, video_type, summary, processed_at
            FROM videos {where}
            ORDER BY processed_at DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_summaries(path: str | Path, days: int = 7) -> list[dict[str, Any]]:
    return get_summaries(path, days=days)


def search_summaries(path: str | Path, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Deterministic ranked search over stored summaries (title/channel weighted 3x)."""
    terms = [term for term in re.split(r"\s+", query.strip().lower()) if term]
    if not terms:
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in get_summaries(path):
        heading = f"{row['title']} {row['channel']}".lower()
        body = str(row["summary"]).lower()
        score = sum(3 * heading.count(term) + body.count(term) for term in terms)
        if score > 0:
            scored.append((score, row))
    # Stable sort: recency desc first, then score desc -> ties keep newest first.
    scored.sort(key=lambda item: str(item[1]["processed_at"]), reverse=True)
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{**row, "score": score} for score, row in scored[: max(0, limit)]]


def get_summary_stats(path: str | Path) -> dict[str, dict[str, int]]:
    init_db(path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """
            SELECT video_type, COUNT(*) as total,
                   SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as success
            FROM videos
            GROUP BY video_type
            """
        ).fetchall()
    return {
        str(row[0] or "unknown"): {"total": int(row[1]), "success": int(row[2] or 0)}
        for row in rows
    }


def _is_permanent_error(error: str) -> bool:
    if not error:
        return False
    lower = error.lower()
    return any(pattern in lower for pattern in PERMANENT_ERROR_PATTERNS)
