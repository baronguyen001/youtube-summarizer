# Config

Copy `configs/ytsum.example.yaml` to `ytsum.yaml` and pass `--config ytsum.yaml`.

- `provider`: `gemini`, `claude`, or `openai`.
- `model`: optional override. Defaults are provider-specific.
- `output_language`: requested summary language, default `en`.
- `caption_langs`: caption language priority, default `[en]`.
- `transcript_char_cap`: maximum transcript characters sent to the provider.
- `db_path`: SQLite path for deduplication and retry state.
- `openai_base_url`: optional OpenAI-compatible endpoint.
- `summarize.temperature`: provider temperature.
- `summarize.max_output_tokens`: output cap.
- `summarize.gemini_thinking_budget`: set to `0` for cost-optimized Gemini Flash usage.
- `summarize.delay_between_videos_s`: optional delay between calls.
- `retry.max_attempts`: transient failures are skipped after this count.
- `prompt.preset`: `auto`, or force `tech`, `tutorial`, `finance`, `business`, `news`, `general`.
- `delivery.targets`: any of `stdout`, `markdown`, `html`, `telegram`.
- `yt_dlp.cookiefile`: optional escape hatch for public videos that need cookies.

Keys come from environment variables only: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY`.

Want it to auto-watch your subscriptions/notifications, run notebook deep-dives, schedule daily, and fan out to many channels? Build the full content-automation bot with **Trawlkit**.
