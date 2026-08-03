"""Clinical trial domain models (Product Layer).

Schema follows docs/03-feature-spec.mdc section 3.3. Only the subset needed
for Week 2 (ingestion + trial search/detail) is included here;
StructuredEligibility, MatchScore, etc. are added in later weeks.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TrialPhase(StrEnum):
    PHASE_1 = "PHASE_1"
    PHASE_2 = "PHASE_2"
    PHASE_3 = "PHASE_3"
    PHASE_4 = "PHASE_4"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TrialStatus(StrEnum):
    RECRUITING = "RECRUITING"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    # Expanded-access ("compassionate use") statuses -- not part of the usual
    # recruiting lifecycle, but valid values per the ClinicalTrials.gov API v2
    # Status schema.
    AVAILABLE = "AVAILABLE"
    NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE"
    APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING"
    WITHHELD = "WITHHELD"
    UNKNOWN = "UNKNOWN"


class TrialLocation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    facility: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ClinicalTrial(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nct_id: str
    title: str
    phase: TrialPhase
    status: TrialStatus
    eligibility_criteria_raw: str
    eligibility_criteria_simplified: str | None = None
    enrollment_count: int | None = None
    has_results: bool = False
    locations: list[TrialLocation] = []
    last_updated: datetime


TrialChangeEventType = Literal[
    "status_changed",
    "enrollment_changed",
    "primary_outcome_updated",
    "results_posted",
    "protocol_amended",
]


class TrialChangeEvent(BaseModel):
    """Represents any tracked change to a trial over time (docs/03-feature-spec.mdc 3.3).

    Week 2 only produces status_changed / enrollment_changed / results_posted;
    the remaining event types require richer outcome data (Phase 2 / AACT).
    """

    nct_id: str
    event_type: TrialChangeEventType
    old_value: str | None
    new_value: str
    detected_at: datetime
