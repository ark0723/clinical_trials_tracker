from datetime import UTC, datetime

from app.domain.clinical_trial import ClinicalTrial, TrialPhase, TrialStatus
from app.domain.eligibility import StructuredEligibility
from app.domain.matching import MatchScore
from app.domain.user_profile import CancerStage, NotificationChannel, UserProfile
from app.services.matching_engine import MatchingEngine, RuleBasedMatchingStrategy


def build_user(**overrides) -> UserProfile:
    defaults = dict(
        id="user-1",
        age=45,
        cancer_type="HER2_POSITIVE_BREAST",
        stage=CancerStage.STAGE_III,
        biomarkers=["HER2-positive"],
        current_treatment="trastuzumab",
        max_travel_distance_km=100,
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


def test_marks_ecog_as_unknown_when_user_profile_lacks_ecog():
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

    score = RuleBasedMatchingStrategy().calculate_compatibility(build_user(), trial)

    assert any("ECOG" in item for item in score.unknown_criteria)
    assert score.total > 0


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
        title="Weak fit",
        structured_eligibility=StructuredEligibility(
            extraction_confidence=0.0,
            extraction_method="rule",
        ),
    )
    engine = MatchingEngine(RuleBasedMatchingStrategy())

    results = engine.get_recommendations(build_user(), [weak, good], limit=2)

    assert len(results) == 2
    assert results[0].total >= results[1].total
    assert isinstance(results[0], MatchScore)
