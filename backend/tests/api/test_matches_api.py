from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.models import ClinicalTrialModel, StructuredEligibilityModel
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


def seed_recruiting_trial(db_session: Session, nct_id: str = "NCT01234567") -> None:
    trial = ClinicalTrialModel(
        nct_id=nct_id,
        title="HER2+ recruiting study",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="Age >= 18 and <= 75. HER2-positive breast cancer.",
        enrollment_count=120,
        has_results=False,
        last_updated=datetime(2026, 1, 15, tzinfo=UTC),
    )
    structured = StructuredEligibilityModel(
        nct_id=nct_id,
        age_min=18,
        age_max=75,
        diagnosis="HER2-positive breast cancer",
        prior_treatments=[],
        ecog=[],
        biomarkers=["HER2-positive"],
        brain_metastasis=None,
        extraction_confidence=0.67,
        extraction_method="rule",
    )
    db_session.add(trial)
    db_session.add(structured)
    db_session.commit()


def test_get_matches_returns_ranked_results_for_existing_profile(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    seed_recruiting_trial(db_session)
    created = client.post(
        "/api/users/profile",
        json={
            "age": 45,
            "stage": "III",
            "biomarkers": ["HER2-positive"],
            "current_treatment": "trastuzumab",
            "max_travel_distance_km": 100,
            "notification_channels": ["email"],
        },
    ).json()

    response = client.get(f"/api/matches/{created['id']}")

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["trial"]["nct_id"] == "NCT01234567"
    assert matches[0]["total"] > 0.8
    assert matches[0]["rationale"]


def test_get_matches_returns_404_for_unknown_user(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.get("/api/matches/missing-user")

    assert response.status_code == 404
    assert response.json() == {"detail": "User profile not found"}
