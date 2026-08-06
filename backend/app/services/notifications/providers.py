"""Browser / Web Push provider (VAPID). Email & Telegram stay stubs for later."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from app.services.notifications.base import NotificationMessage, NotificationProvider


@dataclass(frozen=True)
class PushRecipient:
    endpoint: str
    p256dh: str
    auth: str


class BrowserPushProvider(NotificationProvider):
    """Sends Web Push notifications via pywebpush."""

    def __init__(
        self,
        *,
        vapid_private_key: str,
        vapid_claims_email: str,
        webpush_fn: Any | None = None,
    ):
        self._vapid_private_key = vapid_private_key
        self._vapid_claims = {"sub": vapid_claims_email}
        self._webpush = webpush_fn

    @property
    def channel(self) -> str:
        return "browser"

    async def send(self, message: NotificationMessage, *, recipient: Any) -> None:
        if not isinstance(recipient, PushRecipient):
            raise TypeError("BrowserPushProvider expects PushRecipient")

        payload = json.dumps(
            {
                "title": message.title,
                "body": message.body,
                "data": message.data,
            }
        )
        subscription_info = {
            "endpoint": recipient.endpoint,
            "keys": {"p256dh": recipient.p256dh, "auth": recipient.auth},
        }

        def _send() -> None:
            webpush = self._webpush
            if webpush is None:
                from pywebpush import webpush as default_webpush

                webpush = default_webpush
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self._vapid_private_key,
                vapid_claims=self._vapid_claims,
            )

        await asyncio.to_thread(_send)


class EmailProvider(NotificationProvider):
    """Reserved for later (Resend / SMTP)."""

    @property
    def channel(self) -> str:
        return "email"

    async def send(self, message: NotificationMessage, *, recipient: Any) -> None:
        raise NotImplementedError("Email notifications are not enabled yet")


class TelegramProvider(NotificationProvider):
    """Reserved for later (Telegram Bot API)."""

    @property
    def channel(self) -> str:
        return "telegram"

    async def send(self, message: NotificationMessage, *, recipient: Any) -> None:
        raise NotImplementedError("Telegram notifications are not enabled yet")
