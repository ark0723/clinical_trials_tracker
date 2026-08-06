"""SQLAlchemy ORM models for the ML/Data Layer's ingestion storage.

These mirror the Pydantic domain models in app/domain/clinical_trial.py but
are kept separate (Clean Code: persistence concerns should not leak into the
domain/API layer).
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
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
    structured_eligibility: Mapped["StructuredEligibilityModel | None"] = relationship(
        back_populates="trial",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
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


class StructuredEligibilityModel(Base):
    __tablename__ = "structured_eligibility"

    nct_id: Mapped[str] = mapped_column(
        ForeignKey("clinical_trials.nct_id", ondelete="CASCADE"),
        primary_key=True,
    )
    age_min: Mapped[int | None] = mapped_column(Integer, default=None)
    age_max: Mapped[int | None] = mapped_column(Integer, default=None)
    diagnosis: Mapped[str | None] = mapped_column(String(255), default=None)
    prior_treatments: Mapped[list[str]] = mapped_column(JSON, default=list)
    ecog: Mapped[list[int]] = mapped_column(JSON, default=list)
    biomarkers: Mapped[list[str]] = mapped_column(JSON, default=list)
    brain_metastasis: Mapped[bool | None] = mapped_column(default=None)
    extraction_confidence: Mapped[float] = mapped_column()
    extraction_method: Mapped[str] = mapped_column(String(20))

    trial: Mapped[ClinicalTrialModel] = relationship(back_populates="structured_eligibility")


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    encrypted_health_data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SavedTrialModel(Base):
    __tablename__ = "saved_trials"
    __table_args__ = (
        UniqueConstraint("user_id", "nct_id", name="uq_saved_trials_user_nct"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True
    )
    nct_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("clinical_trials.nct_id", ondelete="CASCADE"), index=True
    )
    status_at_save: Mapped[str] = mapped_column(String(30))
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PushSubscriptionModel(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
