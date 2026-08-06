from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.models import ClinicalTrialModel, StructuredEligibilityModel, TrialLocationModel
from app.main import app
from app.services.profile_cipher import ProfileCipher
from app.services.trial_match_loader import clear_candidate_cache


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    clear_candidate_cache()
    yield
    app.dependency_overrides.clear()
    clear_candidate_cache()


@pytest.fixture()
def profile_cipher() -> ProfileCipher:
    return ProfileCipher(ProfileCipher.generate_key())


def make_client(db_session: Session, profile_cipher: ProfileCipher) -> TestClient:
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_profile_cipher] = lambda: profile_cipher
    return TestClient(app)


def seed_trial(
    db_session: Session,
    *,
    nct_id: str,
    status: TrialStatus,
    title: str | None = None,
) -> None:
    trial = ClinicalTrialModel(
        nct_id=nct_id,
        title=title or f"{status.value} study",
        phase=TrialPhase.PHASE_2,
        status=status,
        eligibility_criteria_raw="Age >= 18 and <= 75. HER2-positive breast cancer.",
        enrollment_count=120,
        has_results=False,
        last_updated=datetime(2026, 1, 15, tzinfo=UTC),
        locations=[
            TrialLocationModel(
                facility="Dana-Farber",
                city="Boston",
                country="United States",
            )
        ],
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


def _create_profile(client: TestClient) -> str:
    return client.post(
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
            "notification_channels": ["email"],
        },
    ).json()["id"]


def test_get_matches_returns_ranked_results_for_existing_profile(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    seed_trial(
        db_session,
        nct_id="NCT01234567",
        status=TrialStatus.RECRUITING,
        title="HER2+ recruiting study",
    )
    user_id = _create_profile(client)

    response = client.get(f"/api/matches/{user_id}")

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["trial"]["nct_id"] == "NCT01234567"
    assert matches[0]["trial"]["title"] == "HER2+ recruiting study"
    assert matches[0]["total"] > 0.8
    assert matches[0]["rationale"]


def test_get_matches_returns_404_for_unknown_user(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)

    response = client.get("/api/matches/does-not-exist")

    assert response.status_code == 404


def test_default_matches_exclude_enrolling_by_invitation(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    seed_trial(
        db_session,
        nct_id="NCT-INVITE",
        status=TrialStatus.ENROLLING_BY_INVITATION,
    )
    seed_trial(db_session, nct_id="NCT-RECRUIT", status=TrialStatus.RECRUITING)
    user_id = _create_profile(client)

    response = client.get(f"/api/matches/{user_id}")

    assert response.status_code == 200
    nct_ids = [m["trial"]["nct_id"] for m in response.json()["matches"]]
    assert "NCT-RECRUIT" in nct_ids
    assert "NCT-INVITE" not in nct_ids


def test_matches_can_include_completed_via_status_filter(
    db_session: Session,
    profile_cipher: ProfileCipher,
):
    client = make_client(db_session, profile_cipher)
    seed_trial(db_session, nct_id="NCT-DONE", status=TrialStatus.COMPLETED)
    user_id = _create_profile(client)

    default_response = client.get(f"/api/matches/{user_id}")
    assert default_response.json()["matches"] == []

    response = client.get(
        f"/api/matches/{user_id}",
        params=[("statuses", "COMPLETED")],
    )

    assert response.status_code == 200
    nct_ids = [m["trial"]["nct_id"] for m in response.json()["matches"]]
    assert nct_ids == ["NCT-DONE"]
