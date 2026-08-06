"""Persist and list saved trials for a user."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.saved_trial import SavedTrial, SavedTrialCreate
from app.infrastructure.models import ClinicalTrialModel, SavedTrialModel


class SavedTrialError(Exception):
    def __init__(self, message: str, *, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def save_trial(db: Session, user_id: str, payload: SavedTrialCreate) -> SavedTrial:
    trial = db.get(ClinicalTrialModel, payload.nct_id)
    if trial is None:
        raise SavedTrialError(f"Trial {payload.nct_id} not found", status_code=404)

    existing = db.scalar(
        select(SavedTrialModel).where(
            SavedTrialModel.user_id == user_id,
            SavedTrialModel.nct_id == payload.nct_id,
        )
    )
    if existing is not None:
        return SavedTrial.model_validate(existing)

    model = SavedTrialModel(
        user_id=user_id,
        nct_id=payload.nct_id,
        status_at_save=str(trial.status.value if hasattr(trial.status, "value") else trial.status),
        saved_at=datetime.now(UTC),
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return SavedTrial.model_validate(model)


def list_saved_trials(db: Session, user_id: str) -> list[SavedTrial]:
    stmt = (
        select(SavedTrialModel)
        .where(SavedTrialModel.user_id == user_id)
        .order_by(SavedTrialModel.saved_at.desc())
    )
    return [SavedTrial.model_validate(row) for row in db.scalars(stmt).all()]


def unsave_trial(db: Session, user_id: str, nct_id: str) -> bool:
    model = db.scalar(
        select(SavedTrialModel).where(
            SavedTrialModel.user_id == user_id,
            SavedTrialModel.nct_id == nct_id,
        )
    )
    if model is None:
        return False
    db.delete(model)
    db.commit()
    return True
