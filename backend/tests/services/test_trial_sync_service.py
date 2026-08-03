from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    ClinicalTrialModel,
    StructuredEligibilityModel,
    TrialChangeEventModel,
)
from app.services.trial_sync_service import sync_clinical_trials


class FakeClinicalTrialsGovClient:
    """Test double standing in for ClinicalTrialsGovClient (external dependency mock)."""

    def __init__(self, studies: list[dict[str, Any]]):
        self._studies = studies

    def search_studies(
        self, condition: str, statuses: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        yield from self._studies


def build_raw_study(**overrides) -> dict:
    raw = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT01234567", "briefTitle": "A HER2+ Study"},
            "statusModule": {
                "overallStatus": "RECRUITING",
                "lastUpdatePostDateStruct": {"date": "2026-01-15"},
            },
            "designModule": {
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 120, "type": "ESTIMATED"},
            },
            "eligibilityModule": {"eligibilityCriteria": "Age >= 18. HER2-positive."},
            "contactsLocationsModule": {"locations": []},
        },
        "hasResults": False,
    }
    raw.update(overrides)
    return raw


def test_sync_creates_new_trial_when_not_in_db(db_session: Session):
    client = FakeClinicalTrialsGovClient([build_raw_study()])

    result = sync_clinical_trials(db_session, client, condition="HER2-positive breast cancer")

    trial = db_session.get(ClinicalTrialModel, "NCT01234567")
    assert trial is not None
    assert trial.status.value == "RECRUITING"
    assert result.created == 1
    assert result.updated == 0
    assert result.events == []


def test_sync_extracts_and_persists_structured_eligibility(db_session: Session):
    raw = build_raw_study()
    raw["protocolSection"]["eligibilityModule"]["eligibilityCriteria"] = (
        "Age >= 18 and <= 75. HER2-positive breast cancer. "
        "ECOG performance status 0 or 1."
    )

    sync_clinical_trials(
        db_session,
        FakeClinicalTrialsGovClient([raw]),
        condition="HER2-positive breast cancer",
    )

    trial = db_session.get(ClinicalTrialModel, "NCT01234567")
    structured = db_session.get(StructuredEligibilityModel, "NCT01234567")
    assert trial is not None
    assert structured is not None
    assert structured.age_min == 18
    assert structured.age_max == 75
    assert structured.biomarkers == ["HER2-positive"]
    assert structured.ecog == [0, 1]
    assert trial.eligibility_criteria_simplified is not None
    assert "ages 18 to 75" in trial.eligibility_criteria_simplified


def test_sync_detects_status_change_and_creates_event(db_session: Session):
    existing_raw = build_raw_study()
    existing_raw["protocolSection"]["statusModule"]["overallStatus"] = "NOT_YET_RECRUITING"
    sync_clinical_trials(db_session, FakeClinicalTrialsGovClient([existing_raw]), condition="x")

    updated_raw = build_raw_study()  # overallStatus == RECRUITING
    result = sync_clinical_trials(
        db_session, FakeClinicalTrialsGovClient([updated_raw]), condition="x"
    )

    trial = db_session.get(ClinicalTrialModel, "NCT01234567")
    assert trial.status.value == "RECRUITING"
    assert result.updated == 1
    assert len(result.events) == 1
    assert result.events[0].event_type == "status_changed"
    assert result.events[0].old_value == "NOT_YET_RECRUITING"
    assert result.events[0].new_value == "RECRUITING"

    stored_events = db_session.query(TrialChangeEventModel).all()
    assert len(stored_events) == 1
    assert stored_events[0].event_type == "status_changed"


def test_sync_detects_enrollment_change_and_creates_event(db_session: Session):
    sync_clinical_trials(
        db_session, FakeClinicalTrialsGovClient([build_raw_study()]), condition="x"
    )

    updated_raw = build_raw_study()
    updated_raw["protocolSection"]["designModule"]["enrollmentInfo"]["count"] = 200
    result = sync_clinical_trials(
        db_session, FakeClinicalTrialsGovClient([updated_raw]), condition="x"
    )

    assert any(e.event_type == "enrollment_changed" for e in result.events)
    event = next(e for e in result.events if e.event_type == "enrollment_changed")
    assert event.old_value == "120"
    assert event.new_value == "200"


def test_sync_detects_results_posted_and_creates_event(db_session: Session):
    sync_clinical_trials(
        db_session, FakeClinicalTrialsGovClient([build_raw_study()]), condition="x"
    )

    updated_raw = build_raw_study(hasResults=True)
    result = sync_clinical_trials(
        db_session, FakeClinicalTrialsGovClient([updated_raw]), condition="x"
    )

    assert any(e.event_type == "results_posted" for e in result.events)


def test_sync_does_not_create_events_when_nothing_changed(db_session: Session):
    raw = build_raw_study()
    sync_clinical_trials(db_session, FakeClinicalTrialsGovClient([raw]), condition="x")

    result = sync_clinical_trials(db_session, FakeClinicalTrialsGovClient([raw]), condition="x")

    assert result.updated == 1
    assert result.events == []
    assert db_session.query(TrialChangeEventModel).count() == 0


class PartiallyFailingClient:
    """Simulates an upstream failure (e.g. exhausted retries) partway through a sync."""

    def search_studies(
        self, condition: str, statuses: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        yield build_raw_study()
        raise RuntimeError("ClinicalTrials.gov unavailable")


def test_sync_commits_incrementally_so_earlier_trials_survive_a_later_failure(
    db_session: Session,
):
    with pytest.raises(RuntimeError):
        sync_clinical_trials(db_session, PartiallyFailingClient(), condition="x")

    # The first trial was processed before the failure and must not be lost,
    # even though the overall sync raised (see plan's incremental-commit decision).
    trial = db_session.get(ClinicalTrialModel, "NCT01234567")
    assert trial is not None
