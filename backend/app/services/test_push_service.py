"""Send a one-off browser push for subscription / device testing."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import PushSubscriptionModel
from app.services.notifications import (
    NotificationMessage,
    NotificationService,
    PushRecipient,
)

logger = logging.getLogger(__name__)


def send_test_browser_push(
    db: Session,
    user_id: str,
    notification_service: NotificationService,
) -> int:
    """Send a test push to all stored subscriptions for the user. Returns attempts."""
    subscriptions = db.scalars(
        select(PushSubscriptionModel).where(PushSubscriptionModel.user_id == user_id)
    ).all()
    if not subscriptions:
        return 0

    message = NotificationMessage(
        user_id=user_id,
        title="Clinical trial alert test",
        body="Browser push is working. You will get alerts when a saved trial changes.",
        data={"type": "test"},
    )
    return asyncio.run(_send_all(subscriptions, message, notification_service))


async def _send_all(
    subscriptions: list[PushSubscriptionModel],
    message: NotificationMessage,
    notification_service: NotificationService,
) -> int:
    sent = 0
    last_error: Exception | None = None
    for sub in subscriptions:
        recipient = PushRecipient(
            endpoint=sub.endpoint,
            p256dh=sub.p256dh,
            auth=sub.auth,
        )
        try:
            await notification_service.send("browser", message, recipient=recipient)
            sent += 1
        except Exception as exc:
            last_error = exc
            logger.exception("Test push failed for endpoint %s", sub.endpoint[:48])
    if sent == 0 and last_error is not None:
        raise last_error
    return sent
