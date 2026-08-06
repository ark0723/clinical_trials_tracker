"""Map match gaps into patient-friendly doctor-handoff prompts (no treatment advice)."""

from __future__ import annotations

from app.domain.matching import MatchScore

_UNKNOWN_QUESTIONS: list[tuple[str, str]] = [
    ("ecog", "What is my current ECOG performance status?"),
    ("brain", "Do I have brain metastases, and are they treated and stable?"),
    ("prior treatment", "Which cancer treatments have I already received?"),
    ("biomarker", "Can we confirm my HER2 and other biomarker results from pathology?"),
    ("diagnosis", "Does my diagnosis wording match this trial's inclusion criteria?"),
    ("age", "Is my age within the range this trial lists?"),
    ("travel", "Is traveling to one of the listed sites realistic for me?"),
    ("structured eligibility", "Can we review the full eligibility criteria together?"),
]

_MISSING_QUESTIONS: list[tuple[str, str]] = [
    ("prior treatment", "Have I completed the prior therapies this trial requires?"),
    ("ecog", "Does my ECOG status meet this trial's requirement?"),
    ("brain", "Does my brain metastasis status meet this trial's criteria?"),
    ("travel", "Can I travel to a nearer site, or should we widen search distance?"),
    ("age", "Am I outside the age range, or is the listing outdated?"),
    ("biomarker", "Do my biomarkers conflict with this trial's requirements?"),
]

_DEFAULT_QUESTION = (
    "What else should we confirm before deciding whether to discuss this trial?"
)


def attach_doctor_handoff(score: MatchScore) -> MatchScore:
    """Enrich a MatchScore with things_to_confirm and questions_for_doctor."""
    things = list(dict.fromkeys([*score.unknown_criteria, *score.missing_criteria]))
    questions: list[str] = []
    for item in score.unknown_criteria:
        questions.append(_question_for(item, _UNKNOWN_QUESTIONS))
    for item in score.missing_criteria:
        questions.append(_question_for(item, _MISSING_QUESTIONS))
    if not questions:
        questions.append(_DEFAULT_QUESTION)
    # Deduplicate while preserving order
    questions = list(dict.fromkeys(questions))
    return score.model_copy(
        update={
            "things_to_confirm": things,
            "questions_for_doctor": questions,
        }
    )


def _question_for(item: str, table: list[tuple[str, str]]) -> str:
    lowered = item.lower()
    for needle, question in table:
        if needle in lowered:
            return question
    return _DEFAULT_QUESTION
