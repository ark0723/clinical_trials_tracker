"""Load lean clinical-trial candidates for matching with an in-process TTL cache.

Neon round-trips dominate match latency when every request reloads ~500+ active
trials. Caching lean rows in memory makes subsequent match requests score-only.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.clinical_trial import ClinicalTrial, TrialLocation, TrialPhase, TrialStatus
from app.domain.eligibility import StructuredEligibility
from app.domain.trial_status_ux import PATIENT_DEFAULT_STATUSES
from app.domain.user_profile import UserProfile
from app.infrastructure.models import (
    ClinicalTrialModel,
    StructuredEligibilityModel,
    TrialLocationModel,
)
from app.services.matching_engine import is_hard_excluded

# Daily sync is the source of truth; a few minutes of staleness is acceptable for MVP.
_DEFAULT_TTL_SECONDS = 300.0


@dataclass
class _CacheEntry:
    trials: list[ClinicalTrial]
    statuses: frozenset[TrialStatus]
    loaded_at: float


_cache_lock = threading.Lock()
_cache_entry: _CacheEntry | None = None
_cache_ttl_seconds = _DEFAULT_TTL_SECONDS


def configure_candidate_cache(*, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
    global _cache_ttl_seconds
    _cache_ttl_seconds = ttl_seconds


def clear_candidate_cache() -> None:
    global _cache_entry
    with _cache_lock:
        _cache_entry = None


def load_match_trials(
    db: Session,
    statuses: frozenset[TrialStatus] | set[TrialStatus] | None = None,
) -> list[ClinicalTrial]:
    """Load scoring columns plus site coordinates (no raw eligibility text)."""
    status_filter = frozenset(statuses) if statuses is not None else PATIENT_DEFAULT_STATUSES
    trial = ClinicalTrialModel
    se = StructuredEligibilityModel

    stmt = (
        select(
            trial.nct_id,
            trial.title,
            trial.phase,
            trial.status,
            trial.eligibility_criteria_simplified,
            trial.last_updated,
            se.age_min,
            se.age_max,
            se.diagnosis,
            se.prior_treatments,
            se.ecog,
            se.biomarkers,
            se.brain_metastasis,
            se.extraction_confidence,
            se.extraction_method,
        )
        .outerjoin(se, trial.nct_id == se.nct_id)
        .where(trial.status.in_(status_filter))
    )
    rows = db.execute(stmt).all()
    nct_ids = [row.nct_id for row in rows]
    locations_by_nct = _load_location_coords(db, nct_ids)
    return [_row_to_matching_trial(row, locations_by_nct.get(row.nct_id, [])) for row in rows]


def load_active_match_trials(db: Session) -> list[ClinicalTrial]:
    """Backward-compatible alias for patient-default status candidates."""
    return load_match_trials(db, PATIENT_DEFAULT_STATUSES)


def get_cached_match_trials(
    db: Session,
    statuses: frozenset[TrialStatus] | set[TrialStatus] | None = None,
) -> list[ClinicalTrial]:
    """Return lean trials for the status set, refreshing cache when stale."""
    global _cache_entry
    status_key = frozenset(statuses) if statuses is not None else PATIENT_DEFAULT_STATUSES
    now = time.monotonic()

    with _cache_lock:
        if (
            _cache_entry is not None
            and _cache_entry.statuses == status_key
            and (now - _cache_entry.loaded_at) < _cache_ttl_seconds
        ):
            return _cache_entry.trials

    trials = load_match_trials(db, status_key)

    with _cache_lock:
        _cache_entry = _CacheEntry(
            trials=trials,
            statuses=status_key,
            loaded_at=time.monotonic(),
        )
        return _cache_entry.trials


def get_cached_active_match_trials(db: Session) -> list[ClinicalTrial]:
    """Backward-compatible alias for patient-default cached candidates."""
    return get_cached_match_trials(db, PATIENT_DEFAULT_STATUSES)


def fetch_candidate_trials(
    db: Session,
    user_profile: UserProfile,
    statuses: frozenset[TrialStatus] | set[TrialStatus] | None = None,
) -> list[ClinicalTrial]:
    """Return cached trials for statuses that are not hard-excluded for this profile."""
    trials = get_cached_match_trials(db, statuses)
    return [trial for trial in trials if not is_hard_excluded(user_profile, trial)]


def fetch_trials_by_nct_ids(
    db: Session, nct_ids: list[str]
) -> dict[str, ClinicalTrial]:
    """Load full trial payloads (including locations) when a detail view needs them."""
    if not nct_ids:
        return {}

    from sqlalchemy.orm import joinedload

    stmt = (
        select(ClinicalTrialModel)
        .where(ClinicalTrialModel.nct_id.in_(nct_ids))
        .options(
            joinedload(ClinicalTrialModel.structured_eligibility),
            joinedload(ClinicalTrialModel.locations),
        )
    )
    models = db.scalars(stmt).unique().all()
    return {model.nct_id: ClinicalTrial.model_validate(model) for model in models}


def _load_location_coords(
    db: Session, nct_ids: list[str]
) -> dict[str, list[TrialLocation]]:
    if not nct_ids:
        return {}

    stmt = select(
        TrialLocationModel.nct_id,
        TrialLocationModel.latitude,
        TrialLocationModel.longitude,
        TrialLocationModel.city,
        TrialLocationModel.country,
        TrialLocationModel.facility,
    ).where(
        TrialLocationModel.nct_id.in_(nct_ids),
        TrialLocationModel.latitude.isnot(None),
        TrialLocationModel.longitude.isnot(None),
    )
    by_nct: dict[str, list[TrialLocation]] = defaultdict(list)
    for row in db.execute(stmt).all():
        by_nct[row.nct_id].append(
            TrialLocation(
                facility=row.facility,
                city=row.city,
                country=row.country,
                latitude=row.latitude,
                longitude=row.longitude,
            )
        )
    return by_nct


def _row_to_matching_trial(
    row, locations: list[TrialLocation] | None = None
) -> ClinicalTrial:
    structured = None
    if row.extraction_method is not None:
        structured = StructuredEligibility(
            age_min=row.age_min,
            age_max=row.age_max,
            diagnosis=row.diagnosis,
            prior_treatments=list(row.prior_treatments or []),
            ecog=list(row.ecog or []),
            biomarkers=list(row.biomarkers or []),
            brain_metastasis=row.brain_metastasis,
            extraction_confidence=float(row.extraction_confidence or 0.0),
            extraction_method=row.extraction_method,
        )

    return ClinicalTrial(
        nct_id=row.nct_id,
        title=row.title,
        phase=TrialPhase(row.phase) if not isinstance(row.phase, TrialPhase) else row.phase,
        status=TrialStatus(row.status) if not isinstance(row.status, TrialStatus) else row.status,
        eligibility_criteria_raw="",
        eligibility_criteria_simplified=row.eligibility_criteria_simplified,
        enrollment_count=None,
        has_results=False,
        locations=list(locations or []),
        structured_eligibility=structured,
        last_updated=row.last_updated,
    )
