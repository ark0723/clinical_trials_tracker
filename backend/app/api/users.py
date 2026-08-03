from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.user_profile import UserProfile, UserProfileCreate
from app.services.profile_cipher import ProfileCipher
from app.services.user_profile_service import (
    create_user_profile,
    get_user_profile,
    update_user_profile,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/profile", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile: UserProfileCreate,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> UserProfile:
    return create_user_profile(db, cipher, profile)


@router.get("/profile/{user_id}", response_model=UserProfile)
def get_profile(
    user_id: str,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> UserProfile:
    profile = get_user_profile(db, cipher, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.put("/profile/{user_id}", response_model=UserProfile)
def update_profile(
    user_id: str,
    profile: UserProfileCreate,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> UserProfile:
    updated = update_user_profile(db, cipher, user_id, profile)
    if updated is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return updated
