"""Notification channel abstraction (Browser first; Email/Telegram later)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NotificationMessage:
    user_id: str
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)


class NotificationProvider(ABC):
    """Pluggable delivery backend for one channel."""

    @property
    @abstractmethod
    def channel(self) -> str:
        """Channel id matching NotificationChannel values (e.g. browser)."""

    @abstractmethod
    async def send(self, message: NotificationMessage, *, recipient: Any) -> None:
        """Deliver one message to a channel-specific recipient payload."""


class NotificationService:
    """Routes messages to registered providers by channel name."""

    def __init__(self, providers: list[NotificationProvider] | None = None):
        self._providers: dict[str, NotificationProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: NotificationProvider) -> None:
        self._providers[provider.channel] = provider

    def get_provider(self, channel: str) -> NotificationProvider | None:
        return self._providers.get(channel)

    async def send(
        self,
        channel: str,
        message: NotificationMessage,
        *,
        recipient: Any,
    ) -> None:
        provider = self._providers.get(channel)
        if provider is None:
            raise ValueError(f"No notification provider registered for channel={channel!r}")
        await provider.send(message, recipient=recipient)
