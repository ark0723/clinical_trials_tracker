"""Persist Web Push subscriptions for BrowserPushProvider."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import PushSubscriptionModel


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(min_length=8)
    p256dh: str = Field(min_length=8)
    auth: str = Field(min_length=4)


class PushSubscriptionOut(BaseModel):
    endpoint: str
    created_at: datetime


def upsert_push_subscription(
    db: Session, user_id: str, payload: PushSubscriptionCreate
) -> PushSubscriptionOut:
    existing = db.scalar(
        select(PushSubscriptionModel).where(
            PushSubscriptionModel.endpoint == payload.endpoint
        )
    )
    now = datetime.now(UTC)
    if existing is not None:
        existing.user_id = user_id
        existing.p256dh = payload.p256dh
        existing.auth = payload.auth
        db.commit()
        db.refresh(existing)
        return PushSubscriptionOut(endpoint=existing.endpoint, created_at=existing.created_at)

    model = PushSubscriptionModel(
        user_id=user_id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
        created_at=now,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return PushSubscriptionOut(endpoint=model.endpoint, created_at=model.created_at)


def delete_push_subscription(db: Session, user_id: str, endpoint: str) -> bool:
    model = db.scalar(
        select(PushSubscriptionModel).where(
            PushSubscriptionModel.user_id == user_id,
            PushSubscriptionModel.endpoint == endpoint,
        )
    )
    if model is None:
        return False
    db.delete(model)
    db.commit()
    return True
