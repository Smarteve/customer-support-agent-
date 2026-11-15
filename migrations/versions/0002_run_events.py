"""Save worker progress for each run."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_run_events"
down_revision = "0001_events_runs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "run_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "run_id", sa.Uuid(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("details", postgresql.JSONB(), server_default="{}", nullable=False),
    )
    op.create_index("ix_run_events_run_id_id", "run_events", ["run_id", "id"])


def downgrade():
    op.drop_index("ix_run_events_run_id_id", table_name="run_events")
    op.drop_table("run_events")
