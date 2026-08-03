from fastapi import FastAPI

from app.api.trials import router as trials_router

app = FastAPI(title="Clinical Trial Tracker API")

app.include_router(trials_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
