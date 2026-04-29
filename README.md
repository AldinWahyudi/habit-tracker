# Habit Tracker

Personal habit tracker with built-in analytics.

## Features

- Track any number of habits as **boolean per habit per date** in SQLite.
- **GitHub-style 365-day heatmap** for each habit, colored by 7-day rolling intensity.
- **Day-of-week consistency** bar chart showing average completion rate per weekday across all habits.
- **Pairwise correlation** detection — Pearson correlation across the last 90 days, with the top 3 pairs explained in plain language.
- **Weekly AI insight** — 3 bullet points analyzing patterns, anomalies, and suggestions from the past 7 days. Uses the Claude API when `ANTHROPIC_API_KEY` is set, otherwise falls back to a deterministic heuristic summary so the endpoint always works.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite, managed with [uv](https://docs.astral.sh/uv/).
- Frontend: React + TypeScript + Vite + Recharts.

## Local development

### Backend

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
uv run python -m app.seed       # optional: load demo habits + 120 days of completions
uv run uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000`. Open `http://localhost:8000/docs` for the auto-generated Swagger UI.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the backend.

## Environment

Copy `backend/.env.example` to `backend/.env`. The only optional setting is:

- `ANTHROPIC_API_KEY` — when present, the weekly insight endpoint uses Claude (`claude-3-5-sonnet-latest`). When absent, a heuristic insight is generated locally.
