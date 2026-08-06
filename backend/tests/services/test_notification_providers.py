import asyncio

from app.services.notifications import (
    BrowserPushProvider,
    EmailProvider,
    NotificationMessage,
    NotificationService,
    PushRecipient,
    TelegramProvider,
)


class RecordingBrowserProvider(BrowserPushProvider):
    def __init__(self):
        super().__init__(
            vapid_private_key="test-key",
            vapid_claims_email="mailto:test@example.com",
        )
        self.sent: list[tuple[NotificationMessage, PushRecipient]] = []

    async def send(self, message: NotificationMessage, *, recipient):
        assert isinstance(recipient, PushRecipient)
        self.sent.append((message, recipient))


def test_notification_service_routes_to_browser_provider():
    browser = RecordingBrowserProvider()
    service = NotificationService([browser, EmailProvider(), TelegramProvider()])
    message = NotificationMessage(
        user_id="u1",
        title="Trial update",
        body="NCT01234567 is now Recruiting",
        data={"nct_id": "NCT01234567"},
    )
    recipient = PushRecipient(endpoint="https://push.example/1", p256dh="p", auth="a")

    asyncio.run(service.send("browser", message, recipient=recipient))

    assert len(browser.sent) == 1
    assert browser.sent[0][0].title == "Trial update"


def test_email_and_telegram_providers_are_stubs():
    email = EmailProvider()
    telegram = TelegramProvider()
    message = NotificationMessage(user_id="u1", title="t", body="b")

    try:
        asyncio.run(email.send(message, recipient="user@example.com"))
        raised = False
    except NotImplementedError:
        raised = True
    assert raised

    try:
        asyncio.run(telegram.send(message, recipient="123"))
        raised = False
    except NotImplementedError:
        raised = True
    assert raised
