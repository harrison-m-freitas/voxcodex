"""create m2 metadata tables

Revision ID: 0001_m2_metadata
Revises:
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_m2_metadata"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
    )
    op.create_index("ix_artifacts_digest", "artifacts", ["digest"])
    op.create_table(
        "processing_activities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )
    op.create_table(
        "derivations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("activity_ref", sa.String(), sa.ForeignKey("processing_activities.id"), nullable=False),
        sa.Column("derivation_kind", sa.String(), nullable=False),
        sa.Column("confidence_ref", sa.String(), nullable=True),
    )
    op.create_table(
        "derivation_inputs",
        sa.Column("derivation_id", sa.String(), sa.ForeignKey("derivations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("artifact_ref", sa.String(), sa.ForeignKey("artifacts.id"), primary_key=True),
    )
    op.create_index("ix_derivation_inputs_artifact_ref", "derivation_inputs", ["artifact_ref"])
    op.create_table(
        "derivation_outputs",
        sa.Column("derivation_id", sa.String(), sa.ForeignKey("derivations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("artifact_ref", sa.String(), sa.ForeignKey("artifacts.id"), primary_key=True),
    )
    op.create_index("ix_derivation_outputs_artifact_ref", "derivation_outputs", ["artifact_ref"])
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("activity_ref", sa.String(), sa.ForeignKey("processing_activities.id"), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("usage_records")
    op.drop_index("ix_derivation_outputs_artifact_ref", table_name="derivation_outputs")
    op.drop_table("derivation_outputs")
    op.drop_index("ix_derivation_inputs_artifact_ref", table_name="derivation_inputs")
    op.drop_table("derivation_inputs")
    op.drop_table("derivations")
    op.drop_table("processing_activities")
    op.drop_index("ix_artifacts_digest", table_name="artifacts")
    op.drop_table("artifacts")
