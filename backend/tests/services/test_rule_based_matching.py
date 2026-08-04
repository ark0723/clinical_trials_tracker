from datetime import UTC, datetime

from app.domain.clinical_trial import ClinicalTrial, TrialLocation, TrialPhase, TrialStatus
from app.domain.eligibility import StructuredEligibility
from app.domain.matching import MatchScore
from app.domain.user_profile import (
    CancerStage,
    CurrentTreatment,
    NotificationChannel,
    UserProfile,
)
from app.services.geo import StaticZipGeocoder, set_zip_geocoder
from app.services.matching_engine import MatchingEngine, RuleBasedMatchingStrategy


def build_user(**overrides) -> UserProfile:
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


def build_trial(**overrides) -> ClinicalTrial:
    structured = StructuredEligibility(
        age_min=18,
        age_max=75,
        diagnosis="HER2-positive breast cancer",
        biomarkers=["HER2-positive"],
        extraction_confidence=0.67,
        extraction_method="rule",
    )
    defaults = dict(
        nct_id="NCT01234567",
        title="A HER2+ Study",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="Age >= 18 and <= 75. HER2-positive breast cancer.",
        structured_eligibility=structured,
        last_updated=datetime(2026, 1, 15, tzinfo=UTC),
    )
    defaults.update(overrides)
    return ClinicalTrial(**defaults)


def test_returns_zero_score_for_incompatible_biomarker():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            biomarkers=["HER2-negative"],
            extraction_confidence=0.5,
            extraction_method="rule",
        )
    )
    strategy = RuleBasedMatchingStrategy()

    score = strategy.calculate_compatibility(build_user(), trial)

    assert score.total == 0.0
    assert "Biomarker" in score.missing_criteria[0]


def test_returns_zero_score_when_age_outside_eligibility_range():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=40,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            extraction_confidence=0.67,
            extraction_method="rule",
        )
    )
    user = build_user(age=45)

    score = RuleBasedMatchingStrategy().calculate_compatibility(user, trial)

    assert score.total == 0.0
    assert any("Age" in item for item in score.missing_criteria)


def test_returns_high_score_for_age_within_eligibility_range():
    strategy = RuleBasedMatchingStrategy()

    score = strategy.calculate_compatibility(build_user(age=45), build_trial())

    assert score.total > 0.8
    assert score.factors["age"] == 1.0
    assert any("HER2" in item for item in score.matched_criteria)


def test_omits_travel_when_postal_code_is_missing():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            extraction_confidence=0.83,
            extraction_method="rule",
        ),
        locations=[TrialLocation(latitude=40.75, longitude=-73.99, city="New York")],
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert not any("Travel" in item or "travel" in item for item in score.unknown_criteria)
    assert not any("travel" in item.lower() for item in score.missing_criteria)
    assert score.factors["distance"] == 0.0
    assert score.total > 0


def test_matches_when_nearest_site_is_within_max_travel_miles(monkeypatch):
    set_zip_geocoder(StaticZipGeocoder({"10001": (40.7506, -73.9971)}))
    monkeypatch.setattr(
        "app.services.matching_engine.get_zip_geocoder",
        lambda: StaticZipGeocoder({"10001": (40.7506, -73.9971)}),
    )
    trial = build_trial(
        locations=[
            TrialLocation(latitude=40.7580, longitude=-73.9855, city="New York"),
        ]
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(
        build_user(postal_code="10001", max_travel_distance_miles=10),
        trial,
    )

    assert any("Within max travel distance" in item for item in score.matched_criteria)
    assert score.factors["distance"] == 1.0
    assert score.nearest_site_miles is not None
    assert score.nearest_site_miles < 5
    assert score.total == 1.0


def test_marks_missing_when_nearest_site_exceeds_max_travel_miles(monkeypatch):
    monkeypatch.setattr(
        "app.services.matching_engine.get_zip_geocoder",
        lambda: StaticZipGeocoder({"10001": (40.7506, -73.9971)}),
    )
    trial = build_trial(
        locations=[
            TrialLocation(latitude=42.3601, longitude=-71.0589, city="Boston"),
        ]
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(
        build_user(postal_code="10001", max_travel_distance_miles=10),
        trial,
    )

    assert any("travel" in item.lower() for item in score.missing_criteria)
    assert score.factors["distance"] == 0.0
    assert score.nearest_site_miles is not None
    assert score.nearest_site_miles > 10


def test_reports_ecog_and_brain_unknown_when_profile_answers_are_unknown():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            ecog=[0, 1],
            brain_metastasis=False,
            extraction_confidence=0.83,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert any("ECOG" in item for item in score.unknown_criteria)
    assert any("Brain metastasis" in item for item in score.unknown_criteria)


def test_matches_ecog_when_profile_value_is_allowed():
    from app.domain.user_profile import EcogStatus

    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            ecog=[0, 1],
            extraction_confidence=0.83,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(
        build_user(ecog=EcogStatus.RESTRICTED),
        trial,
    )

    assert any("ECOG" in item for item in score.matched_criteria)
    assert not any("ECOG" in item for item in score.unknown_criteria)


def test_matches_brain_metastasis_exclusion_when_user_has_none():
    from app.domain.user_profile import BrainMetastasisStatus

    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            brain_metastasis=False,
            extraction_confidence=0.67,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(
        build_user(brain_metastasis=BrainMetastasisStatus.NO),
        trial,
    )

    assert any("Brain metastasis" in item for item in score.matched_criteria)


def test_omits_prior_treatment_unknown_when_trial_has_no_prior_requirement():
    trial = build_trial()

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert not any("Prior treatment" in item for item in score.unknown_criteria)


def test_keeps_age_and_diagnosis_unknown_when_structured_fields_missing():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            biomarkers=["HER2-positive"],
            extraction_confidence=0.17,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert any("Age" in item for item in score.unknown_criteria)
    assert any("Diagnosis" in item for item in score.unknown_criteria)
    assert not any("Travel distance" in item for item in score.unknown_criteria)


def test_does_not_hard_exclude_when_structured_eligibility_is_missing():
    trial = build_trial(structured_eligibility=None)

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert score.total > 0
    assert score.confidence == 0.0
    assert any("unable to verify" in item.lower() for item in score.unknown_criteria)


def test_does_not_hard_exclude_on_age_when_extraction_confidence_is_very_low():
    """Low-confidence age bounds must not trigger hard exclude (extractor may be wrong)."""
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=40,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            extraction_confidence=0.17,
            extraction_method="rule",
        )
    )
    user = build_user(age=45)

    score = RuleBasedMatchingStrategy().calculate_compatibility(user, trial)

    assert score.total > 0
    assert any("Age" in item for item in score.unknown_criteria)
    assert score.missing_criteria == []


def test_matching_engine_returns_sorted_recommendations():
    good = build_trial(nct_id="NCT001", title="Good fit")
    weak = build_trial(
        nct_id="NCT002",
        title="Weak HER2+ fit",
        structured_eligibility=StructuredEligibility(
            biomarkers=["HER2-positive"],
            extraction_confidence=0.17,
            extraction_method="rule",
        ),
    )
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(build_user(), [weak, good], limit=2)

    assert len(results) == 2
    assert results[0].trial.nct_id == "NCT001"
    assert results[0].total > results[1].total
    assert isinstance(results[0], MatchScore)


def test_single_biomarker_match_is_not_inflated_to_100_percent():
    """Unknown criteria must reduce score; do not renormalize over matched factors only."""
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            biomarkers=["HER2-positive"],
            extraction_confidence=0.17,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert score.total < 0.5
    assert any("Age" in item for item in score.unknown_criteria)
    assert any("Diagnosis" in item for item in score.unknown_criteria)


def test_full_core_match_with_unknown_distance_scores_high_but_not_perfect():
    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), build_trial())

    assert 0.8 <= score.total < 1.0
    # No ZIP yet → distance unscored (not listed as unknown noise).
    assert score.factors["distance"] == 0.0
    assert not any("Travel distance" in item for item in score.unknown_criteria)


def test_missing_prior_treatment_reduces_score():
    trial = build_trial(
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            prior_treatments=["pertuzumab"],
            extraction_confidence=0.67,
            extraction_method="rule",
        )
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert any("prior treatment" in item.lower() for item in score.missing_criteria)
    assert score.total < 0.8


def test_hard_excludes_her2_negative_title_for_her2_positive_user():
    trial = build_trial(
        title="ER Positive HER2 Negative Breast Cancer Study",
        structured_eligibility=StructuredEligibility(
            biomarkers=[],
            extraction_confidence=0.5,
            extraction_method="rule",
        ),
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert score.total == 0.0
    assert any("Biomarker" in item for item in score.missing_criteria)


def test_hard_excludes_triple_negative_title_for_her2_positive_user():
    trial = build_trial(
        title="Pembrolizumab in Triple-Negative Breast Cancer",
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            biomarkers=["HER2-positive"],  # noisy extraction must not override clear title
            extraction_confidence=0.5,
            extraction_method="rule",
        ),
    )

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert score.total == 0.0


def test_is_hard_excluded_uses_title_signal():
    from app.services.matching_engine import is_hard_excluded

    trial = build_trial(
        title="HR+ and HER2- Breast Cancer Observational Study",
        structured_eligibility=StructuredEligibility(
            extraction_confidence=0.2,
            extraction_method="rule",
        ),
    )

    assert is_hard_excluded(build_user(), trial) is True


def test_recommendations_prefer_higher_confidence_when_scores_tie():
    high_conf = build_trial(
        nct_id="NCT-HI",
        title="HER2+ high confidence",
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            extraction_confidence=0.83,
            extraction_method="rule",
        ),
    )
    low_conf = build_trial(
        nct_id="NCT-LO",
        title="HER2+ low confidence",
        structured_eligibility=StructuredEligibility(
            age_min=18,
            age_max=75,
            diagnosis="HER2-positive breast cancer",
            biomarkers=["HER2-positive"],
            extraction_confidence=0.17,
            extraction_method="rule",
        ),
    )
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(build_user(), [low_conf, high_conf], limit=2)

    assert results[0].trial.nct_id == "NCT-HI"
    assert results[1].trial.nct_id == "NCT-LO"


def test_recommendations_exclude_trials_beyond_max_travel_distance(monkeypatch):
    monkeypatch.setattr(
        "app.services.matching_engine.get_zip_geocoder",
        lambda: StaticZipGeocoder({"10001": (40.7506, -73.9971)}),
    )
    in_range = build_trial(
        nct_id="NCT-NEAR",
        title="HER2+ nearby",
        locations=[
            TrialLocation(latitude=40.7580, longitude=-73.9855, city="New York"),
        ],
    )
    too_far = build_trial(
        nct_id="NCT-FAR",
        title="HER2+ far away China site",
        locations=[
            TrialLocation(latitude=39.9042, longitude=116.4074, city="Beijing"),
        ],
    )
    no_sites = build_trial(
        nct_id="NCT-NOSITE",
        title="HER2+ without sites",
        locations=[],
    )
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(
        build_user(postal_code="10001", max_travel_distance_miles=25),
        [too_far, no_sites, in_range],
        limit=10,
    )

    assert [item.trial.nct_id for item in results] == ["NCT-NEAR", "NCT-NOSITE"]
    assert results[0].nearest_site_miles is not None
    assert results[0].nearest_site_miles < 25


def test_recommendations_prefer_nearer_in_range_site(monkeypatch):
    monkeypatch.setattr(
        "app.services.matching_engine.get_zip_geocoder",
        lambda: StaticZipGeocoder({"10001": (40.7506, -73.9971)}),
    )
    nearer = build_trial(
        nct_id="NCT-CLOSER",
        title="Closer site",
        locations=[
            TrialLocation(latitude=40.7580, longitude=-73.9855, city="New York"),
        ],
    )
    farther = build_trial(
        nct_id="NCT-FARTHER",
        title="Farther but still in range",
        locations=[
            # Philadelphia ~80 miles from NYC ZIP — still within 100 mi max in this test (50).
            TrialLocation(latitude=39.9526, longitude=-75.1652, city="Philadelphia"),
        ],
    )
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(
        build_user(postal_code="10001", max_travel_distance_miles=100),
        [farther, nearer],
        limit=2,
    )

    assert results[0].trial.nct_id == "NCT-CLOSER"
    assert results[0].nearest_site_miles < results[1].nearest_site_miles


def test_recommendations_drop_zero_score_trials():
    excluded = build_trial(
        nct_id="NCT-EX",
        title="HER2 Negative Only Study",
        structured_eligibility=StructuredEligibility(
            biomarkers=["HER2-negative"],
            extraction_confidence=0.5,
            extraction_method="rule",
        ),
    )
    good = build_trial(nct_id="NCT-OK", title="HER2+ Study")
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(build_user(), [excluded, good], limit=10)

    assert [item.trial.nct_id for item in results] == ["NCT-OK"]
