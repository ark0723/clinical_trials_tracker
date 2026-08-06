"""Notify users when saved trials change (change detection → NotificationService)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.clinical_trial import TrialChangeEvent
from app.domain.user_profile import NotificationChannel
from app.infrastructure.models import PushSubscriptionModel, SavedTrialModel
from app.services.notifications import (
    NotificationMessage,
    NotificationService,
    PushRecipient,
)
from app.services.profile_cipher import ProfileCipher
from app.services.user_profile_service import get_user_profile

logger = logging.getLogger(__name__)


def notify_saved_trial_changes(
    db: Session,
    cipher: ProfileCipher,
    events: list[TrialChangeEvent],
    notification_service: NotificationService,
) -> int:
    """Send browser push for saved-trial change events. Returns send attempts."""
    if not events:
        return 0
    return asyncio.run(
        _notify_async(db, cipher, events, notification_service)
    )


async def _notify_async(
    db: Session,
    cipher: ProfileCipher,
    events: list[TrialChangeEvent],
    notification_service: NotificationService,
) -> int:
    sent = 0
    for event in events:
        user_ids = db.scalars(
            select(SavedTrialModel.user_id).where(SavedTrialModel.nct_id == event.nct_id)
        ).all()
        for user_id in user_ids:
            profile = get_user_profile(db, cipher, user_id)
            if profile is None:
                continue
            if NotificationChannel.BROWSER not in profile.notification_channels:
                continue

            message = NotificationMessage(
                user_id=user_id,
                title="Clinical trial update",
                body=_format_body(event),
                data={
                    "nct_id": event.nct_id,
                    "event_type": event.event_type,
                },
            )
            subscriptions = db.scalars(
                select(PushSubscriptionModel).where(
                    PushSubscriptionModel.user_id == user_id
                )
            ).all()
            for sub in subscriptions:
                recipient = PushRecipient(
                    endpoint=sub.endpoint,
                    p256dh=sub.p256dh,
                    auth=sub.auth,
                )
                try:
                    await notification_service.send(
                        "browser", message, recipient=recipient
                    )
                    sent += 1
                except Exception:
                    logger.exception(
                        "Failed browser push for user=%s endpoint=%s",
                        user_id,
                        sub.endpoint[:48],
                    )
    return sent


def _format_body(event: TrialChangeEvent) -> str:
    if event.event_type == "status_changed":
        return (
            f"{event.nct_id} status changed"
            + (f" to {event.new_value}" if event.new_value else "")
        )
    if event.event_type == "enrollment_changed":
        return f"{event.nct_id} enrollment updated to {event.new_value}"
    return f"{event.nct_id} updated ({event.event_type})"
