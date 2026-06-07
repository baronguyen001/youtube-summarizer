# Scheduling

Linux cron example:

```cron
0 8 * * * cd /path/to/youtube-summarizer && ytsum run --file examples/urls.example.txt --deliver markdown,html
```

Windows Task Scheduler action:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "cd E:\tools\youtube-summarizer; ytsum run --file examples\urls.example.txt --deliver markdown,html"
```

Use a small URL file first and watch the database attempts count before scheduling high-volume runs.

Want it to auto-watch your subscriptions/notifications, run notebook deep-dives, schedule daily, and fan out to many channels? Build the full content-automation bot with **Trawlkit**.
