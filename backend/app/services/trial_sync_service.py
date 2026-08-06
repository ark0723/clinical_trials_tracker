"""ML/Data Layer ingestion: fetches trials from ClinicalTrials.gov and detects changes.

See docs/03-feature-spec.mdc "기능 2: 임상시험 데이터 수집 및 조회".
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.domain.clinical_trial import ClinicalTrial, TrialChangeEvent
from app.domain.eligibility import StructuredEligibility
from app.infrastructure.ctgov_mapper import map_study_to_trial
from app.infrastructure.models import (
    ClinicalTrialModel,
    StructuredEligibilityModel,
    TrialChangeEventModel,
    TrialLocationModel,
)
from app.services.eligibility_extractor import (
    EligibilityExtractor,
    RuleBasedEligibilityExtractor,
)
from app.services.eligibility_summarizer import RuleBasedEligibilitySummarizer


class TrialSource(Protocol):
    """Anything that can list raw ClinicalTrials.gov studies (see ClinicalTrialsGovClient)."""

    def search_studies(
        self, condition: str, statuses: list[str] | None = None
    ) -> Any: ...


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    events: list[TrialChangeEvent] = field(default_factory=list)


def detect_changes(
    existing: ClinicalTrialModel, incoming: ClinicalTrial, detected_at: datetime | None = None
) -> list[TrialChangeEvent]:
    """Compare a stored trial snapshot against a freshly-fetched one.

    Only the change types that can be derived from the ClinicalTrials.gov API v2
    response are covered in Week 2 (status/enrollment/results). primary_outcome_updated
    and protocol_amended need richer data and are deferred to Phase 2 (see plan).
    """
    detected_at = detected_at or datetime.now(UTC)
    events: list[TrialChangeEvent] = []

    if existing.status != incoming.status:
        events.append(
            TrialChangeEvent(
                nct_id=incoming.nct_id,
                event_type="status_changed",
                old_value=existing.status.value,
                new_value=incoming.status.value,
                detected_at=detected_at,
            )
        )

    if existing.enrollment_count != incoming.enrollment_count:
        events.append(
            TrialChangeEvent(
                nct_id=incoming.nct_id,
                event_type="enrollment_changed",
                old_value=str(existing.enrollment_count)
                if existing.enrollment_count is not None
                else None,
                new_value=str(incoming.enrollment_count),
                detected_at=detected_at,
            )
        )

    if not existing.has_results and incoming.has_results:
        events.append(
            TrialChangeEvent(
                nct_id=incoming.nct_id,
                event_type="results_posted",
                old_value="false",
                new_value="true",
                detected_at=detected_at,
            )
        )

    return events


def _apply_trial_fields(model: ClinicalTrialModel, trial: ClinicalTrial) -> None:
    model.title = trial.title
    model.phase = trial.phase
    model.status = trial.status
    model.eligibility_criteria_raw = trial.eligibility_criteria_raw
    model.eligibility_criteria_simplified = trial.eligibility_criteria_simplified
    model.enrollment_count = trial.enrollment_count
    model.has_results = trial.has_results
    model.last_updated = trial.last_updated
    model.locations = [
        TrialLocationModel(
            facility=location.facility,
            city=location.city,
            country=location.country,
            latitude=location.latitude,
            longitude=location.longitude,
        )
        for location in trial.locations
    ]


def _upsert_structured_eligibility(
    db: Session,
    nct_id: str,
    structured: StructuredEligibility,
) -> None:
    model = db.get(StructuredEligibilityModel, nct_id)
    if model is None:
        model = StructuredEligibilityModel(nct_id=nct_id)
        db.add(model)

    model.age_min = structured.age_min
    model.age_max = structured.age_max
    model.diagnosis = structured.diagnosis
    model.prior_treatments = list(structured.prior_treatments)
    model.ecog = list(structured.ecog)
    model.biomarkers = list(structured.biomarkers)
    model.brain_metastasis = structured.brain_metastasis
    model.extraction_confidence = structured.extraction_confidence
    model.extraction_method = structured.extraction_method


def sync_clinical_trials(
    db: Session,
    client: TrialSource,
    condition: str,
    statuses: list[str] | None = None,
    extractor: EligibilityExtractor | None = None,
) -> SyncResult:
    """Fetch and persist trials one at a time, committing after each.

    Committing per-trial (instead of once at the end) means a transient
    failure partway through the daily batch (e.g. ClinicalTrials.gov rate
    limiting, see plan's "incremental-commit" decision) does not discard
    already-synced trials -- the next run simply resumes from where it left
    off, since new/updated trials are looked up by nct_id.

    After mapping each study, a rule-based extractor (MVP: no LLM) fills
    StructuredEligibility and a deterministic plain-English summary.
    """
    result = SyncResult()
    extractor = extractor or RuleBasedEligibilityExtractor()
    summarizer = RuleBasedEligibilitySummarizer()

    for raw_study in client.search_studies(condition=condition, statuses=statuses):
        incoming = map_study_to_trial(raw_study)
        structured = extractor.extract(incoming.eligibility_criteria_raw)
        incoming.eligibility_criteria_simplified = summarizer.summarize(structured)
        incoming.structured_eligibility = structured

        existing = db.get(ClinicalTrialModel, incoming.nct_id)

        if existing is None:
            model = ClinicalTrialModel(nct_id=incoming.nct_id)
            _apply_trial_fields(model, incoming)
            db.add(model)
            result.created += 1
        else:
            events = detect_changes(existing, incoming)
            _apply_trial_fields(existing, incoming)
            result.updated += 1

            for event in events:
                db.add(
                    TrialChangeEventModel(
                        nct_id=event.nct_id,
                        event_type=event.event_type,
                        old_value=event.old_value,
                        new_value=event.new_value,
                        detected_at=event.detected_at,
                    )
                )
            result.events.extend(events)

        _upsert_structured_eligibility(db, incoming.nct_id, structured)
        db.commit()

    # Matching API keeps an in-process lean-trial cache; invalidate after sync.
    from app.services.trial_match_loader import clear_candidate_cache

    clear_candidate_cache()

    if result.events:
        _maybe_notify_saved_trial_changes(db, result.events)

    return result


def _maybe_notify_saved_trial_changes(db: Session, events: list) -> None:
    """Best-effort browser push for users watching changed trials."""
    from app.core.config import settings
    from app.services.change_notifier import notify_saved_trial_changes
    from app.services.notifications.factory import build_notification_service
    from app.services.profile_cipher import ProfileCipher

    if not settings.profile_encryption_key or not settings.vapid_private_key:
        return
    try:
        cipher = ProfileCipher(settings.profile_encryption_key)
        notify_saved_trial_changes(
            db, cipher, events, build_notification_service()
        )
    except Exception:
        # Sync must succeed even if notifications fail.
        import logging

        logging.getLogger(__name__).exception(
            "Saved-trial change notifications failed after sync"
        )
