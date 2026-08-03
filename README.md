# Clinical Trial Tracker

A personalized clinical trial matching and change-notification service for
HER2-positive breast cancer patients and caregivers (US market).

Beyond the patient-facing product, the project is architected as a two-layer
system: a **Product Layer** (trial search, patient matching, notifications,
timeline) sitting on top of an internal **ML/Data Layer** (clinical data
ingestion, LLM-assisted eligibility structuring, benchmark datasets, and
leakage-resistant evaluation). See `docs/03-feature-spec.mdc` for the full
architecture (planning docs are local-only, see below).

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
- Frontend setup: see [`frontend/README.md`](frontend/README.md).

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
