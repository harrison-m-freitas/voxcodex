from sqlalchemy import Column, ForeignKey, Index, Integer, MetaData, String, Table, Text

metadata = MetaData()

artifacts = Table(
    "artifacts",
    metadata,
    Column("id", String, primary_key=True),
    Column("digest", String(64), nullable=False),
    Column("kind", String, nullable=False),
    Index("ix_artifacts_digest", "digest"),
)

processing_activities = Table(
    "processing_activities",
    metadata,
    Column("id", String, primary_key=True),
    Column("type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("payload_json", Text, nullable=False),
)

derivations = Table(
    "derivations",
    metadata,
    Column("id", String, primary_key=True),
    Column("activity_ref", String, ForeignKey("processing_activities.id"), nullable=False),
    Column("derivation_kind", String, nullable=False),
    Column("confidence_ref", String, nullable=True),
)

derivation_inputs = Table(
    "derivation_inputs",
    metadata,
    Column("derivation_id", String, ForeignKey("derivations.id", ondelete="CASCADE"), primary_key=True),
    Column("artifact_ref", String, ForeignKey("artifacts.id"), primary_key=True),
    Index("ix_derivation_inputs_artifact_ref", "artifact_ref"),
)

derivation_outputs = Table(
    "derivation_outputs",
    metadata,
    Column("derivation_id", String, ForeignKey("derivations.id", ondelete="CASCADE"), primary_key=True),
    Column("artifact_ref", String, ForeignKey("artifacts.id"), primary_key=True),
    Index("ix_derivation_outputs_artifact_ref", "artifact_ref"),
)

usage_records = Table(
    "usage_records",
    metadata,
    Column("id", String, primary_key=True),
    Column("activity_ref", String, ForeignKey("processing_activities.id"), nullable=False),
    Column("payload_json", Text, nullable=False),
)
