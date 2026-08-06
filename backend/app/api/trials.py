from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.domain.clinical_trial import ClinicalTrial, TrialChangeEvent, TrialStatus
from app.infrastructure.models import ClinicalTrialModel, TrialChangeEventModel

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


@router.get("/{nct_id}/history")
def get_trial_history(
    nct_id: str,
    db: Session = Depends(get_db_session),
) -> dict[str, list[TrialChangeEvent]]:
    if db.get(ClinicalTrialModel, nct_id) is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

    stmt = (
        select(TrialChangeEventModel)
        .where(TrialChangeEventModel.nct_id == nct_id)
        .order_by(TrialChangeEventModel.detected_at.desc())
    )
    events = [
        TrialChangeEvent(
            nct_id=row.nct_id,
            event_type=row.event_type,
            old_value=row.old_value,
            new_value=row.new_value,
            detected_at=row.detected_at,
        )
        for row in db.scalars(stmt).all()
    ]
    return {"events": events}


@router.get("/{nct_id}")
def get_trial_detail(
    nct_id: str,
    db: Session = Depends(get_db_session),
) -> ClinicalTrial:
    model = db.get(ClinicalTrialModel, nct_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

    return ClinicalTrial.model_validate(model)
