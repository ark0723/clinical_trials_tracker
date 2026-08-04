"""Encrypted user-profile persistence with a short in-process TTL cache.

Match requests hit get_user_profile on every call; caching the decrypted
profile removes a Neon round-trip on warm dashboard refreshes.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.user_profile import UserProfile, UserProfileCreate
from app.infrastructure.models import UserProfileModel
from app.services.profile_cipher import ProfileCipher

_DEFAULT_TTL_SECONDS = 60.0


@dataclass
class _ProfileCacheEntry:
    profile: UserProfile
    loaded_at: float


_cache_lock = threading.Lock()
_profile_cache: dict[str, _ProfileCacheEntry] = {}
_cache_ttl_seconds = _DEFAULT_TTL_SECONDS


def configure_profile_cache(*, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
    global _cache_ttl_seconds
    _cache_ttl_seconds = ttl_seconds


def clear_profile_cache() -> None:
    with _cache_lock:
        _profile_cache.clear()


def _cache_get(user_id: str) -> UserProfile | None:
    now = time.monotonic()
    with _cache_lock:
        entry = _profile_cache.get(user_id)
        if entry is None:
            return None
        if (now - entry.loaded_at) >= _cache_ttl_seconds:
            del _profile_cache[user_id]
            return None
        return entry.profile


def _cache_put(profile: UserProfile) -> None:
    with _cache_lock:
        _profile_cache[profile.id] = _ProfileCacheEntry(
            profile=profile,
            loaded_at=time.monotonic(),
        )


def _cache_invalidate(user_id: str) -> None:
    with _cache_lock:
        _profile_cache.pop(user_id, None)


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
    domain = _to_domain(model, cipher)
    _cache_put(domain)
    return domain


def get_user_profile(
    db: Session,
    cipher: ProfileCipher,
    user_id: str,
) -> UserProfile | None:
    cached = _cache_get(user_id)
    if cached is not None:
        return cached

    model = db.get(UserProfileModel, user_id)
    if model is None:
        return None
    domain = _to_domain(model, cipher)
    _cache_put(domain)
    return domain


def update_user_profile(
    db: Session,
    cipher: ProfileCipher,
    user_id: str,
    profile: UserProfileCreate,
) -> UserProfile | None:
    model = db.get(UserProfileModel, user_id)
    if model is None:
        _cache_invalidate(user_id)
        return None

    model.encrypted_health_data = cipher.encrypt(profile)
    model.updated_at = datetime.now(UTC)
    db.commit()
    domain = _to_domain(model, cipher)
    _cache_put(domain)
    return domain


def _to_domain(model: UserProfileModel, cipher: ProfileCipher) -> UserProfile:
    decrypted = cipher.decrypt(model.encrypted_health_data)
    return UserProfile(id=model.id, **decrypted.model_dump())
