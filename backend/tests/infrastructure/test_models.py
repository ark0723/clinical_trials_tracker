from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.models import ClinicalTrialModel, TrialLocationModel


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
