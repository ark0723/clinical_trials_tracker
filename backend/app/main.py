from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.matches import router as matches_router
from app.api.notifications import router as notifications_router
from app.api.trials import router as trials_router
from app.api.users import router as users_router
from app.core.config import settings
from app.infrastructure.db import SessionLocal
from app.services.trial_match_loader import get_cached_match_trials


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Warm the lean trial cache so the first dashboard match request is fast.
    session = SessionLocal()
    try:
        get_cached_match_trials(session)
    except Exception:
        # Startup must not fail if Neon is briefly unreachable; first request will retry.
        pass
    finally:
        session.close()
    yield


app = FastAPI(title="Clinical Trial Tracker API", lifespan=lifespan)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(trials_router)
app.include_router(users_router)
app.include_router(matches_router)
app.include_router(notifications_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
