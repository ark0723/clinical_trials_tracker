from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.matches import router as matches_router
from app.api.trials import router as trials_router
from app.api.users import router as users_router
from app.infrastructure.db import SessionLocal
from app.services.trial_match_loader import get_cached_active_match_trials


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Warm the lean trial cache so the first dashboard match request is fast.
    session = SessionLocal()
    try:
        get_cached_active_match_trials(session)
    except Exception:
        # Startup must not fail if Neon is briefly unreachable; first request will retry.
        pass
    finally:
        session.close()
    yield


app = FastAPI(title="Clinical Trial Tracker API", lifespan=lifespan)

app.include_router(trials_router)
app.include_router(users_router)
app.include_router(matches_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
