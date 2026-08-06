"""Patient profile contracts for the US-market MVP."""

from enum import IntEnum, StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CancerStage(StrEnum):
    STAGE_I = "I"
    STAGE_II = "II"
    STAGE_III = "III"
    STAGE_IV = "IV"


class NotificationChannel(StrEnum):
    BROWSER = "browser"
    EMAIL = "email"
    TELEGRAM = "telegram"


class CurrentTreatment(StrEnum):
    """Common HER2+ breast cancer treatments for structured matching."""

    TRASTUZUMAB = "trastuzumab"
    PERTUZUMAB = "pertuzumab"
    TRASTUZUMAB_EMTANSINE = "trastuzumab_emtansine"
    TRASTUZUMAB_DERUXTECAN = "trastuzumab_deruxtecan"
    TUCATINIB = "tucatinib"
    NERATINIB = "neratinib"
    LAPATINIB = "lapatinib"
    CHEMOTHERAPY = "chemotherapy"
    ENDOCRINE_THERAPY = "endocrine_therapy"
    NONE = "none"
    OTHER = "other"
    UNKNOWN = "unknown"


class BrainMetastasisStatus(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class EcogStatus(IntEnum):
    """ECOG performance status (0–4). Use profile field None for 'I don't know'."""

    FULLY_ACTIVE = 0
    RESTRICTED = 1
    AMBULATORY = 2
    LIMITED = 3
    DISABLED = 4


_TREATMENT_ALIASES: dict[str, CurrentTreatment] = {
    "trastuzumab": CurrentTreatment.TRASTUZUMAB,
    "herceptin": CurrentTreatment.TRASTUZUMAB,
    "pertuzumab": CurrentTreatment.PERTUZUMAB,
    "perjeta": CurrentTreatment.PERTUZUMAB,
    "trastuzumab emtansine": CurrentTreatment.TRASTUZUMAB_EMTANSINE,
    "trastuzumab_emtansine": CurrentTreatment.TRASTUZUMAB_EMTANSINE,
    "t-dm1": CurrentTreatment.TRASTUZUMAB_EMTANSINE,
    "kadcyla": CurrentTreatment.TRASTUZUMAB_EMTANSINE,
    "trastuzumab deruxtecan": CurrentTreatment.TRASTUZUMAB_DERUXTECAN,
    "trastuzumab_deruxtecan": CurrentTreatment.TRASTUZUMAB_DERUXTECAN,
    "t-dxd": CurrentTreatment.TRASTUZUMAB_DERUXTECAN,
    "enhertu": CurrentTreatment.TRASTUZUMAB_DERUXTECAN,
    "tucatinib": CurrentTreatment.TUCATINIB,
    "tukysa": CurrentTreatment.TUCATINIB,
    "neratinib": CurrentTreatment.NERATINIB,
    "nerlynx": CurrentTreatment.NERATINIB,
    "lapatinib": CurrentTreatment.LAPATINIB,
    "tykerb": CurrentTreatment.LAPATINIB,
    "chemotherapy": CurrentTreatment.CHEMOTHERAPY,
    "chemo": CurrentTreatment.CHEMOTHERAPY,
    "endocrine therapy": CurrentTreatment.ENDOCRINE_THERAPY,
    "endocrine_therapy": CurrentTreatment.ENDOCRINE_THERAPY,
    "none": CurrentTreatment.NONE,
    "not currently on treatment": CurrentTreatment.NONE,
    "other": CurrentTreatment.OTHER,
    "unknown": CurrentTreatment.UNKNOWN,
    "i don't know": CurrentTreatment.UNKNOWN,
    "i do not know": CurrentTreatment.UNKNOWN,
}


def normalize_current_treatment(value: object) -> CurrentTreatment:
    if value is None or value == "":
        return CurrentTreatment.UNKNOWN
    if isinstance(value, CurrentTreatment):
        return value
    text = str(value).strip().lower()
    if text in _TREATMENT_ALIASES:
        return _TREATMENT_ALIASES[text]
    # Prefer longer aliases so "trastuzumab deruxtecan" wins over "trastuzumab".
    for alias, treatment in sorted(
        _TREATMENT_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if alias in text:
            return treatment
    return CurrentTreatment.OTHER


class UserProfileCreate(BaseModel):
    age: int = Field(ge=18, le=120)
    cancer_type: Literal["HER2_POSITIVE_BREAST"] = "HER2_POSITIVE_BREAST"
    stage: CancerStage
    biomarkers: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1,
        max_length=20,
    )
    current_treatment: CurrentTreatment = CurrentTreatment.UNKNOWN
    postal_code: str | None = Field(default=None, max_length=20)
    ecog: EcogStatus | None = None
    brain_metastasis: BrainMetastasisStatus = BrainMetastasisStatus.UNKNOWN
    # Miles to match US audience + ClinicalTrials.gov filter.geo examples (e.g. 50mi).
    max_travel_distance_miles: int = Field(ge=0, le=10_000, default=50)
    notification_channels: list[NotificationChannel] = Field(min_length=1, max_length=3)

    @field_validator("current_treatment", mode="before")
    @classmethod
    def _coerce_current_treatment(cls, value: object) -> CurrentTreatment:
        return normalize_current_treatment(value)

    @field_validator("postal_code", mode="before")
    @classmethod
    def _blank_postal_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("ecog", mode="before")
    @classmethod
    def _coerce_ecog(cls, value: object) -> EcogStatus | None:
        if value is None or value == "" or value == "unknown":
            return None
        return EcogStatus(int(value))

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_travel_km(cls, value: object) -> object:
        """Accept older encrypted profiles that stored max_travel_distance_km."""
        if not isinstance(value, dict):
            return value
        if "max_travel_distance_miles" in value:
            return value
        km = value.get("max_travel_distance_km")
        if km is None:
            return value
        migrated = dict(value)
        migrated["max_travel_distance_miles"] = round(float(km) * 0.621371)
        migrated.pop("max_travel_distance_km", None)
        return migrated


class UserProfile(UserProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


# Search terms used when matching profile treatment against trial prior_treatments.
TREATMENT_MATCH_TERMS: dict[CurrentTreatment, tuple[str, ...]] = {
    CurrentTreatment.TRASTUZUMAB: ("trastuzumab", "herceptin"),
    CurrentTreatment.PERTUZUMAB: ("pertuzumab", "perjeta"),
    CurrentTreatment.TRASTUZUMAB_EMTANSINE: (
        "trastuzumab emtansine",
        "t-dm1",
        "tdm1",
        "kadcyla",
    ),
    CurrentTreatment.TRASTUZUMAB_DERUXTECAN: (
        "trastuzumab deruxtecan",
        "t-dxd",
        "tdxd",
        "enhertu",
    ),
    CurrentTreatment.TUCATINIB: ("tucatinib", "tukysa"),
    CurrentTreatment.NERATINIB: ("neratinib", "nerlynx"),
    CurrentTreatment.LAPATINIB: ("lapatinib", "tykerb"),
    CurrentTreatment.CHEMOTHERAPY: ("chemotherapy", "chemo", "taxane", "docetaxel", "paclitaxel"),
    CurrentTreatment.ENDOCRINE_THERAPY: (
        "endocrine",
        "hormone therapy",
        "letrozole",
        "anastrozole",
        "fulvestrant",
    ),
    CurrentTreatment.NONE: (),
    CurrentTreatment.OTHER: (),
    CurrentTreatment.UNKNOWN: (),
}
