from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.infrastructure.models import PushSubscriptionModel
from app.main import app
from app.services.profile_cipher import ProfileCipher


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def profile_cipher() -> ProfileCipher:
    return ProfileCipher(ProfileCipher.generate_key())


def make_client(db_session: Session, profile_cipher: ProfileCipher) -> TestClient:
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_profile_cipher] = lambda: profile_cipher
    return TestClient(app)


def _create_profile(client: TestClient) -> str:
    response = client.post(
        "/api/users/profile",
        json={
            "age": 45,
            "stage": "III",
            "biomarkers": ["HER2-positive"],
            "current_treatment": "trastuzumab",
            "postal_code": "10001",
            "ecog": 0,
            "brain_metastasis": "unknown",
            "max_travel_distance_miles": 100,
            "notification_channels": ["browser"],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_send_test_push_requires_subscription(
    db_session: Session,
    profile_cipher: ProfileCipher,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.api.notifications.settings.vapid_private_key",
        "test-private-key",
    )
    client = make_client(db_session, profile_cipher)
    user_id = _create_profile(client)

    response = client.post(f"/api/notifications/users/{user_id}/test")

    assert response.status_code == 404
    assert "subscription" in response.json()["detail"].lower()


def test_send_test_push_sends_when_subscribed(
    db_session: Session,
    profile_cipher: ProfileCipher,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.api.notifications.settings.vapid_private_key",
        "test-private-key",
    )
    sent_payloads: list = []

    class FakeService:
        async def send(self, channel, message, *, recipient):
            sent_payloads.append((channel, message, recipient))

    monkeypatch.setattr(
        "app.api.notifications.build_notification_service",
        lambda: FakeService(),
    )

    client = make_client(db_session, profile_cipher)
    user_id = _create_profile(client)
    db_session.add(
        PushSubscriptionModel(
            user_id=user_id,
            endpoint="https://push.example/endpoint",
            p256dh="p256dh-key",
            auth="auth-key",
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    response = client.post(f"/api/notifications/users/{user_id}/test")

    assert response.status_code == 200
    assert response.json()["sent"] == 1
    assert sent_payloads[0][0] == "browser"
    assert "test" in sent_payloads[0][1].title.lower()
