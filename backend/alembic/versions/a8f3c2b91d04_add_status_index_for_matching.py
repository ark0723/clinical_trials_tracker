"""Add index on clinical_trials.status for active-trial matching queries."""

from collections.abc import Sequence

from alembic import op

revision: str = "a8f3c2b91d04"
down_revision: str | None = "4e9c7a1d2b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_clinical_trials_status", "clinical_trials", ["status"])


def downgrade() -> None:
    op.drop_index("ix_clinical_trials_status", table_name="clinical_trials")
