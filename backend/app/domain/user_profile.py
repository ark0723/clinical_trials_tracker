"""Patient profile contracts for the US-market MVP."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class CancerStage(StrEnum):
    STAGE_I = "I"
    STAGE_II = "II"
    STAGE_III = "III"
    STAGE_IV = "IV"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    TELEGRAM = "telegram"


class UserProfileCreate(BaseModel):
    age: int = Field(ge=18, le=120)
    cancer_type: Literal["HER2_POSITIVE_BREAST"] = "HER2_POSITIVE_BREAST"
    stage: CancerStage
    biomarkers: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1,
        max_length=20,
    )
    current_treatment: str | None = Field(default=None, max_length=500)
    max_travel_distance_km: int = Field(ge=0, le=10_000)
    notification_channels: list[NotificationChannel] = Field(min_length=1, max_length=2)


class UserProfile(UserProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
