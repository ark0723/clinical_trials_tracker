# Clinical Trial Tracker — Frontend

React + TypeScript frontend for the Clinical Trial Tracker (US market). Built with [Vite](https://vite.dev/).

## Getting started

```bash
# Install dependencies
npm install

# Start backend (separate terminal, from backend/)
uv run fastapi dev app/main.py

# Development server (proxies /api to localhost:8000)
npm run dev

# Run tests (Vitest + React Testing Library)
npm run test:run

# Production build
npm run build
```

Set `VITE_API_BASE_URL` when the API is hosted on a different origin (optional for local dev; Vite proxy handles `/api`).

## Dashboard

The MVP dashboard includes:

- **Health profile form** — create or update an encrypted profile via
  `/api/users/profile` (age, stage, biomarkers, prior/current treatment,
  ECOG, brain metastasis, ZIP code, max travel distance in **miles**)
- **Recommended trials** — ranked matches from `/api/matches/{user_id}` with:
  - compatibility % and eligibility-data confidence
  - matched / not met / unable-to-verify criteria and plain-English rationale
  - trial sites (when listed on ClinicalTrials.gov) and approximate miles to
    the nearest site when computable
- Trials beyond the user's max travel distance are **not shown** (backend
  hard filter). Prefer a realistic US ZIP + mileage for useful local results.

## Folder structure

```
src/
  api/          # Backend API client and shared types
  components/   # Dashboard UI (ProfileForm, MatchCard, MatchResults, FieldHelp)
  test/         # Test utilities and fixtures
  utils/        # Formatting helpers
  App.tsx       # Root app component
  main.tsx      # Entry point
```

## Development principles

- **User-facing copy**: All UI text must be in English (US audience).
- **TDD**: Write component tests before or alongside UI changes.
- **TanStack Query**: Server state for profiles and match results.

See `backend/README.md` for backend setup and project-wide docs under `docs/`.
