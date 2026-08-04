from datetime import UTC, datetime

from app.domain.user_profile import CancerStage, CurrentTreatment, NotificationChannel, UserProfile
from app.infrastructure.models import (
    ClinicalTrialModel,
    StructuredEligibilityModel,
    TrialLocationModel,
)
from app.services.trial_match_loader import (
    clear_candidate_cache,
    fetch_candidate_trials,
    fetch_trials_by_nct_ids,
    get_cached_active_match_trials,
    load_active_match_trials,
)


def build_profile(**overrides) -> UserProfile:
    defaults = dict(
        id="user-1",
        age=45,
        cancer_type="HER2_POSITIVE_BREAST",
        stage=CancerStage.STAGE_III,
        biomarkers=["HER2-positive"],
        current_treatment=CurrentTreatment.TRASTUZUMAB,
        max_travel_distance_miles=100,
        notification_channels=[NotificationChannel.EMAIL],
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def seed_trial(
    db_session,
    *,
    nct_id: str,
    age_min: int | None,
    age_max: int | None,
    confidence: float,
    biomarkers: list[str] | None = None,
):
    from app.domain.clinical_trial import TrialPhase, TrialStatus

    trial = ClinicalTrialModel(
        nct_id=nct_id,
        title=f"Trial {nct_id}",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="x" * 5000,
        enrollment_count=100,
        has_results=False,
        last_updated=datetime(2026, 1, 15, tzinfo=UTC),
        locations=[
            TrialLocationModel(
                facility="Test Center",
                city="Boston",
                country="United States",
                latitude=42.3601,
                longitude=-71.0589,
            ),
        ],
    )
    structured = StructuredEligibilityModel(
        nct_id=nct_id,
        age_min=age_min,
        age_max=age_max,
        diagnosis="HER2-positive breast cancer",
        prior_treatments=[],
        ecog=[],
        biomarkers=biomarkers if biomarkers is not None else ["HER2-positive"],
        brain_metastasis=None,
        extraction_confidence=confidence,
        extraction_method="rule",
    )
    db_session.add(trial)
    db_session.add(structured)
    db_session.commit()


def test_fetch_candidate_trials_excludes_trustworthy_age_mismatch(db_session):
    clear_candidate_cache()
    seed_trial(db_session, nct_id="NCT-IN", age_min=18, age_max=40, confidence=0.67)
    seed_trial(db_session, nct_id="NCT-OK", age_min=18, age_max=75, confidence=0.67)

    candidates = fetch_candidate_trials(db_session, build_profile(age=45))
    nct_ids = {trial.nct_id for trial in candidates}

    assert "NCT-OK" in nct_ids
    assert "NCT-IN" not in nct_ids


def test_fetch_candidate_trials_keeps_low_confidence_age_bounds(db_session):
    clear_candidate_cache()
    seed_trial(db_session, nct_id="NCT-LOW", age_min=18, age_max=40, confidence=0.17)

    candidates = fetch_candidate_trials(db_session, build_profile(age=45))
    nct_ids = {trial.nct_id for trial in candidates}

    assert "NCT-LOW" in nct_ids


def test_fetch_candidate_trials_excludes_her2_negative_conflict(db_session):
    clear_candidate_cache()
    seed_trial(
        db_session,
        nct_id="NCT-NEG",
        age_min=18,
        age_max=75,
        confidence=0.67,
        biomarkers=["HER2-negative"],
    )
    seed_trial(db_session, nct_id="NCT-POS", age_min=18, age_max=75, confidence=0.67)

    candidates = fetch_candidate_trials(db_session, build_profile())
    nct_ids = {trial.nct_id for trial in candidates}

    assert "NCT-POS" in nct_ids
    assert "NCT-NEG" not in nct_ids


def test_load_active_match_trials_includes_site_coordinates(db_session):
    clear_candidate_cache()
    seed_trial(db_session, nct_id="NCT-LEAN", age_min=18, age_max=75, confidence=0.67)

    trials = load_active_match_trials(db_session)
    trial = next(item for item in trials if item.nct_id == "NCT-LEAN")

    assert trial.eligibility_criteria_raw == ""
    assert len(trial.locations) == 1
    assert trial.locations[0].city == "Boston"
    assert trial.structured_eligibility is not None
    assert trial.structured_eligibility.biomarkers == ["HER2-positive"]


def test_candidate_cache_reuses_loaded_trials(db_session):
    clear_candidate_cache()
    seed_trial(db_session, nct_id="NCT-CACHE", age_min=18, age_max=75, confidence=0.67)

    first = get_cached_active_match_trials(db_session)
    second = get_cached_active_match_trials(db_session)

    assert first is second
    assert first[0].nct_id == "NCT-CACHE"


def test_fetch_trials_by_nct_ids_hydrates_full_trial_payload(db_session):
    seed_trial(db_session, nct_id="NCT-FULL", age_min=18, age_max=75, confidence=0.67)

    trials = fetch_trials_by_nct_ids(db_session, ["NCT-FULL"])
    trial = trials["NCT-FULL"]

    assert trial.eligibility_criteria_raw.startswith("x")
    assert len(trial.locations) == 1
    assert trial.locations[0].city == "Boston"
