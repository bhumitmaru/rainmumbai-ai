"""Add prediction source and backfill uniqueness.

Revision ID: 0002_prediction_source_backfill_unique
Revises: 0001_initial
Create Date: 2026-10-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_prediction_source_backfill_unique"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="live"),
    )
    op.create_index(op.f("ix_predictions_source"), "predictions", ["source"], unique=False)
    op.create_index(
        "uq_predictions_backfill_model_target",
        "predictions",
        ["model_version_id", "target_timestamp"],
        unique=True,
        sqlite_where=sa.text("source = 'backfill'"),
        postgresql_where=sa.text("source = 'backfill'"),
    )
    op.alter_column("predictions", "source", server_default=None)


def downgrade() -> None:
    op.drop_index("uq_predictions_backfill_model_target", table_name="predictions")
    op.drop_index(op.f("ix_predictions_source"), table_name="predictions")
    op.drop_column("predictions", "source")
