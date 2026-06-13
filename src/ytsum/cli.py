from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yt_dlp

from ytsum import __version__, sources, store
from ytsum import export as export_lib
from ytsum.config import Config, load_config
from ytsum.deliver import digest as digest_render
from ytsum.deliver.stdout import render
from ytsum.models import SummaryResult, TranscriptResult, Video
from ytsum.pipeline import run as run_pipeline
from ytsum.summarize import summarize_video


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = _build_parser()
    args = parser.parse_args(argv)
    cfg = _load_cli_config(args)
    if args.command == "summarize":
        return _cmd_summarize(args, cfg)
    if args.command == "run":
        return _cmd_run(args, cfg)
    if args.command == "retry":
        return _cmd_retry(args, cfg)
    if args.command == "stats":
        return _cmd_stats(cfg)
    if args.command == "digest":
        return _cmd_digest(args, cfg)
    if args.command == "search":
        return _cmd_search(args, cfg)
    if args.command == "export":
        return _cmd_export(args, cfg)
    if args.command == "doctor":
        return _cmd_doctor(cfg)
    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ytsum")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", help="Path to ytsum.yaml")
    parser.add_argument("--provider", choices=["gemini", "claude", "openai", "mock"])
    parser.add_argument("--model")
    parser.add_argument("--lang")
    parser.add_argument("--deliver", help="Comma-separated targets: stdout,markdown,html,telegram")
    sub = parser.add_subparsers(dest="command")
    summarize = sub.add_parser("summarize", help="Summarize one video URL")
    summarize.add_argument("url", nargs="?", help="Public YouTube URL")
    summarize.add_argument("--transcript-json", help="Offline transcript fixture")
    summarize.add_argument("--dry-run", action="store_true")
    run = sub.add_parser("run", help="Run the full pipeline")
    run.add_argument("urls", nargs="*", help="One or more public YouTube URLs")
    run.add_argument("--file")
    run.add_argument("--playlist")
    run.add_argument("--channel")
    run.add_argument("--limit", type=int)
    run.add_argument("--dry-run", action="store_true")
    retry = sub.add_parser("retry", help="Retry transient failures")
    retry.add_argument("--limit", type=int, default=20)
    sub.add_parser("stats", help="Show summary stats")
    digest = sub.add_parser("digest", help="Aggregate stored summaries into one report")
    digest.add_argument("--days", type=int, default=7, help="Look-back window (0 = whole library)")
    digest.add_argument("--format", choices=["html", "markdown"], default="html")
    digest.add_argument("--out", help="Output file (default digest_<date>.<ext>)")
    search = sub.add_parser("search", help="Search the stored summary library")
    search.add_argument("query", help="One or more keywords")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    export = sub.add_parser("export", help="Export stored summaries to JSON or CSV")
    export.add_argument("--format", choices=["json", "csv"], default="json")
    export.add_argument("--days", type=int, help="Look-back window (omit = whole library)")
    export.add_argument("--out", help="Output file (default ytsum_export.<ext>)")
    sub.add_parser("doctor", help="Check local setup")
    return parser


def _load_cli_config(args: argparse.Namespace) -> Config:
    return load_config(args.config).with_overrides(
        provider=args.provider,
        model=args.model,
        lang=args.lang,
        deliver=args.deliver,
    )


def _cmd_summarize(args: argparse.Namespace, cfg: Config) -> int:
    if args.transcript_json:
        result = _summarize_fixture(Path(args.transcript_json), cfg)
    else:
        if not args.url:
            raise SystemExit("summarize requires a URL or --transcript-json")
        result = summarize_video(sources.from_url(args.url), cfg)
    render([result])
    if not args.dry_run:
        store.save_video(cfg.db_path, result)
    return 0 if result.success else 1


def _summarize_fixture(path: Path, cfg: Config) -> SummaryResult:
    raw = json.loads(path.read_text(encoding="utf-8"))
    video = Video(
        id=str(raw.get("id", "sample")),
        url=str(raw.get("url", "offline")),
        title=str(raw.get("title", "Sample transcript")),
        channel=str(raw.get("channel", "Example")),
        is_short=bool(raw.get("is_short", False)),
    )
    tr = TranscriptResult(
        title=video.title,
        channel=video.channel,
        duration=int(raw.get("duration", 0)),
        language=str(raw.get("language", "en")),
        transcript=str(raw.get("transcript", "")),
        error="",
    )
    mock_cfg = cfg.with_overrides(provider="mock")

    def getter(*_: Any, **__: Any) -> TranscriptResult:
        return tr

    def mock_summary(prompt: str, **__: Any) -> str:
        del prompt
        return (
            "## Summary\n"
            "This offline fixture demonstrates the ytsum pipeline without a network call.\n\n"
            "## Key Points\n"
            "- Captions are parsed before the provider step.\n"
            "- Delivery can render stdout, Markdown, HTML, or Telegram.\n\n"
            "## Takeaway\n"
            "Use this path for smoke tests when no provider key is available."
        )

    return summarize_video(video, mock_cfg, transcript_getter=getter, llm_summarizer=mock_summary)


def _cmd_run(args: argparse.Namespace, cfg: Config) -> int:
    videos: list[Video] = []
    videos.extend(sources.from_url(url) for url in args.urls)
    if args.file:
        videos.extend(sources.from_file(args.file))
    if args.playlist:
        videos.extend(sources.from_playlist(args.playlist, limit=args.limit))
    if args.channel:
        videos.extend(sources.from_channel(args.channel, limit=args.limit))
    if not videos:
        raise SystemExit("run requires URLs, --file, --playlist, or --channel")
    run_pipeline(sources.unique(videos), cfg, dry_run=args.dry_run)
    return 0


def _cmd_retry(args: argparse.Namespace, cfg: Config) -> int:
    videos = store.get_failed_videos(
        cfg.db_path,
        limit=args.limit,
        max_attempts=cfg.retry.max_attempts,
    )
    if not videos:
        print("No retryable failures.")
        return 0
    run_pipeline(videos, cfg)
    return 0


def _cmd_stats(cfg: Config) -> int:
    stats = store.get_summary_stats(cfg.db_path)
    if not stats:
        print("No summaries stored yet.")
        return 0
    for video_type, values in stats.items():
        print(f"{video_type}: {values['success']}/{values['total']} successful")
    return 0


def _cmd_digest(args: argparse.Namespace, cfg: Config) -> int:
    days = None if args.days == 0 else args.days
    summaries = store.get_summaries(cfg.db_path, days=days)
    ext = "md" if args.format == "markdown" else "html"
    out = Path(args.out) if args.out else Path(f"digest_{datetime.now():%Y%m%d_%H%M%S}.{ext}")
    path = digest_render.write(summaries, out, fmt=args.format)
    print(f"Wrote {len(summaries)} summaries to {path}")
    return 0


def _cmd_search(args: argparse.Namespace, cfg: Config) -> int:
    matches = store.search_summaries(cfg.db_path, args.query, limit=args.limit)
    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
        return 0
    if not matches:
        print(f"No summaries match: {args.query}")
        return 0
    for row in matches:
        print(f"[{row['score']:>3}] {row['title']} - {row['channel']}")
        print(f"      {row['url']}")
    return 0


def _cmd_export(args: argparse.Namespace, cfg: Config) -> int:
    summaries = store.get_summaries(cfg.db_path, days=args.days)
    out = Path(args.out) if args.out else Path(f"ytsum_export.{args.format}")
    path = export_lib.write(summaries, out, fmt=args.format)
    print(f"Exported {len(summaries)} summaries to {path}")
    return 0


def _cmd_doctor(cfg: Config) -> int:
    print(f"ytsum {__version__}")
    print(f"yt-dlp {yt_dlp.version.__version__}")
    if cfg.api_key:
        print(f"{cfg.api_key_env}: set")
    else:
        print(f"{cfg.api_key_env}: missing for provider '{cfg.provider}'")
    try:
        store.init_db(cfg.db_path)
        print(f"Database writable: {cfg.db_path}")
    except Exception as exc:
        print(f"Database check failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
