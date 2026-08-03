from fastapi import FastAPI

from app.api.trials import router as trials_router
from app.api.users import router as users_router

app = FastAPI(title="Clinical Trial Tracker API")

app.include_router(trials_router)
app.include_router(users_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
