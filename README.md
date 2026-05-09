# xalpha-intel

Local investment intelligence service built around `xalpha`.

It provides:

- A FastAPI backend that wraps xalpha fund data and portfolio-style group analysis.
- A React dashboard for market/fund intelligence.
- A fund workbench that supports single fund lookup and multi-fund groups.
- Optional Codex CLI analysis with deterministic rule-based fallback.
- A sentiment layer that combines fund announcements, topic news, and AI/rule-based bullish-bearish signals.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

cd frontend
bun install
cd ..
```

Run backend:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8128
```

Run frontend:

```bash
cd frontend
bun run dev --host 127.0.0.1 --port 5178
```

Then open:

```text
http://127.0.0.1:5178
```

## API

- `GET /api/health`
- `GET /api/funds/search?q=原油`
- `GET /api/funds/{code}`
- `GET /api/funds/{code}/summary`
- `POST /api/analyze/fund`
- `POST /api/groups/analyze`
- `POST /api/analyze/group`
- `POST /api/sentiment/fund`
- `POST /api/sentiment/group`

AI analysis tries to call local `codex exec` first. If Codex is unavailable, times out, or returns
no usable text, the API returns a rule-based analysis with `analysis.source = "rules"` so the UI
stays usable.

Environment knobs:

```bash
export CODEX_BIN=codex
export CODEX_ANALYSIS_TIMEOUT=45
export SENTIMENT_NEWS_TIMEOUT=6
```

Sentiment analysis uses xalpha/Eastmoney fund announcements and Google News RSS keyword searches.
Codex summarizes the combined materials when available; otherwise the API returns deterministic rule
signals with `sentiment.analysis_source = "rules"`.

This is research tooling, not financial advice.
