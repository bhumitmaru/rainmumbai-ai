"""Initial schema (D1 users, D3 meteo, D4 predictions/outcomes, D5 metadata).

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-05

The schema is created directly from the SQLAlchemy models so the migration can
never drift from the ORM definitions. Payments/subscriptions (D2) are
intentionally absent: the product is free.
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.db.models import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db.models import Base

    Base.metadata.drop_all(bind=op.get_bind())
