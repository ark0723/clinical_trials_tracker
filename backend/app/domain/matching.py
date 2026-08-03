"""Matching result contracts (Product Layer)."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.clinical_trial import ClinicalTrial


class MatchScore(BaseModel):
    """Compatibility between a user profile and a trial, with transparent rationale."""

    model_config = ConfigDict(from_attributes=True)

    trial: ClinicalTrial
    total: float = Field(ge=0.0, le=1.0)
    factors: dict[str, float]
    matched_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    unknown_criteria: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
