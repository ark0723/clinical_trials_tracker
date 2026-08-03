"""Encrypted user-profile persistence operations."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.user_profile import UserProfile, UserProfileCreate
from app.infrastructure.models import UserProfileModel
from app.services.profile_cipher import ProfileCipher


def create_user_profile(
    db: Session,
    cipher: ProfileCipher,
    profile: UserProfileCreate,
) -> UserProfile:
    now = datetime.now(UTC)
    model = UserProfileModel(
        id=str(uuid4()),
        encrypted_health_data=cipher.encrypt(profile),
        created_at=now,
        updated_at=now,
    )
    db.add(model)
    db.commit()
    return _to_domain(model, cipher)


def get_user_profile(
    db: Session,
    cipher: ProfileCipher,
    user_id: str,
) -> UserProfile | None:
    model = db.get(UserProfileModel, user_id)
    if model is None:
        return None
    return _to_domain(model, cipher)


def update_user_profile(
    db: Session,
    cipher: ProfileCipher,
    user_id: str,
    profile: UserProfileCreate,
) -> UserProfile | None:
    model = db.get(UserProfileModel, user_id)
    if model is None:
        return None

    model.encrypted_health_data = cipher.encrypt(profile)
    model.updated_at = datetime.now(UTC)
    db.commit()
    return _to_domain(model, cipher)


def _to_domain(model: UserProfileModel, cipher: ProfileCipher) -> UserProfile:
    decrypted = cipher.decrypt(model.encrypted_health_data)
    return UserProfile(id=model.id, **decrypted.model_dump())
