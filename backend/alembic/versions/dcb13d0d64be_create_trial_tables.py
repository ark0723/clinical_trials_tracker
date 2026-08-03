"""create trial tables

Revision ID: dcb13d0d64be
Revises:
Create Date: 2026-08-03 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.domain.clinical_trial import TrialPhase, TrialStatus

# revision identifiers, used by Alembic.
revision: str = "dcb13d0d64be"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinical_trials",
        sa.Column("nct_id", sa.String(length=20), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("phase", sa.Enum(TrialPhase, native_enum=False, length=20), nullable=False),
        sa.Column("status", sa.Enum(TrialStatus, native_enum=False, length=30), nullable=False),
        sa.Column("eligibility_criteria_raw", sa.Text(), nullable=False),
        sa.Column("eligibility_criteria_simplified", sa.Text(), nullable=True),
        sa.Column("enrollment_count", sa.Integer(), nullable=True),
        sa.Column("has_results", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "trial_locations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "nct_id",
            sa.String(length=20),
            sa.ForeignKey("clinical_trials.nct_id"),
            nullable=False,
        ),
        sa.Column("facility", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
    )

    op.create_table(
        "trial_change_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "nct_id",
            sa.String(length=20),
            sa.ForeignKey("clinical_trials.nct_id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trial_change_events")
    op.drop_table("trial_locations")
    op.drop_table("clinical_trials")
