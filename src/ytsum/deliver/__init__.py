from __future__ import annotations

import os
from pathlib import Path

from ytsum.config import Config
from ytsum.deliver import html, markdown, stdout, telegram
from ytsum.models import SummaryResult


def dispatch(results: list[SummaryResult], cfg: Config) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for target in cfg.delivery.targets:
        if target == "stdout":
            stdout.render(results)
            outputs[target] = "printed"
        elif target == "markdown":
            outputs[target] = str(markdown.write(results, Path(cfg.delivery.markdown_dir)))
        elif target == "html":
            outputs[target] = str(html.write(results, Path(cfg.delivery.html_dir)))
        elif target == "telegram":
            ok = telegram.send_all(
                results,
                token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
                chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            )
            outputs[target] = "sent" if ok else "skipped"
        else:
            outputs[target] = "unknown target"
    return outputs
