"""Structured eligibility domain models used by the ML/Data Layer."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StructuredEligibility(BaseModel):
    """Rule-extracted facts from a trial's free-text eligibility criteria.

    Fields are optional because ClinicalTrials.gov criteria are inconsistent
    and partial extraction is preferable to rejecting the source text.
    """

    model_config = ConfigDict(from_attributes=True)

    age_min: int | None = Field(default=None, ge=0, le=120)
    age_max: int | None = Field(default=None, ge=0, le=120)
    diagnosis: str | None = None
    prior_treatments: list[str] = Field(default_factory=list)
    ecog: list[int] = Field(default_factory=list)
    biomarkers: list[str] = Field(default_factory=list)
    brain_metastasis: bool | None = None
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: Literal["rule", "llm", "hybrid"]
