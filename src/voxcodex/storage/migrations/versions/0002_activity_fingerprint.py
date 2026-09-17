"""add activity fingerprint for cache lookup

Revision ID: 0002_activity_fingerprint
Revises: 0001_m2_metadata
Create Date: 2026-09-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_activity_fingerprint"
down_revision: str | None = "0001_m2_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "processing_activities",
        sa.Column("activity_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_processing_activities_fingerprint",
        "processing_activities",
        ["activity_fingerprint"],
    )


def downgrade() -> None:
    op.drop_index("ix_processing_activities_fingerprint", table_name="processing_activities")
    op.drop_column("processing_activities", "activity_fingerprint")
