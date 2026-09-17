from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, func, select

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceSnapshot
from voxcodex.domain.reconstruction import (
    OpenStructuralState,
    ReconstructionContext,
    ReconstructionUnit,
    StageResult,
)
from voxcodex.reconstruction.engine import ReconstructionEngine
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import derivations, metadata, processing_activities


class AppendUnitStage:
    def __init__(self, name: str, unit_id: str) -> None:
        self.name = name
        self.version = "0.1.0"
        self.unit_id = unit_id

    def run(
        self,
        context: ReconstructionContext,
        units: tuple[ReconstructionUnit, ...],
    ) -> StageResult:
        next_unit = ReconstructionUnit(
            id=self.unit_id,
            reconstruction_snapshot_ref=context.snapshot_ref,
            parent_ref=None,
            order_key=f"{len(units):06d}",
            reconstruction_class="block_candidate",
            evidence_refs=context.source_evidence_refs,
            properties={"stage": self.name},
            provenance_ref=f"pending:{self.name}",
        )
        return StageResult(
            units=(*units, next_unit),
            issues=(),
            open_state=OpenStructuralState(),
        )


def _evidence_snapshot() -> EvidenceSnapshot:
    return EvidenceSnapshot(
        id="snapshot:evidence:test",
        source_artifact_ref="source:test",
        extraction_activity_ref="activity:extract:test",
        extraction_profile_ref="extraction-profile:test",
        partition_refs=(),
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
        snapshot_digest="e" * 64,
    )


def _engine(tmp_path: Path) -> tuple[ReconstructionEngine, MetadataStore]:
    sql_engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    metadata.create_all(sql_engine)
    metadata_store = MetadataStore(sql_engine)
    engine = ReconstructionEngine(
        stages=(
            AppendUnitStage("r0-normalize", "reconstruction-unit:r0"),
            AppendUnitStage("r1-group", "reconstruction-unit:r1"),
        ),
        blob_store=LocalBlobStore(tmp_path / "blobs"),
        metadata_store=metadata_store,
        now=lambda: datetime(2026, 9, 16, tzinfo=UTC),
    )
    return engine, metadata_store


def test_engine_executes_configured_stages_and_records_activity_and_derivation(tmp_path: Path):
    engine, metadata_store = _engine(tmp_path)
    evidence = _evidence_snapshot()

    result = engine.run(evidence, reconstruction_profile_ref="reconstruction-profile:test")

    assert tuple(unit.id for unit in result.units) == (
        "reconstruction-unit:r0",
        "reconstruction-unit:r1",
    )
    evidence_ref = ArtifactRef(
        id=evidence.id,
        digest=evidence.snapshot_digest,
        kind="evidence_snapshot",
    )
    downstream = metadata_store.get_downstream(evidence_ref)
    assert len(downstream) == 2
    assert {ref.kind for ref in downstream} == {"reconstruction_stage_output"}

    with metadata_store.engine.connect() as connection:
        activity_count = connection.scalar(select(func.count()).select_from(processing_activities))
        derivation_count = connection.scalar(select(func.count()).select_from(derivations))
    assert activity_count == 2
    assert derivation_count == 2


def test_engine_does_not_mutate_evidence_snapshot(tmp_path: Path):
    engine, _metadata_store = _engine(tmp_path)
    evidence = _evidence_snapshot()
    before = evidence.model_dump_json()

    engine.run(evidence, reconstruction_profile_ref="reconstruction-profile:test")

    assert evidence.model_dump_json() == before
