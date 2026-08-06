from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.models import ClinicalTrialModel, TrialLocationModel
from app.main import app


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def seed_trial(db_session: Session, **overrides) -> ClinicalTrialModel:
    defaults = dict(
        nct_id="NCT01234567",
        title="A HER2+ Study",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="Age >= 18.",
        enrollment_count=120,
        has_results=False,
        last_updated=datetime(2026, 1, 15, tzinfo=UTC),
        locations=[TrialLocationModel(facility="SNUH", city="Seoul", country="South Korea")],
    )
    defaults.update(overrides)
    trial = ClinicalTrialModel(**defaults)
    db_session.add(trial)
    db_session.commit()
    return trial


def make_client(db_session: Session) -> TestClient:
    app.dependency_overrides[get_db_session] = lambda: db_session
    return TestClient(app)


def test_get_trials_returns_seeded_trials(db_session: Session):
    seed_trial(db_session)
    client = make_client(db_session)

    response = client.get("/api/trials")

    assert response.status_code == 200
    trials = response.json()["trials"]
    assert len(trials) == 1
    assert trials[0]["nct_id"] == "NCT01234567"
    assert trials[0]["locations"][0]["city"] == "Seoul"


def test_get_trials_filters_by_status(db_session: Session):
    seed_trial(db_session, nct_id="NCT001", status=TrialStatus.RECRUITING)
    seed_trial(db_session, nct_id="NCT002", status=TrialStatus.COMPLETED)
    client = make_client(db_session)

    response = client.get("/api/trials", params={"status": "RECRUITING"})

    trials = response.json()["trials"]
    assert len(trials) == 1
    assert trials[0]["nct_id"] == "NCT001"


def test_get_trial_detail_returns_trial(db_session: Session):
    seed_trial(db_session)
    client = make_client(db_session)

    response = client.get("/api/trials/NCT01234567")

    assert response.status_code == 200
    assert response.json()["nct_id"] == "NCT01234567"


def test_get_trial_detail_returns_404_for_unknown_nct_id(db_session: Session):
    client = make_client(db_session)

    response = client.get("/api/trials/NCT99999999")

    assert response.status_code == 404


def test_get_trial_history_returns_change_events_newest_first(db_session: Session):
    from app.infrastructure.models import TrialChangeEventModel

    seed_trial(db_session)
    db_session.add_all(
        [
            TrialChangeEventModel(
                nct_id="NCT01234567",
                event_type="status_changed",
                old_value="NOT_YET_RECRUITING",
                new_value="RECRUITING",
                detected_at=datetime(2026, 1, 10, tzinfo=UTC),
            ),
            TrialChangeEventModel(
                nct_id="NCT01234567",
                event_type="enrollment_changed",
                old_value="100",
                new_value="120",
                detected_at=datetime(2026, 2, 1, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()
    client = make_client(db_session)

    response = client.get("/api/trials/NCT01234567/history")

    assert response.status_code == 200
    events = response.json()["events"]
    assert len(events) == 2
    assert events[0]["event_type"] == "enrollment_changed"
    assert events[0]["new_value"] == "120"
    assert events[1]["event_type"] == "status_changed"


def test_get_trial_history_returns_empty_list_when_no_changes(db_session: Session):
    seed_trial(db_session)
    client = make_client(db_session)

    response = client.get("/api/trials/NCT01234567/history")

    assert response.status_code == 200
    assert response.json()["events"] == []


def test_get_trial_history_returns_404_for_unknown_trial(db_session: Session):
    client = make_client(db_session)

    response = client.get("/api/trials/NCT99999999/history")

    assert response.status_code == 404
