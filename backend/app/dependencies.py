from fastapi import HTTPException

from app.core.config import settings
from app.infrastructure.db import get_db_session
from app.services.profile_cipher import ProfileCipher


def get_profile_cipher() -> ProfileCipher:
    if settings.profile_encryption_key is None:
        raise HTTPException(
            status_code=503,
            detail="User profiles are unavailable because encryption is not configured",
        )
    return ProfileCipher(settings.profile_encryption_key)


__all__ = ["get_db_session", "get_profile_cipher"]
