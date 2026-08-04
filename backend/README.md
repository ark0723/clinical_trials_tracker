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
Each sync also runs a **rule-based** eligibility extractor (no LLM / zero cost)
to persist `StructuredEligibility` and a plain-English summary when facts can
be extracted; otherwise the summary stays empty and the raw criteria remain
available. Trials are committed one at a time (not in a single batch
transaction), so a transient failure partway through (e.g. rate limiting)
does not roll back trials already synced in that run -- the next run simply
resumes.

```bash
uv run python -m app.scripts.sync_trials
```

In production this runs daily via [.github/workflows/sync-trials.yml](../.github/workflows/sync-trials.yml)
(cron + manual `workflow_dispatch`), writing to the production database
described below. That workflow reads its connection string from a
`DATABASE_URL` repository secret (Settings → Secrets and variables → Actions).

After a successful sync, the in-process lean-trial cache used by matching is
invalidated so recommendations pick up new/updated sites.

## User profiles

Encrypted patient profiles are available at:

- `POST /api/users/profile`
- `GET /api/users/profile/{user_id}`
- `PUT /api/users/profile/{user_id}`

Profile fields used for matching include age, stage, biomarkers, prior
treatments, **current treatment**, **ECOG**, **brain metastasis**, **US ZIP
(`postal_code`)**, and **`max_travel_distance_miles`** (US-facing miles; legacy
encrypted profiles that stored km are migrated on decrypt).

Set `PROFILE_ENCRYPTION_KEY` in `.env` (Fernet key; see `.env.example`). Without
it, profile endpoints return HTTP 503 so sensitive data is never stored in
plaintext by accident.

## Personalized matching (rule-based, no LLM)

`GET /api/matches/{user_id}?limit=10` scores active recruiting trials against
the user's encrypted profile using `StructuredEligibility` from sync (never
re-parses raw eligibility text). Results include `matched_criteria`,
`missing_criteria`, `unknown_criteria`, plain-English `rationale`,
`confidence`, and `nearest_site_miles` when a distance can be computed.

Key ranking / filter rules:

- **Compatibility score** uses a full-weight denominator so unknown or missing
  criteria reduce the score (no score inflation).
- **Hard excludes** (score 0, dropped from recommendations): high-confidence
  age/biomarker conflicts, and HER2-negative / TNBC-oriented trials for
  HER2-positive users (title + structured diagnosis).
- **Travel distance**: ZIP is geocoded (Nominatim, cached); haversine miles to
  each trial site with coordinates. Trials whose **nearest site exceeds**
  `max_travel_distance_miles` are **excluded** from recommendations. In-range
  trials prefer nearer sites; trials with **no listed sites** sort below
  trials with known distances.
- Recommendations sort by score, then nearer site, then travel evidence, then
  eligibility-data confidence.

### Match performance

Matching loads a **lean** trial projection (`trial_match_loader`) with an
in-process TTL cache, warmed on app startup. Prefer Neon's **pooled**
(`-pooler`) connection string for app traffic (see `.env.example`); keep a
direct URL for Alembic if needed. DB engine uses `pool_pre_ping` and
`pool_recycle` for serverless Postgres. An index on trial `overall_status`
supports candidate filtering.

See `docs/03-feature-spec.mdc` sections 3.4 (기능 3) and 3.10 (LLM policy).

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
- For interactive API traffic, prefer the Neon **pooler** hostname
  (`-pooler` in the host).
- Neon's free tier scales to zero when idle, so the first request after
  inactivity may take a couple seconds longer (cold start) -- this is normal.
  The match-trial cache warm on startup reduces first-match latency after the
  DB is reachable.

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
  api/            # FastAPI routers (trials, user profiles, matches)
  core/           # Settings and shared utilities
  domain/         # Pydantic models (ClinicalTrial, StructuredEligibility, UserProfile, MatchScore)
  services/       # Sync, eligibility extract, matching, geo, lean trial loader, profile cipher
  infrastructure/ # DB models/session and ClinicalTrials.gov client
  scripts/        # CLI entry points (e.g. sync_trials.py)
  dependencies.py # Shared FastAPI dependencies
  main.py         # FastAPI app entry point (warms match-trial cache)
alembic/          # DB migrations
tests/            # pytest tests (write tests first)
```

## Development principles

- **TDD**: Write a failing test before implementation (Red → Green → Refactor).
- **Clean Code**: Keep layers loosely coupled; put core business logic (e.g. matching) behind interfaces so implementations can be swapped (rule-based → ML later).
