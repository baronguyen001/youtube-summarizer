# Quickstart

Install the package in editable mode:

```bash
pip install -e ".[gemini]"
```

Set one provider key:

```bash
export GEMINI_API_KEY="AIza_your_key_here"
```

Summarize one video:

```bash
ytsum summarize "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Run without a provider key using the synthetic fixture:

```bash
ytsum --provider mock summarize --transcript-json examples/sample_transcript.json --dry-run
```
