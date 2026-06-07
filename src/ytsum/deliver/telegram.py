from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any

import requests

from ytsum.models import SummaryResult

TELEGRAM_LIMIT = 4096
PostFunc = Callable[..., Any]
SleepFunc = Callable[[float], None]


def send_all(
    results: list[SummaryResult],
    *,
    token: str,
    chat_id: str,
    post: PostFunc = requests.post,
    sleep: SleepFunc = time.sleep,
) -> bool:
    if not token or not chat_id:
        print("Telegram delivery skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set.")
        return False
    total = len(results)
    success = sum(1 for item in results if item.success)
    ok = send_message(
        f"<b>YouTube Summary Digest</b>\n{success}/{total} videos summarized",
        token=token,
        chat_id=chat_id,
        post=post,
        sleep=sleep,
    )
    for index, result in enumerate(results, 1):
        for chunk in _split_message(_format_single_video(index, result)):
            ok = send_message(chunk, token=token, chat_id=chat_id, post=post, sleep=sleep) and ok
            sleep(0.1)
    return ok


def send_message(
    text: str,
    *,
    token: str,
    chat_id: str,
    parse_mode: str = "HTML",
    post: PostFunc = requests.post,
    sleep: SleepFunc = time.sleep,
    max_retries: int = 3,
) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text[:TELEGRAM_LIMIT],
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    return _send_with_retry(url, payload, post=post, sleep=sleep, max_retries=max_retries)


def _send_with_retry(
    url: str,
    payload: dict[str, Any],
    *,
    post: PostFunc,
    sleep: SleepFunc,
    max_retries: int,
) -> bool:
    for _ in range(max_retries):
        response = post(url, json=payload, timeout=120)
        data = response.json()
        if response.status_code == 429:
            retry_after = data.get("parameters", {}).get("retry_after", 10)
            sleep(float(retry_after) + 2)
            continue
        if data.get("ok"):
            return True
        description = str(data.get("description", ""))
        if "parse" in description.lower() or "can't" in description.lower():
            payload.pop("parse_mode", None)
            continue
        return False
    return False


def _format_single_video(index: int, result: SummaryResult) -> str:
    title = _escape_html(result.title or result.id)
    channel = _escape_html(result.channel)
    lines = [f'<b>{index}. <a href="{_escape_html(result.url)}">{title}</a></b>']
    if channel:
        lines.append(f"Channel: {channel}")
    lines.append(f"Type: {_escape_html(result.video_type)}")
    lines.append("")
    if result.success:
        lines.append(_clean_for_telegram(result.summary))
    else:
        lines.append(f"Could not summarize: {_escape_html(result.error_message)}")
    return "\n".join(lines)


def _split_message(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit - 20)
        if split_at <= 0:
            split_at = limit - 20
        chunks.append(remaining[:split_at] + "\n[continued]")
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _clean_for_telegram(text: str) -> str:
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _escape_html(text.strip())


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
