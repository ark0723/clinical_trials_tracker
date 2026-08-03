import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.infrastructure.models import UserProfileModel
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


def profile_payload(**overrides) -> dict:
    payload = {
        "age": 45,
        "stage": "III",
        "biomarkers": ["HER2-positive"],
        "current_treatment": "trastuzumab deruxtecan",
        "max_travel_distance_km": 100,
        "notification_channels": ["email"],
    }
    payload.update(overrides)
    return payload


def test_create_profile_returns_id_and_stores_encrypted_payload(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.post("/api/users/profile", json=profile_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["age"] == 45
    assert body["stage"] == "III"

    stored = db_session.get(UserProfileModel, body["id"])
    assert stored is not None
    assert "HER2-positive" not in stored.encrypted_health_data
    assert "trastuzumab" not in stored.encrypted_health_data


def test_get_profile_returns_decrypted_health_data(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    created = client.post("/api/users/profile", json=profile_payload()).json()

    response = client.get(f"/api/users/profile/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_update_profile_replaces_encrypted_payload(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    created = client.post("/api/users/profile", json=profile_payload()).json()
    stored = db_session.get(UserProfileModel, created["id"])
    original_ciphertext = stored.encrypted_health_data

    response = client.put(
        f"/api/users/profile/{created['id']}",
        json=profile_payload(age=46, max_travel_distance_km=250),
    )

    assert response.status_code == 200
    assert response.json()["age"] == 46
    assert response.json()["max_travel_distance_km"] == 250
    db_session.refresh(stored)
    assert stored.encrypted_health_data != original_ciphertext


def test_get_profile_returns_404_for_unknown_user(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.get("/api/users/profile/missing-user")

    assert response.status_code == 404
    assert response.json() == {"detail": "User profile not found"}


def test_update_profile_returns_404_for_unknown_user(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.put("/api/users/profile/missing-user", json=profile_payload())

    assert response.status_code == 404
    assert response.json() == {"detail": "User profile not found"}


def test_create_profile_rejects_missing_biomarkers(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.post("/api/users/profile", json=profile_payload(biomarkers=[]))

    assert response.status_code == 422
