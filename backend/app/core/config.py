from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/clinical_tracker"

    ctgov_base_url: str = "https://clinicaltrials.gov/api/v2"
    ctgov_condition_query: str = "HER2-positive breast cancer"
    ctgov_page_size: int = 100

    profile_encryption_key: str | None = None

    # Web Push (VAPID). Generate with py_vapid / openssl; see backend README.
    vapid_private_key: str | None = None
    vapid_public_key: str | None = None
    vapid_subject: str = "mailto:alerts@clinicaltrialnavigator.local"

    # Comma-separated browser origins allowed to call the API (Vercel, ngrok, local).
    # Empty = no CORS middleware (local Vite proxy does not need it).
    cors_origins: str = ""


settings = Settings()
