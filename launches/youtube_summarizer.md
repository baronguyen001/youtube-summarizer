# Build-In-Public Launch Draft

I shipped `ytsum`, a small CLI for summarizing a YouTube backlog with one command.

Demo:

```bash
ytsum run --file urls.txt --provider gemini --deliver stdout,markdown,html
```

What it does:

- Uses `yt-dlp` to fetch title, channel, and caption-track URLs.
- Parses json3 captions and removes duplicate auto-caption fragments.
- Summarizes with Gemini, Claude, or any OpenAI-compatible model.
- Saves retry state in SQLite so repeated runs do not waste tokens.
- Delivers to stdout, Markdown, styled HTML, or Telegram.

No logged-in browser profile. No scraping subscriptions. No media download. Your key, your queue.

Want it to auto-watch subscriptions, run notebook deep-dives, schedule daily, and fan out to many channels? That is the bigger Trawlkit workflow.
