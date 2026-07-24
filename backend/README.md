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

# Run the development server
uv run fastapi dev app/main.py

# Run tests (TDD)
uv run pytest

# Lint
uv run ruff check .
```

## Folder structure

```
app/
  api/            # FastAPI routers
  core/           # Settings and shared utilities
  domain/         # Pydantic domain models (UserProfile, ClinicalTrial, etc.)
  services/       # Business logic (matching engine, etc.)
  infrastructure/ # DB and external API clients (ClinicalTrials.gov, etc.)
  main.py         # FastAPI app entry point
tests/            # pytest tests (write tests first)
```

## Development principles

- **TDD**: Write a failing test before implementation (Red → Green → Refactor).
- **Clean Code**: Keep layers loosely coupled; put core business logic (e.g. matching) behind interfaces so implementations can be swapped (rule-based → ML later).
