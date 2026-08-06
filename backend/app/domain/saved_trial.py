"""Saved-trial subscriptions for monitoring (Patient Journey Platform)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SavedTrialCreate(BaseModel):
    nct_id: str = Field(min_length=5, max_length=20)


class SavedTrial(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    nct_id: str
    status_at_save: str
    saved_at: datetime
