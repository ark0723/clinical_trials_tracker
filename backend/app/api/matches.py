from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db_session, get_profile_cipher
from app.domain.clinical_trial import ClinicalTrial, TrialStatus
from app.domain.matching import MatchScore
from app.infrastructure.models import ClinicalTrialModel
from app.services.matching_engine import MatchingEngine, RuleBasedMatchingStrategy
from app.services.profile_cipher import ProfileCipher
from app.services.user_profile_service import get_user_profile

router = APIRouter(prefix="/api/matches", tags=["matches"])

_ACTIVE_STATUSES = {
    TrialStatus.RECRUITING,
    TrialStatus.NOT_YET_RECRUITING,
    TrialStatus.ENROLLING_BY_INVITATION,
}


@router.get("/{user_id}")
def get_matches_for_user(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db_session),
    cipher: ProfileCipher = Depends(get_profile_cipher),
) -> dict[str, list[MatchScore]]:
    profile = get_user_profile(db, cipher, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")

    models = (
        db.query(ClinicalTrialModel)
        .options(joinedload(ClinicalTrialModel.structured_eligibility))
        .filter(ClinicalTrialModel.status.in_(_ACTIVE_STATUSES))
        .all()
    )
    trials = [ClinicalTrial.model_validate(model) for model in models]

    engine = MatchingEngine(RuleBasedMatchingStrategy())
    matches = engine.get_recommendations(profile, trials, limit=limit)
    return {"matches": matches}
