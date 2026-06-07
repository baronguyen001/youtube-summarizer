from __future__ import annotations

import re
from pathlib import Path

FORMATS = {"tech", "tutorial", "finance", "business", "news", "general"}

KEYWORDS: dict[str, tuple[str, ...]] = {
    "finance": (
        "stock",
        "stocks",
        "invest",
        "portfolio",
        "market",
        "fed",
        "inflation",
        "bond",
        "bitcoin",
        "crypto",
        "earnings",
        "valuation",
        "interest rate",
    ),
    "tech": (
        "ai",
        "api",
        "model",
        "software",
        "developer",
        "programming",
        "python",
        "javascript",
        "cloud",
        "open source",
        "claude",
        "chatgpt",
        "gemini",
        "agent",
    ),
    "tutorial": (
        "tutorial",
        "how to",
        "setup",
        "install",
        "walkthrough",
        "guide",
        "step by step",
        "build",
        "fix",
        "configure",
    ),
    "business": (
        "marketing",
        "sales",
        "startup",
        "founder",
        "customer",
        "revenue",
        "strategy",
        "pricing",
        "brand",
        "growth",
        "saas",
    ),
    "news": (
        "breaking",
        "news",
        "election",
        "policy",
        "announced",
        "report",
        "war",
        "court",
        "deadline",
        "update",
    ),
}

TEMPLATES: dict[str, str] = {
    "finance": """## Situation
What happened? Include concrete prices, percentages, dates, and market moves if present.

## Analysis
Explain the causes, second-order effects, and what the speaker believes matters.

## Actions
- Practical move or watch item for an investor
- Price zone, risk level, or timing note if mentioned
- Risks and assumptions to keep in mind

## Bottom Line
One or two actionable takeaways.""",
    "tech": """## What Changed
Name the product, release, tool, model, or technical idea.

## Key Details
- Main capability or mechanism
- Comparison with prior versions or alternatives if mentioned
- Limitations, cost, or reliability notes

## Evaluation
Who should use it, who should skip it, and why.""",
    "tutorial": """## Goal
What the viewer should be able to do after the video.

## Tools
Mention software, commands, accounts, links, or materials named in the transcript.

## Steps
1. First concrete step
2. Next concrete step
3. Continue until the workflow is clear

## Tips
- Important shortcut or warning
- Common mistake to avoid""",
    "business": """## Topic
What business, marketing, or operating problem is being discussed.

## Strategy
- Concrete method, playbook, or framework
- Metrics, examples, or numbers mentioned
- Tradeoffs and constraints

## Apply It
What to try first in a real business context.""",
    "news": """## Event
What happened, when, where, and who is involved.

## Details
Important facts, numbers, quotes paraphrased from the transcript, and timeline.

## Impact
Who is affected and what could happen next.""",
    "general": """## Summary
Two or three sentences covering the main idea.

## Key Points
- Important point one
- Important point two
- Important point three if useful

## Takeaway
The strongest practical or conceptual takeaway.""",
}


def detect_format(title: str, channel: str, text: str) -> str:
    haystack = f"{title} {channel} {text[:4000]}".lower()
    scores = {
        name: sum(1 for keyword in keywords if _contains_keyword(haystack, keyword))
        for name, keywords in KEYWORDS.items()
    }
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score > 0 else "general"


def _contains_keyword(haystack: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in haystack
    return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None


def build_prompt(
    title: str,
    channel: str,
    transcript: str,
    *,
    preset: str = "auto",
    output_language: str = "en",
    custom_template: str | None = None,
) -> tuple[str, str, str]:
    video_type = detect_format(title, channel, transcript) if preset == "auto" else preset
    if video_type not in FORMATS:
        video_type = "general"
    template = (
        Path(custom_template).read_text(encoding="utf-8")
        if custom_template
        else TEMPLATES[video_type]
    )
    system = (
        "You summarize YouTube transcripts for busy technical readers. "
        "Use only facts present in the transcript. Do not invent sources, links, or claims."
    )
    user = f"""Video: {title}
Channel: {channel}

Transcript:
{transcript}

Write the summary in {output_language}. Use the format below when it fits the transcript.
Do not include meta labels such as "video type". Prefer concrete numbers, tool names,
steps, risks, and decisions. Target 300 to 600 words.

{template}"""
    return system, user, video_type
