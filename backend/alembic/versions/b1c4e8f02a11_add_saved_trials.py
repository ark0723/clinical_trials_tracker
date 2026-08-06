"""Add saved_trials table for monitoring subscriptions."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c4e8f02a11"
down_revision: str | None = "a8f3c2b91d04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_trials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("nct_id", sa.String(length=20), nullable=False),
        sa.Column("status_at_save", sa.String(length=30), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["nct_id"], ["clinical_trials.nct_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "nct_id", name="uq_saved_trials_user_nct"),
    )
    op.create_index("ix_saved_trials_user_id", "saved_trials", ["user_id"])
    op.create_index("ix_saved_trials_nct_id", "saved_trials", ["nct_id"])


def downgrade() -> None:
    op.drop_index("ix_saved_trials_nct_id", table_name="saved_trials")
    op.drop_index("ix_saved_trials_user_id", table_name="saved_trials")
    op.drop_table("saved_trials")
