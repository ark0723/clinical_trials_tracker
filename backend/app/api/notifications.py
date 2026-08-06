from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db_session, get_profile_cipher
from app.services.profile_cipher import ProfileCipher
from app.services.push_subscription_service import (
    PushSubscriptionCreate,
    PushSubscriptionOut,
    delete_push_subscription,
    upsert_push_subscription,
)
from app.services.user_profile_service import get_user_profile

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/vapid-public-key")
def get_vapid_public_key() -> dict[str, str]:
    if not settings.vapid_public_key:
        raise HTTPException(
            status_code=503,
            detail="Browser push is not configured (missing VAPID_PUBLIC_KEY)",
        )
    return {"public_key": settings.vapid_public_key}


@router.post(
    "/users/{user_id}/subscriptions",
    response_model=PushSubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_push_subscription(
    user_id: str,
    payload: PushSubscriptionCreate,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> PushSubscriptionOut:
    if get_user_profile(db, cipher, user_id) is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return upsert_push_subscription(db, user_id, payload)


@router.delete("/users/{user_id}/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def remove_push_subscription(
    user_id: str,
    endpoint: str,
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> Response:
    if get_user_profile(db, cipher, user_id) is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not delete_push_subscription(db, user_id, endpoint):
        raise HTTPException(status_code=404, detail="Push subscription not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
