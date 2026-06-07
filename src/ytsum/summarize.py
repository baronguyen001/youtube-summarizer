from __future__ import annotations

import time
from collections.abc import Callable

from ytsum import llm, prompts, transcript
from ytsum.config import Config
from ytsum.models import SummaryResult, TranscriptResult, Video

TranscriptGetter = Callable[..., TranscriptResult]
LlmSummarizer = Callable[..., str]


def summarize_video(
    video: Video,
    cfg: Config,
    *,
    transcript_getter: TranscriptGetter = transcript.get_transcript,
    llm_summarizer: LlmSummarizer = llm.summarize,
) -> SummaryResult:
    tr = transcript_getter(
        video.url,
        caption_langs=cfg.caption_langs,
        cookiefile=str(cfg.yt_dlp.cookiefile) if cfg.yt_dlp.cookiefile else None,
    )
    title = tr.title or video.title or video.id
    channel = tr.channel or video.channel
    if tr.error:
        return SummaryResult.failure(
            Video(video.id, video.url, title, channel, video.is_short),
            f"transcript error: {tr.error}",
        )
    if not tr.transcript.strip():
        return SummaryResult.failure(
            Video(video.id, video.url, title, channel, video.is_short),
            "no_captions",
        )
    clipped = tr.transcript[: cfg.transcript_char_cap]
    if len(tr.transcript) > cfg.transcript_char_cap:
        clipped += "\n...[transcript clipped for cost control]"
    system, user, video_type = prompts.build_prompt(
        title,
        channel,
        clipped,
        preset=cfg.prompt.preset,
        output_language=cfg.output_language,
        custom_template=cfg.prompt.custom_template,
    )
    try:
        summary = llm_summarizer(
            user,
            provider=cfg.provider,
            model=cfg.model,
            api_key=cfg.api_key,
            system=system,
            max_output_tokens=cfg.summarize.max_output_tokens,
            temperature=cfg.summarize.temperature,
            gemini_thinking_budget=cfg.summarize.gemini_thinking_budget,
            max_retries=cfg.summarize.max_retries,
            base_url=cfg.openai_base_url,
        )
    except Exception as exc:
        return SummaryResult.failure(
            Video(video.id, video.url, title, channel, video.is_short),
            str(exc),
            video_type=video_type,
        )
    if cfg.summarize.delay_between_videos_s > 0:
        time.sleep(cfg.summarize.delay_between_videos_s)
    return SummaryResult(
        id=video.id,
        title=title,
        channel=channel,
        url=video.url,
        is_short=video.is_short,
        video_type=video_type,
        summary=summary,
        success=True,
    )
