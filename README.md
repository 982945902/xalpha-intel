# xalpha-intel

Local investment intelligence service built around `xalpha`.

It provides:

- A FastAPI backend that wraps xalpha fund data and portfolio-style group analysis.
- A React dashboard for market/fund intelligence.
- A fund workbench that supports single fund lookup and multi-fund groups.

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
- `GET /api/funds/{code}`
- `GET /api/funds/{code}/summary`
- `POST /api/analyze/fund`
- `POST /api/groups/analyze`

This is research tooling, not financial advice.
