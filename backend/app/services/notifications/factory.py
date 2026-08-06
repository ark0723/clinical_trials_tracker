"""Factory for NotificationService with configured providers."""

from __future__ import annotations

from app.core.config import settings
from app.services.notifications import (
    BrowserPushProvider,
    EmailProvider,
    NotificationService,
    TelegramProvider,
)


def build_notification_service() -> NotificationService:
    providers: list = [EmailProvider(), TelegramProvider()]
    if settings.vapid_private_key:
        providers.insert(
            0,
            BrowserPushProvider(
                vapid_private_key=settings.vapid_private_key,
                vapid_claims_email=settings.vapid_subject,
            ),
        )
    return NotificationService(providers)
