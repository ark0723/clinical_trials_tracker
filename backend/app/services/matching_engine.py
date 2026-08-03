"""Rule-based patient-trial matching (MVP — no LLM).

Uses StructuredEligibility produced at sync time; never re-parses raw eligibility
text during matching (see docs/03-feature-spec.mdc 기능 3).
"""

from abc import ABC, abstractmethod

from app.domain.clinical_trial import ClinicalTrial
from app.domain.eligibility import StructuredEligibility
from app.domain.matching import MatchScore
from app.domain.user_profile import UserProfile

# Require at least ~2 extracted fields before trusting age for hard exclude.
_MIN_CONFIDENCE_FOR_AGE_DECISION = 0.34

_FACTOR_WEIGHTS = {
    "age": 0.30,
    "biomarker": 0.30,
    "diagnosis": 0.25,
    "distance": 0.15,
}


class MatchingStrategy(ABC):
    @abstractmethod
    def calculate_compatibility(
        self, user_profile: UserProfile, trial: ClinicalTrial
    ) -> MatchScore: ...


class RuleBasedMatchingStrategy(MatchingStrategy):
    """Scores trials using structured eligibility only."""

    def calculate_compatibility(
        self, user_profile: UserProfile, trial: ClinicalTrial
    ) -> MatchScore:
        structured = trial.structured_eligibility
        if structured is None:
            return self._score_without_structure(user_profile, trial)

        matched: list[str] = []
        missing: list[str] = []
        unknown: list[str] = []
        factors: dict[str, float] = {}

        age_outcome = _evaluate_age(user_profile, structured)
        if age_outcome == "exclude":
            return self._excluded_score(
                user_profile,
                trial,
                structured,
                missing=["Age outside eligible range"],
                rationale="You are outside the age range listed for this trial.",
            )
        if age_outcome == "match":
            matched.append("Age within eligible range")
            factors["age"] = 1.0
        elif age_outcome == "unknown":
            unknown.append("Age: unable to verify")

        biomarker_outcome = _evaluate_biomarkers(user_profile, structured)
        if biomarker_outcome == "exclude":
            return self._excluded_score(
                user_profile,
                trial,
                structured,
                missing=["Biomarker requirements not met"],
                rationale="Your biomarker profile does not match this trial's requirements.",
            )
        if biomarker_outcome == "match":
            matched.append("HER2+ biomarker")
            factors["biomarker"] = 1.0
        elif biomarker_outcome == "unknown":
            unknown.append("Biomarker: unable to verify")

        diagnosis_outcome = _evaluate_diagnosis(user_profile, structured)
        if diagnosis_outcome == "match":
            matched.append("HER2-positive breast cancer diagnosis")
            factors["diagnosis"] = 1.0
        elif diagnosis_outcome == "unknown":
            unknown.append("Diagnosis: unable to verify")

        unknown.append("Travel distance: unable to verify (location not provided)")

        prior_outcome = _evaluate_prior_treatments(user_profile, structured)
        if prior_outcome == "match":
            matched.append("Prior treatment history")
        elif prior_outcome == "missing":
            missing.append("Required prior treatment")
        elif prior_outcome == "unknown":
            unknown.append("Prior treatment: unable to verify")

        if structured.ecog:
            unknown.append("ECOG performance status: unable to verify")

        if structured.brain_metastasis is False:
            unknown.append("Brain metastasis status: unable to verify")

        total = _weighted_total(factors)
        rationale = _build_rationale(matched, missing, unknown, total)

        return MatchScore(
            trial=trial,
            total=total,
            factors=factors,
            matched_criteria=matched,
            missing_criteria=missing,
            unknown_criteria=unknown,
            confidence=structured.extraction_confidence,
            rationale=rationale,
        )

    @staticmethod
    def _score_without_structure(user_profile: UserProfile, trial: ClinicalTrial) -> MatchScore:
        unknown = [
            "Structured eligibility: unable to verify",
            "Travel distance: unable to verify (location not provided)",
        ]
        matched: list[str] = []
        if user_profile.cancer_type == "HER2_POSITIVE_BREAST":
            matched.append("HER2-positive breast cancer (profile)")
        return MatchScore(
            trial=trial,
            total=0.35 if matched else 0.1,
            factors={},
            matched_criteria=matched,
            missing_criteria=[],
            unknown_criteria=unknown,
            confidence=0.0,
            rationale=(
                "We could not verify detailed eligibility criteria for this trial yet. "
                "Review the full eligibility text with your care team."
            ),
        )

    @staticmethod
    def _excluded_score(
        user_profile: UserProfile,
        trial: ClinicalTrial,
        structured: StructuredEligibility,
        *,
        missing: list[str],
        rationale: str,
    ) -> MatchScore:
        _ = user_profile
        return MatchScore(
            trial=trial,
            total=0.0,
            factors={"age": 0.0} if "Age" in missing[0] else {"biomarker": 0.0},
            matched_criteria=[],
            missing_criteria=missing,
            unknown_criteria=[],
            confidence=structured.extraction_confidence,
            rationale=rationale,
        )


class MatchingEngine:
    def __init__(self, strategy: MatchingStrategy):
        self._strategy = strategy

    def get_recommendations(
        self, user_profile: UserProfile, trials: list[ClinicalTrial], limit: int = 10
    ) -> list[MatchScore]:
        scores = [
            self._strategy.calculate_compatibility(user_profile, trial) for trial in trials
        ]
        scores.sort(key=lambda score: score.total, reverse=True)
        return scores[:limit]


def _evaluate_age(user: UserProfile, structured: StructuredEligibility) -> str:
    if structured.age_min is None and structured.age_max is None:
        return "unknown"
    if not _age_bounds_are_trustworthy(structured):
        return "unknown"

    if structured.age_min is not None and user.age < structured.age_min:
        return "exclude"
    if structured.age_max is not None and user.age > structured.age_max:
        return "exclude"
    return "match"


def _age_bounds_are_trustworthy(structured: StructuredEligibility) -> bool:
    if structured.extraction_confidence < _MIN_CONFIDENCE_FOR_AGE_DECISION:
        return False
    for bound in (structured.age_min, structured.age_max):
        if bound is not None and not (0 <= bound <= 120):
            return False
    return True


def _normalize_biomarker(label: str) -> str:
    normalized = label.lower().replace("_", "-")
    if normalized in {"her2-positive", "her2+"}:
        return "her2-positive"
    if normalized in {"her2-negative", "her2-"}:
        return "her2-negative"
    return normalized


def _user_biomarkers(user: UserProfile) -> set[str]:
    markers = {_normalize_biomarker(marker) for marker in user.biomarkers}
    if user.cancer_type == "HER2_POSITIVE_BREAST":
        markers.add("her2-positive")
    return markers


def _evaluate_biomarkers(user: UserProfile, structured: StructuredEligibility) -> str:
    if not structured.biomarkers:
        return "unknown"

    trial_markers = {_normalize_biomarker(marker) for marker in structured.biomarkers}
    user_markers = _user_biomarkers(user)

    if "her2-negative" in trial_markers and "her2-positive" in user_markers:
        return "exclude"
    if "her2-positive" in trial_markers and "her2-positive" in user_markers:
        return "match"
    if trial_markers & user_markers:
        return "match"
    return "unknown"


def _evaluate_diagnosis(user: UserProfile, structured: StructuredEligibility) -> str:
    if structured.diagnosis is None:
        return "unknown"
    diagnosis = structured.diagnosis.lower()
    if user.cancer_type == "HER2_POSITIVE_BREAST" and "her2" in diagnosis and "breast" in diagnosis:
        return "match"
    return "unknown"


def _evaluate_prior_treatments(user: UserProfile, structured: StructuredEligibility) -> str:
    if not structured.prior_treatments:
        return "unknown"
    if not user.current_treatment:
        return "missing"
    current = user.current_treatment.lower()
    if any(treatment.lower() in current for treatment in structured.prior_treatments):
        return "match"
    return "missing"


def _weighted_total(factors: dict[str, float]) -> float:
    if not factors:
        return 0.0
    weight_sum = sum(_FACTOR_WEIGHTS[name] for name in factors)
    if weight_sum == 0:
        return 0.0
    total = sum(factors[name] * _FACTOR_WEIGHTS[name] for name in factors) / weight_sum
    return round(min(max(total, 0.0), 1.0), 2)


def _build_rationale(
    matched: list[str], missing: list[str], unknown: list[str], total: float
) -> str:
    parts: list[str] = []
    if matched:
        parts.append("Matched: " + "; ".join(matched) + ".")
    if missing:
        parts.append("Not met: " + "; ".join(missing) + ".")
    if unknown:
        parts.append("Unable to verify: " + "; ".join(unknown) + ".")
    if not parts:
        return "Limited structured eligibility data is available for this trial."
    parts.append(f"Overall compatibility score: {int(total * 100)}%.")
    return " ".join(parts)
