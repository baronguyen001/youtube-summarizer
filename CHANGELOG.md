# Changelog

## v0.4.0

- Added `ytsum chapters` - split any transcript JSON into deterministic, evenly sized chapters with proportional timestamps and an outline or `--json` view. Pure stdlib, no provider call.
- Added `ytsum digest --related N` - each card now links its N nearest stored summaries (HTML and Markdown). Opt-in: without the flag the report is unchanged.
- Added `ytsum export --tags N` - appends a `tags` column with each summary's N most distinctive TF-IDF terms (`;`-joined in CSV, a list in JSON). Opt-in: without the flag the export shape is unchanged.
- Added `textsim.related_map` and `textsim.keywords_by_id`, which build the TF-IDF matrix once for the whole library instead of once per row.
- Fixed: CSV exports no longer get a blank row between records on Windows (`write` kept the writer's CRLF endings from being doubled).

## v0.3.0

- Added `ytsum related` - find similar stored summaries with deterministic TF-IDF cosine ranking, by stored id or free-text query.
- Added `ytsum feed` - list recent videos from a public YouTube channel RSS feed or local Atom XML file, with `--new` filtering against the local store.
- Added `ytsum keywords` - surface distinctive library-wide themes or per-summary TF-IDF terms.
- All three commands are keyless, additive, and covered by deterministic offline tests.

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
