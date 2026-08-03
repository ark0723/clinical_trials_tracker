from datetime import UTC, datetime

from app.domain.clinical_trial import TrialPhase, TrialStatus
from app.infrastructure.ctgov_mapper import map_study_to_trial


def build_raw_study(**overrides) -> dict:
    raw = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT01234567",
                "briefTitle": "A Study of Trastuzumab Deruxtecan in HER2-positive Breast Cancer",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "lastUpdatePostDateStruct": {"date": "2026-01-15"},
            },
            "designModule": {
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 120, "type": "ESTIMATED"},
            },
            "eligibilityModule": {
                "eligibilityCriteria": (
                    "Inclusion Criteria:\n- Age >= 18\n- HER2-positive breast cancer"
                ),
            },
            "contactsLocationsModule": {
                "locations": [
                    {
                        "facility": "Seoul National University Hospital",
                        "city": "Seoul",
                        "country": "South Korea",
                        "geoPoint": {"lat": 37.5665, "lon": 126.9780},
                    }
                ]
            },
        },
        "hasResults": False,
    }
    raw.update(overrides)
    return raw


def test_map_study_to_trial_extracts_core_fields():
    trial = map_study_to_trial(build_raw_study())

    assert trial.nct_id == "NCT01234567"
    assert "Trastuzumab Deruxtecan" in trial.title
    assert trial.phase == TrialPhase.PHASE_2
    assert trial.status == TrialStatus.RECRUITING
    assert trial.enrollment_count == 120
    assert trial.has_results is False
    assert trial.last_updated == datetime(2026, 1, 15, tzinfo=UTC)
    assert "HER2-positive" in trial.eligibility_criteria_raw


def test_map_study_to_trial_extracts_locations():
    trial = map_study_to_trial(build_raw_study())

    assert len(trial.locations) == 1
    location = trial.locations[0]
    assert location.facility == "Seoul National University Hospital"
    assert location.city == "Seoul"
    assert location.country == "South Korea"
    assert location.latitude == 37.5665
    assert location.longitude == 126.9780


def test_map_study_to_trial_defaults_missing_optional_fields():
    raw = build_raw_study()
    del raw["protocolSection"]["designModule"]["enrollmentInfo"]
    raw["protocolSection"]["contactsLocationsModule"] = {}
    del raw["hasResults"]

    trial = map_study_to_trial(raw)

    assert trial.enrollment_count is None
    assert trial.locations == []
    assert trial.has_results is False


def test_map_study_to_trial_defaults_missing_phase_to_not_applicable():
    raw = build_raw_study()
    raw["protocolSection"]["designModule"]["phases"] = []

    trial = map_study_to_trial(raw)

    assert trial.phase == TrialPhase.NOT_APPLICABLE


def test_map_study_to_trial_maps_expanded_access_statuses():
    """ClinicalTrials.gov reports these for expanded-access ("compassionate use")
    studies; they are outside the recruiting/completed lifecycle but still
    valid values the API can return (see API v2 Status schema)."""
    for raw_status, expected in [
        ("AVAILABLE", TrialStatus.AVAILABLE),
        ("NO_LONGER_AVAILABLE", TrialStatus.NO_LONGER_AVAILABLE),
        ("APPROVED_FOR_MARKETING", TrialStatus.APPROVED_FOR_MARKETING),
        ("WITHHELD", TrialStatus.WITHHELD),
    ]:
        raw = build_raw_study()
        raw["protocolSection"]["statusModule"]["overallStatus"] = raw_status

        trial = map_study_to_trial(raw)

        assert trial.status == expected


def test_map_study_to_trial_defaults_unrecognized_status_to_unknown():
    """A future/unlisted status value from the API must not crash the sync
    job; fall back to UNKNOWN so one bad trial doesn't block the whole batch."""
    raw = build_raw_study()
    raw["protocolSection"]["statusModule"]["overallStatus"] = "SOME_NEW_STATUS"

    trial = map_study_to_trial(raw)

    assert trial.status == TrialStatus.UNKNOWN
