# Providers

## Gemini

Install:

```bash
pip install "youtube-summarizer[gemini]"
```

Set `GEMINI_API_KEY`. The default model is `gemini-2.5-flash-lite`, with `thinkingBudget=0` to keep summarization cheap.

## Claude

Install:

```bash
pip install "youtube-summarizer[claude]"
```

Set `ANTHROPIC_API_KEY`. The default model is `claude-haiku-4-5`. Use `claude-sonnet-4-6` when quality matters more than cost.

## OpenAI-compatible

Install:

```bash
pip install "youtube-summarizer[openai]"
```

Set `OPENAI_API_KEY`. Configure `model` and optionally `openai_base_url` for compatible gateways or local servers.

Want it to auto-watch your subscriptions/notifications, run notebook deep-dives, schedule daily, and fan out to many channels? Build the full content-automation bot with **Trawlkit**.
