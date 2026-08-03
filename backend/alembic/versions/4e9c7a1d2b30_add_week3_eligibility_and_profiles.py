"""add Week 3 eligibility and profile tables

Revision ID: 4e9c7a1d2b30
Revises: dcb13d0d64be
Create Date: 2026-08-03 13:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4e9c7a1d2b30"
down_revision: str | None = "dcb13d0d64be"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "structured_eligibility",
        sa.Column(
            "nct_id",
            sa.String(length=20),
            sa.ForeignKey("clinical_trials.nct_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("diagnosis", sa.String(length=255), nullable=True),
        sa.Column("prior_treatments", sa.JSON(), nullable=False),
        sa.Column("ecog", sa.JSON(), nullable=False),
        sa.Column("biomarkers", sa.JSON(), nullable=False),
        sa.Column("brain_metastasis", sa.Boolean(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=False),
        sa.Column("extraction_method", sa.String(length=20), nullable=False),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("encrypted_health_data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_table("structured_eligibility")
