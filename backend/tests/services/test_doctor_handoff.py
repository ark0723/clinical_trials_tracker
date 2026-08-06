from datetime import UTC, datetime

from app.domain.clinical_trial import ClinicalTrial, TrialPhase, TrialStatus
from app.domain.matching import MatchScore
from app.services.doctor_handoff import attach_doctor_handoff


def _score(**overrides) -> MatchScore:
    trial = ClinicalTrial(
        nct_id="NCT1",
        title="Study",
        phase=TrialPhase.PHASE_2,
        status=TrialStatus.RECRUITING,
        eligibility_criteria_raw="raw",
        eligibility_criteria_simplified="Adults with HER2-positive breast cancer.",
        last_updated=datetime(2026, 1, 1, tzinfo=UTC),
    )
    base = dict(
        trial=trial,
        total=0.7,
        factors={"age": 1.0},
        matched_criteria=["Age within eligible range"],
        missing_criteria=[],
        unknown_criteria=["ECOG performance status: unable to verify"],
        confidence=0.5,
        rationale="Matched age.",
    )
    base.update(overrides)
    return MatchScore(**base)


def test_attach_doctor_handoff_maps_unknowns_to_confirm_and_questions():
    enriched = attach_doctor_handoff(_score())

    assert enriched.things_to_confirm == [
        "ECOG performance status: unable to verify"
    ]
    assert any("ECOG" in q for q in enriched.questions_for_doctor)
    assert len(enriched.questions_for_doctor) >= 1


def test_attach_doctor_handoff_adds_questions_for_missing_criteria():
    enriched = attach_doctor_handoff(
        _score(
            unknown_criteria=[],
            missing_criteria=["Required prior treatment"],
        )
    )

    assert "Required prior treatment" in enriched.things_to_confirm
    assert any("prior" in q.lower() for q in enriched.questions_for_doctor)
