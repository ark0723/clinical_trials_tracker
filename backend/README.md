# Clinical Trial Tracker — Backend

FastAPI backend for the Clinical Trial Tracker. Package management uses [uv](https://docs.astral.sh/uv/).

## Planning docs

Project goals, user requirements, and feature specs live in the repo docs (local only):

- `docs/01-project-goals.mdc`
- `docs/02-user-requirements.mdc`
- `docs/03-feature-spec.mdc`

## Getting started

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Copy environment defaults (matches docker-compose.yml)
cp .env.example .env

# Start local Postgres
docker compose -f ../docker-compose.yml up -d

# Apply database migrations
uv run alembic upgrade head

# Run the development server
uv run fastapi dev app/main.py

# Run tests (TDD) -- uses an in-memory SQLite DB, no infra required
uv run pytest

# Lint
uv run ruff check .
```

## Data ingestion (ClinicalTrials.gov sync)

`app/scripts/sync_trials.py` fetches trials from the ClinicalTrials.gov API v2,
detects changes against the stored snapshot, and records `TrialChangeEvent`s.
Trials are committed one at a time (not in a single batch transaction), so a
transient failure partway through (e.g. rate limiting) does not roll back
trials already synced in that run -- the next run simply resumes.

```bash
uv run python -m app.scripts.sync_trials
```

In production this runs daily via [.github/workflows/sync-trials.yml](../.github/workflows/sync-trials.yml)
(cron + manual `workflow_dispatch`), writing to the production database
described below. That workflow reads its connection string from a
`DATABASE_URL` repository secret (Settings → Secrets and variables → Actions).

## Production database (Neon)

Production uses [Neon](https://neon.tech) (serverless Postgres) rather than
the local Docker Postgres used for development.

- The connection string lives only in `backend/.env` (gitignored) locally,
  and in the `DATABASE_URL` GitHub Actions secret for CI/scheduled syncs --
  never commit it to `.env.example` or anywhere else tracked by git.
- To point local commands (migrations, sync script) at Neon instead of the
  Docker Postgres, temporarily set `DATABASE_URL` in `backend/.env` to the
  Neon connection string (`postgresql+psycopg://...neon.tech/...?sslmode=require`),
  then run `uv run alembic upgrade head` / `uv run python -m app.scripts.sync_trials`
  as usual.
- Neon's free tier scales to zero when idle, so the first request after
  inactivity may take a couple seconds longer (cold start) -- this is normal.

## Database migrations

```bash
# Apply all migrations
uv run alembic upgrade head

# Create a new migration after changing app/infrastructure/models.py
uv run alembic revision --autogenerate -m "describe the change"
```

## Folder structure

```
app/
  api/            # FastAPI routers (e.g. GET /api/trials)
  core/           # Settings and shared utilities
  domain/         # Pydantic domain models (ClinicalTrial, TrialChangeEvent, etc.)
  services/       # Business logic (trial sync, matching engine, etc.)
  infrastructure/ # DB models/session and external API clients (ClinicalTrials.gov)
  scripts/        # CLI entry points (e.g. sync_trials.py)
  dependencies.py # Shared FastAPI dependencies (get_db_session)
  main.py         # FastAPI app entry point
alembic/          # DB migrations
tests/            # pytest tests (write tests first)
```

## Development principles

- **TDD**: Write a failing test before implementation (Red → Green → Refactor).
- **Clean Code**: Keep layers loosely coupled; put core business logic (e.g. matching) behind interfaces so implementations can be swapped (rule-based → ML later).
