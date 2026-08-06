from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.domain.user_profile import (
    BrainMetastasisStatus,
    CancerStage,
    CurrentTreatment,
    NotificationChannel,
    UserProfileCreate,
)
from app.infrastructure.models import ClinicalTrialModel
from app.main import app
from app.services.profile_cipher import ProfileCipher
from app.services.user_profile_service import create_user_profile


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def make_client(db_session: Session, cipher: ProfileCipher) -> TestClient:
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_profile_cipher] = lambda: cipher
    return TestClient(app)


def seed_user_and_trial(db_session: Session, cipher: ProfileCipher) -> str:
    profile = create_user_profile(
        db_session,
        cipher,
        UserProfileCreate(
            age=45,
            stage=CancerStage.STAGE_II,
            biomarkers=["HER2-positive"],
            current_treatment=CurrentTreatment.UNKNOWN,
            brain_metastasis=BrainMetastasisStatus.UNKNOWN,
            max_travel_distance_miles=100,
            notification_channels=[NotificationChannel.EMAIL],
        ),
    )
    db_session.add(
        ClinicalTrialModel(
            nct_id="NCT01234567",
            title="A HER2+ Study",
            phase=TrialPhase.PHASE_2,
            status=TrialStatus.RECRUITING,
            eligibility_criteria_raw="Age >= 18.",
            enrollment_count=120,
            has_results=False,
            last_updated=datetime(2026, 1, 15, tzinfo=UTC),
        )
    )
    db_session.commit()
    return profile.id


@pytest.fixture()
def profile_cipher() -> ProfileCipher:
    return ProfileCipher(ProfileCipher.generate_key())


def test_save_trial_for_user(db_session: Session, profile_cipher: ProfileCipher):
    user_id = seed_user_and_trial(db_session, profile_cipher)
    client = make_client(db_session, profile_cipher)

    response = client.post(
        f"/api/users/{user_id}/saved-trials",
        json={"nct_id": "NCT01234567"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nct_id"] == "NCT01234567"
    assert body["status_at_save"] == "RECRUITING"


def test_list_saved_trials(db_session: Session, profile_cipher: ProfileCipher):
    user_id = seed_user_and_trial(db_session, profile_cipher)
    client = make_client(db_session, profile_cipher)
    client.post(f"/api/users/{user_id}/saved-trials", json={"nct_id": "NCT01234567"})

    response = client.get(f"/api/users/{user_id}/saved-trials")

    assert response.status_code == 200
    assert len(response.json()["saved_trials"]) == 1


def test_unsave_trial(db_session: Session, profile_cipher: ProfileCipher):
    user_id = seed_user_and_trial(db_session, profile_cipher)
    client = make_client(db_session, profile_cipher)
    client.post(f"/api/users/{user_id}/saved-trials", json={"nct_id": "NCT01234567"})

    response = client.delete(f"/api/users/{user_id}/saved-trials/NCT01234567")

    assert response.status_code == 204
    listed = client.get(f"/api/users/{user_id}/saved-trials")
    assert listed.json()["saved_trials"] == []
