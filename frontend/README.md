# Clinical Trial Tracker — Frontend

React + TypeScript frontend for the Clinical Trial Tracker (US market). Built with [Vite](https://vite.dev/).

## Getting started

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Run tests (Vitest + React Testing Library)
npm run test:run

# Production build
npm run build
```

## Folder structure

```
src/
  components/   # UI components
  api/          # Backend API client (to be added)
  App.tsx       # Root app component
  main.tsx      # Entry point
```

## Development principles

- **User-facing copy**: All UI text must be in English (US audience).
- **TDD**: Write component tests before or alongside UI changes.

See `backend/README.md` for backend setup and project-wide docs under `docs/`.
