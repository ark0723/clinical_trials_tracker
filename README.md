# AI Clinical Trial Navigator

An evidence-grounded AI assistant for discovering, understanding, and
monitoring clinical trials.

**Mission:** Help cancer patients discover, understand, and monitor clinical
trial opportunities with transparent, evidence-grounded AI assistance
(US market; initial focus: HER2-positive breast cancer).

Built on the Clinical Trial Tracker foundation (same repo): Product Layer
(discovery, matching, saved trials, monitoring) plus Agent / ML-Data layers
(eligibility structuring, RAG, evaluation). Planning docs (local): `docs/01`–`03`.

Assistive only — potentially relevant trials, why they match, things to
confirm, and questions for a doctor — not AI treatment decisions.

## Current status & roadmap

**Foundation (done) — Clinical Trial Tracker**

- Backend: ClinicalTrials.gov sync, encrypted profiles, rule-based matching
  with travel-distance hard filters, lean trial cache.
- Frontend: health profile form and ranked matches (compatibility, criteria,
  sites, nearest-site miles).

**Next (product-first):** Patient Journey Platform — **Understanding**,
saved trials, monitoring/alerts — then AI understanding (paid tier), then
LangGraph Navigator (with Planner) + MCP + evaluation, then personalized
decision support and platform expansion.

**Hosting path (decided):** Frontend on **Vercel**, API on **Fly.io**, DB on
**Neon**. Daily trial sync stays on GitHub Actions. ngrok is only for local
experiments.

## Project structure

```
backend/   # FastAPI + SQLAlchemy backend (see backend/README.md)
frontend/  # React + TypeScript frontend (see frontend/README.md)
docs/      # Planning docs: project goals, user requirements, feature spec
           # (local-only, gitignored -- not tracked in this repo)
```

## Getting started

- Backend setup, local Postgres via Docker, migrations, and the
  ClinicalTrials.gov data sync job: see [`backend/README.md`](backend/README.md).
- Frontend setup and dashboard: see [`frontend/README.md`](frontend/README.md).

Typical local flow:

```bash
# Terminal 1 — API
cd backend && uv sync && uv run alembic upgrade head && uv run fastapi dev app/main.py

# Terminal 2 — UI (proxies /api → :8000)
cd frontend && npm install && npm run dev
```

### Production hosting (MVP)

| Layer | Host | Notes |
|---|---|---|
| Frontend | Vercel | `clinical-trial-navigator-one.vercel.app` |
| API | Fly.io | `https://clinical-trial-navigator-api.fly.dev` |
| Database | Neon | Pooled `DATABASE_URL` |

Deploy API from `backend/` (`fly deploy`). Set Fly secrets for `DATABASE_URL`,
`PROFILE_ENCRYPTION_KEY`, VAPID keys, and
`CORS_ORIGINS=https://clinical-trial-navigator-one.vercel.app`.

Deploy UI from `frontend/` (`vercel --prod`) with build-time
`VITE_API_BASE_URL=https://clinical-trial-navigator-api.fly.dev`.

## Development principles

- **Clean Code**: single responsibility, low coupling -- e.g. the matching
  logic sits behind a `MatchingStrategy` interface so rule-based scoring can
  later be swapped for an ML-based one.
- **TDD**: Red → Green → Refactor. External dependencies (DB, ClinicalTrials.gov
  API, email/Telegram) are mocked in tests.
- **Product Layer / ML Layer separation**: user-facing features and the
  internal data/ML engine are designed as distinct layers within a single
  project (not separate projects).
- **Locale**: user-facing output (UI copy, README files, API messages,
  notifications) is written in English for the US market.
