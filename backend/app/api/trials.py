from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.domain.clinical_trial import ClinicalTrial, TrialStatus
from app.infrastructure.models import ClinicalTrialModel

router = APIRouter(prefix="/api/trials", tags=["trials"])


@router.get("")
def list_trials(
    status: TrialStatus | None = None,
    db: Session = Depends(get_db_session),
) -> dict[str, list[ClinicalTrial]]:
    query = db.query(ClinicalTrialModel)
    if status is not None:
        query = query.filter(ClinicalTrialModel.status == status)

    trials = [ClinicalTrial.model_validate(model) for model in query.all()]
    return {"trials": trials}


@router.get("/{nct_id}")
def get_trial_detail(
    nct_id: str,
    db: Session = Depends(get_db_session),
) -> ClinicalTrial:
    model = db.get(ClinicalTrialModel, nct_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

    return ClinicalTrial.model_validate(model)
