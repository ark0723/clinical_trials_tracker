from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.saved_trial import SavedTrial, SavedTrialCreate
from app.domain.user_profile import UserProfile, UserProfileCreate
from app.services.profile_cipher import ProfileCipher
from app.services.saved_trial_service import (
    SavedTrialError,
    list_saved_trials,
    save_trial,
    unsave_trial,
)
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


@router.post(
    "/{user_id}/saved-trials",
    response_model=SavedTrial,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_trial(
    user_id: str,
    payload: SavedTrialCreate,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> SavedTrial:
    if get_user_profile(db, cipher, user_id) is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    try:
        return save_trial(db, user_id, payload)
    except SavedTrialError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/{user_id}/saved-trials")
def get_saved_trials(
    user_id: str,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> dict[str, list[SavedTrial]]:
    if get_user_profile(db, cipher, user_id) is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return {"saved_trials": list_saved_trials(db, user_id)}


@router.delete("/{user_id}/saved-trials/{nct_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_trial(
    user_id: str,
    nct_id: str,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> Response:
    if get_user_profile(db, cipher, user_id) is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not unsave_trial(db, user_id, nct_id):
        raise HTTPException(status_code=404, detail="Saved trial not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
