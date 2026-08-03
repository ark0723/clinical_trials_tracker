"""SQLAlchemy ORM models for the ML/Data Layer's ingestion storage.

These mirror the Pydantic domain models in app/domain/clinical_trial.py but
are kept separate (Clean Code: persistence concerns should not leak into the
domain/API layer).
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.clinical_trial import TrialChangeEventType, TrialPhase, TrialStatus
from app.infrastructure.db import Base


class ClinicalTrialModel(Base):
    __tablename__ = "clinical_trials"

    nct_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    phase: Mapped[TrialPhase] = mapped_column(Enum(TrialPhase, native_enum=False, length=20))
    status: Mapped[TrialStatus] = mapped_column(Enum(TrialStatus, native_enum=False, length=30))
    eligibility_criteria_raw: Mapped[str] = mapped_column(Text)
    eligibility_criteria_simplified: Mapped[str | None] = mapped_column(Text, default=None)
    enrollment_count: Mapped[int | None] = mapped_column(Integer, default=None)
    has_results: Mapped[bool] = mapped_column(default=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    locations: Mapped[list["TrialLocationModel"]] = relationship(
        back_populates="trial", cascade="all, delete-orphan"
    )


class TrialLocationModel(Base):
    __tablename__ = "trial_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nct_id: Mapped[str] = mapped_column(ForeignKey("clinical_trials.nct_id"))
    facility: Mapped[str | None] = mapped_column(String(255), default=None)
    city: Mapped[str | None] = mapped_column(String(255), default=None)
    country: Mapped[str | None] = mapped_column(String(255), default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)

    trial: Mapped[ClinicalTrialModel] = relationship(back_populates="locations")


class TrialChangeEventModel(Base):
    __tablename__ = "trial_change_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nct_id: Mapped[str] = mapped_column(ForeignKey("clinical_trials.nct_id"))
    event_type: Mapped[TrialChangeEventType] = mapped_column(String(30))
    old_value: Mapped[str | None] = mapped_column(Text, default=None)
    new_value: Mapped[str] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
