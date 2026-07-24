from fastapi import FastAPI

app = FastAPI(title="Clinical Trial Tracker API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
