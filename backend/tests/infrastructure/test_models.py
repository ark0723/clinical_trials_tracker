from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.models import (
    ClinicalTrialModel,
    StructuredEligibilityModel,
    TrialLocationModel,
    UserProfileModel,
)


def test_clinical_trial_persists_with_locations(db_session: Session):
    trial = ClinicalTrialModel(
        nct_id="NCT00000001",
        title="A Study of Trastuzumab in HER2-positive Breast Cancer",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="Age >= 18. HER2-positive breast cancer.",
        enrollment_count=120,
        has_results=False,
        last_updated=datetime(2026, 1, 1, tzinfo=UTC),
        locations=[
            TrialLocationModel(
                facility="Seoul National University Hospital", city="Seoul", country="South Korea"
            )
        ],
    )

    db_session.add(trial)
    db_session.commit()

    persisted = db_session.get(ClinicalTrialModel, "NCT00000001")
    assert persisted is not None
    assert persisted.phase == TrialPhase.PHASE_2
    assert persisted.status == TrialStatus.RECRUITING
    assert len(persisted.locations) == 1
    assert persisted.locations[0].city == "Seoul"


def test_clinical_trial_persists_structured_eligibility(db_session: Session):
    trial = ClinicalTrialModel(
        nct_id="NCT00000002",
        title="Structured eligibility study",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="Age >= 18. HER2-positive breast cancer.",
        has_results=False,
        last_updated=datetime(2026, 1, 1, tzinfo=UTC),
        structured_eligibility=StructuredEligibilityModel(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            prior_treatments=["trastuzumab"],
            ecog=[0, 1],
            biomarkers=["HER2-positive"],
            brain_metastasis=False,
            extraction_confidence=1.0,
            extraction_method="rule",
        ),
    )

    db_session.add(trial)
    db_session.commit()

    persisted = db_session.get(ClinicalTrialModel, "NCT00000002")
    assert persisted is not None
    assert persisted.structured_eligibility is not None
    assert persisted.structured_eligibility.age_min == 18
    assert persisted.structured_eligibility.ecog == [0, 1]
    assert persisted.structured_eligibility.biomarkers == ["HER2-positive"]


def test_user_profile_stores_only_encrypted_health_payload(db_session: Session):
    profile = UserProfileModel(
        id="user-123",
        encrypted_health_data="opaque-encrypted-token",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    db_session.add(profile)
    db_session.commit()

    persisted = db_session.get(UserProfileModel, "user-123")
    assert persisted is not None
    assert persisted.encrypted_health_data == "opaque-encrypted-token"
