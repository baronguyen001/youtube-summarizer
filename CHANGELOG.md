# Changelog

## v0.2.0

- Added `ytsum digest` — aggregate the stored library into one cross-run HTML or Markdown report, grouped by detected topic.
- Added `ytsum search "<query>"` — deterministic ranked keyword search across stored summaries (title/channel weighted, `--json` output).
- Added `ytsum export` — export the summary library to portable JSON or CSV (stdlib only, `--days` look-back window).
- Added `store.get_summaries` (whole-library accessor) and `store.search_summaries`; `get_recent_summaries` now delegates to it.
- All new paths are offline and covered by deterministic, network-free tests.

## v0.1.0

- Initial CLI for URL, file, playlist, and channel inputs.
- Added json3 caption parsing with auto-caption append-event deduplication.
- Added Gemini, Claude, and OpenAI-compatible provider adapter.
- Added SQLite deduplication, retry attempts, and permanent-failure classification.
- Added stdout, Markdown, HTML, and Telegram delivery targets.
- Added mocked CI test suite with no network calls.
