from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.clinical_trial import TrialStatus
from app.domain.matching import MatchScore
from app.domain.trial_status_ux import PATIENT_DEFAULT_STATUSES
from app.services.matching_engine import MatchingEngine, RuleBasedMatchingStrategy
from app.services.profile_cipher import ProfileCipher
from app.services.trial_match_loader import fetch_candidate_trials
from app.services.user_profile_service import get_user_profile

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/{user_id}")
def get_matches_for_user(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    statuses: list[TrialStatus] | None = Query(
        default=None,
        description=(
            "ClinicalTrials.gov overallStatus values to include. "
            "Default: Recruiting + Not yet recruiting (Patient Mode)."
        ),
    ),
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> dict[str, list[MatchScore]]:
    profile = get_user_profile(db, cipher, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    status_set = frozenset(statuses) if statuses else PATIENT_DEFAULT_STATUSES
    # Lean candidates come from an in-process TTL cache; scoring is CPU-only.
    candidates = fetch_candidate_trials(db, profile, status_set)
    engine = MatchingEngine(RuleBasedMatchingStrategy())
    matches = engine.get_recommendations(profile, candidates, limit=limit)
    return {"matches": matches}
