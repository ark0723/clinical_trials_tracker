"""Rule-based patient-trial matching (MVP — no LLM).

Uses StructuredEligibility produced at sync time; never re-parses raw eligibility
text during matching (see docs/03-feature-spec.mdc 기능 3).

Reliability rules:
- Score against the full factor weight denominator (no inflation when few factors match).
- Unknown / missing criteria reduce the score instead of being ignored.
- Clear HER2-negative / TNBC signals in title or structured data hard-exclude HER2+ users.
- Rank by score, then extraction confidence; drop zero-score trials from recommendations.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.domain.clinical_trial import ClinicalTrial
from app.domain.eligibility import StructuredEligibility
from app.domain.matching import MatchScore
from app.domain.user_profile import (
    BrainMetastasisStatus,
    CurrentTreatment,
    TREATMENT_MATCH_TERMS,
    UserProfile,
)
from app.services.geo import get_zip_geocoder, nearest_site_distance_miles

# Require at least ~2 extracted fields before trusting age for hard exclude.
_MIN_CONFIDENCE_FOR_AGE_DECISION = 0.34
_MISSING_CRITERION_PENALTY = 0.15

_FACTOR_WEIGHTS = {
    "age": 0.30,
    "biomarker": 0.30,
    "diagnosis": 0.25,
    "distance": 0.15,
}
_TOTAL_WEIGHT = sum(_FACTOR_WEIGHTS.values())

_HER2_NEGATIVE_TITLE = re.compile(
    r"""
    triple[\s-]?negative
    | \btnbc\b
    | her[\s-]?2[\s\-]*(?:negative|neg\b)
    | her[\s-]?2\s*-(?!\s*positive)
    """,
    re.IGNORECASE | re.VERBOSE,
)


class MatchingStrategy(ABC):
    @abstractmethod
    def calculate_compatibility(
        self, user_profile: UserProfile, trial: ClinicalTrial
    ) -> MatchScore: ...


class RuleBasedMatchingStrategy(MatchingStrategy):
    """Scores trials using structured eligibility only (plus title hard filters)."""

    def calculate_compatibility(
        self, user_profile: UserProfile, trial: ClinicalTrial
    ) -> MatchScore:
        if _her2_positive_user_incompatible(user_profile, trial):
            confidence = (
                trial.structured_eligibility.extraction_confidence
                if trial.structured_eligibility is not None
                else 0.0
            )
            return MatchScore(
                trial=trial,
                total=0.0,
                factors={"biomarker": 0.0},
                matched_criteria=[],
                missing_criteria=["Biomarker requirements not met"],
                unknown_criteria=[],
                confidence=confidence,
                rationale="Your biomarker profile does not match this trial's requirements.",
            )

        structured = trial.structured_eligibility
        if structured is None:
            return self._score_without_structure(user_profile, trial)

        matched: list[str] = []
        missing: list[str] = []
        unknown: list[str] = []
        factors: dict[str, float] = {
            "age": 0.0,
            "biomarker": 0.0,
            "diagnosis": 0.0,
            "distance": 0.0,  # location not in MVP profile
        }

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
        else:
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
        else:
            unknown.append("Biomarker: unable to verify")

        diagnosis_outcome = _evaluate_diagnosis(user_profile, structured)
        if diagnosis_outcome == "match":
            matched.append("HER2-positive breast cancer diagnosis")
            factors["diagnosis"] = 1.0
        else:
            unknown.append("Diagnosis: unable to verify")

        distance_outcome, nearest_site_miles = _evaluate_distance(user_profile, trial)
        distance_soft_penalties = 0
        if distance_outcome == "match":
            miles_label = (
                f"Within max travel distance ({nearest_site_miles:.0f} mi to nearest site)"
                if nearest_site_miles is not None
                else "Within max travel distance"
            )
            matched.append(miles_label)
            factors["distance"] = 1.0
        elif distance_outcome == "missing":
            missing.append("Nearest site exceeds max travel distance")
        elif distance_outcome == "no_sites":
            unknown.append("Travel distance: unable to verify (no trial sites listed)")
            # Soft-demote so no-site trials do not outrank trials with known sites.
            distance_soft_penalties = 1
        elif distance_outcome == "unknown":
            unknown.append("Travel distance: unable to verify")

        prior_outcome = _evaluate_prior_treatments(user_profile, structured)
        if prior_outcome == "match":
            matched.append("Prior treatment history")
        elif prior_outcome == "missing":
            missing.append("Required prior treatment")
        elif prior_outcome == "unknown":
            unknown.append("Prior treatment: unable to verify")

        ecog_outcome = _evaluate_ecog(user_profile, structured)
        if ecog_outcome == "match":
            matched.append("ECOG performance status")
        elif ecog_outcome == "missing":
            missing.append("ECOG performance status requirement not met")
        elif ecog_outcome == "unknown":
            unknown.append("ECOG performance status: unable to verify")

        brain_outcome = _evaluate_brain_metastasis(user_profile, structured)
        if brain_outcome == "match":
            matched.append("Brain metastasis status")
        elif brain_outcome == "missing":
            missing.append("Brain metastasis status does not meet trial criteria")
        elif brain_outcome == "unknown":
            unknown.append("Brain metastasis status: unable to verify")

        total = _weighted_total(
            factors,
            missing_count=len(missing) + distance_soft_penalties,
        )
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
            nearest_site_miles=nearest_site_miles,
        )

    @staticmethod
    def _score_without_structure(user_profile: UserProfile, trial: ClinicalTrial) -> MatchScore:
        unknown = ["Structured eligibility: unable to verify"]
        matched: list[str] = []
        factors = {"age": 0.0, "biomarker": 0.0, "diagnosis": 0.0, "distance": 0.0}
        if user_profile.cancer_type == "HER2_POSITIVE_BREAST":
            matched.append("HER2-positive breast cancer (profile)")
            # Weak prior without structured data — do not claim high compatibility.
            factors["biomarker"] = 0.35
        total = _weighted_total(factors)
        return MatchScore(
            trial=trial,
            total=total,
            factors=factors,
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
        scores = [score for score in scores if score.total > 0]
        # Max travel distance is a hard preference once we can measure it.
        scores = [
            score
            for score in scores
            if not any(
                "exceeds max travel distance" in item.lower()
                for item in score.missing_criteria
            )
        ]
        # Prefer higher score, then nearer sites, then travel evidence, then confidence.
        scores.sort(
            key=lambda score: (
                score.total,
                _nearest_site_sort_key(score),
                _travel_evidence_rank(score),
                score.confidence,
            ),
            reverse=True,
        )
        return scores[:limit]


def _nearest_site_sort_key(score: MatchScore) -> float:
    """Higher is better: nearer miles sort above farther / unknown distances."""
    if score.nearest_site_miles is None:
        return float("-inf")
    # Invert miles so reverse=True puts smaller distances first.
    return -score.nearest_site_miles


def _travel_evidence_rank(score: MatchScore) -> int:
    """Rank travel evidence so no-site unknowns sort below trials with known sites."""
    if any("Within max travel distance" in item for item in score.matched_criteria):
        return 3
    if any("exceeds max travel distance" in item.lower() for item in score.missing_criteria):
        return 2
    if any("Travel distance" in item for item in score.unknown_criteria):
        return 0
    return 1


def is_hard_excluded(user_profile: UserProfile, trial: ClinicalTrial) -> bool:
    """True when rule-based matching would assign a zero score (hard exclude)."""
    if _her2_positive_user_incompatible(user_profile, trial):
        return True

    structured = trial.structured_eligibility
    if structured is None:
        return False
    if _evaluate_age(user_profile, structured) == "exclude":
        return True
    return _evaluate_biomarkers(user_profile, structured) == "exclude"


def _her2_positive_user_incompatible(user: UserProfile, trial: ClinicalTrial) -> bool:
    if user.cancer_type != "HER2_POSITIVE_BREAST" and "her2-positive" not in _user_biomarkers(
        user
    ):
        return False

    if _text_indicates_her2_negative(trial.title):
        return True

    structured = trial.structured_eligibility
    if structured is None:
        return False

    if structured.diagnosis and _text_indicates_her2_negative(structured.diagnosis):
        # Allow mixed wording like "HER2-positive or HER2-negative".
        diagnosis = structured.diagnosis.lower()
        if "her2-positive" not in diagnosis and "her2+" not in diagnosis:
            return True

    return _evaluate_biomarkers(user, structured) == "exclude"


def _text_indicates_her2_negative(text: str) -> bool:
    return bool(_HER2_NEGATIVE_TITLE.search(text))


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
        # If the trial also lists HER2-positive, it may enroll either — do not hard exclude.
        if "her2-positive" not in trial_markers:
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
    if _text_indicates_her2_negative(diagnosis) and "her2-positive" not in diagnosis:
        return "unknown"
    if user.cancer_type == "HER2_POSITIVE_BREAST" and "her2" in diagnosis and "breast" in diagnosis:
        if "negative" in diagnosis and "positive" not in diagnosis:
            return "unknown"
        return "match"
    return "unknown"


def _evaluate_distance(
    user: UserProfile, trial: ClinicalTrial
) -> tuple[str, float | None]:
    if not user.postal_code:
        return "skip", None

    origin = get_zip_geocoder().geocode(user.postal_code)
    if origin is None:
        return "unknown", None

    site_coords = [
        (location.latitude, location.longitude)
        for location in trial.locations
        if location.latitude is not None and location.longitude is not None
    ]
    nearest = nearest_site_distance_miles(origin, site_coords)
    if nearest is None:
        return "no_sites", None
    if nearest <= user.max_travel_distance_miles:
        return "match", nearest
    return "missing", nearest


def _evaluate_prior_treatments(user: UserProfile, structured: StructuredEligibility) -> str:
    if not structured.prior_treatments:
        return "skip"
    if user.current_treatment in {CurrentTreatment.UNKNOWN, CurrentTreatment.OTHER}:
        return "unknown"
    if user.current_treatment == CurrentTreatment.NONE:
        return "missing"

    terms = TREATMENT_MATCH_TERMS.get(user.current_treatment, ())
    if not terms:
        return "unknown"

    for required in structured.prior_treatments:
        required_lower = required.lower()
        if any(term in required_lower for term in terms):
            return "match"
        # Also allow trial text to mention the enum value itself.
        if user.current_treatment.value.replace("_", " ") in required_lower:
            return "match"
    return "missing"


def _evaluate_ecog(user: UserProfile, structured: StructuredEligibility) -> str:
    if not structured.ecog:
        return "skip"
    if user.ecog is None:
        return "unknown"
    if int(user.ecog) in structured.ecog:
        return "match"
    return "missing"


def _evaluate_brain_metastasis(user: UserProfile, structured: StructuredEligibility) -> str:
    # structured.brain_metastasis False means the trial excludes active brain mets.
    if structured.brain_metastasis is None:
        return "skip"
    if user.brain_metastasis == BrainMetastasisStatus.UNKNOWN:
        return "unknown"
    if structured.brain_metastasis is False:
        if user.brain_metastasis == BrainMetastasisStatus.NO:
            return "match"
        return "missing"
    # structured.brain_metastasis True: trial allows/requires brain mets.
    if user.brain_metastasis == BrainMetastasisStatus.YES:
        return "match"
    return "missing"


def _weighted_total(factors: dict[str, float], *, missing_count: int = 0) -> float:
    """Score against the full factor set so sparse matches cannot become 100%."""
    if _TOTAL_WEIGHT == 0:
        return 0.0
    total = sum(
        factors.get(name, 0.0) * weight for name, weight in _FACTOR_WEIGHTS.items()
    ) / _TOTAL_WEIGHT
    if missing_count:
        total *= max(0.0, 1.0 - _MISSING_CRITERION_PENALTY * missing_count)
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
