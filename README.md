# Clinical Trial Tracker

A personalized clinical trial matching and change-notification service for
HER2-positive breast cancer patients and caregivers (US market).

Beyond the patient-facing product, the project is architected as a two-layer
system: a **Product Layer** (trial search, patient matching, notifications,
timeline) sitting on top of an internal **ML/Data Layer** (clinical data
ingestion, LLM-assisted eligibility structuring, benchmark datasets, and
leakage-resistant evaluation). See `docs/03-feature-spec.mdc` for the full
architecture (planning docs are local-only, see below).

## Current status (Week 4 MVP)

- **Backend**: ClinicalTrials.gov sync, encrypted profiles, rule-based
  matching with travel-distance hard filters (ZIP → site miles), lean
  cached trial loading for fast recommendations.
- **Frontend**: Dashboard with health profile form and ranked recommended
  trials (compatibility, criteria breakdown, sites, nearest-site miles).

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
