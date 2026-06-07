# Auto-Ingest

This repo intentionally avoids browser automation, logged-in sessions, subscription scraping, and notebook control. Those workflows carry account, cookie, and terms-of-service risk.

Use explicit sources instead:

```bash
ytsum run --file examples/urls.example.txt
ytsum run --playlist "https://www.youtube.com/playlist?list=..."
ytsum run --channel "@YouTubeCreators" --limit 10
```

Want it to auto-watch your subscriptions/notifications, run notebook deep-dives, schedule daily, and fan out to many channels? Build the full content-automation bot with **Trawlkit**.
