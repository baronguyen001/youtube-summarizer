# Pipeline

`ytsum` takes explicit public inputs: one URL, a file of URLs, a public playlist, or a public channel uploads page.

1. `yt-dlp` reads metadata and caption-track URLs with `download=False`.
2. Manual captions are preferred before automatic captions, in `caption_langs` order.
3. json3 captions are fetched with `requests` and parsed into plain text.
4. Auto-caption `aAppend=1` events are skipped and consecutive duplicate chunks are collapsed.
5. The transcript is capped before the provider call to control cost.
6. A format-aware prompt is routed to Gemini, Claude, or OpenAI-compatible models.
7. SQLite stores success, attempts, and permanent failure flags.
8. Delivery writes to stdout, Markdown, HTML, or Telegram.

Data contracts live in `ytsum.models`: `Video`, `TranscriptResult`, and `SummaryResult`.

Want it to auto-watch your subscriptions/notifications, run notebook deep-dives, schedule daily, and fan out to many channels? Build the full content-automation bot with **Trawlkit**.
