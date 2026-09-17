from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceSnapshot
from voxcodex.domain.reconstruction import (
    OpenStructuralState,
    ReconstructionContext,
    ReconstructionIssue,
    ReconstructionUnit,
    StageResult,
)
from voxcodex.reconstruction.engine import ReconstructionEngine
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


class AmbiguousAssemblyStage:
    name = "r7-assembly-fixture"
    version = "0.1.0"

    def __init__(self, evidence_refs: tuple[ArtifactRef, ...]) -> None:
        self.evidence_refs = evidence_refs

    def run(
        self,
        context: ReconstructionContext,
        units: tuple[ReconstructionUnit, ...],
    ) -> StageResult:
        root = ReconstructionUnit(
            id="reconstruction-unit:document",
            reconstruction_snapshot_ref=context.snapshot_ref,
            parent_ref=None,
            order_key="000000",
            reconstruction_class="document",
            evidence_refs=self.evidence_refs,
            properties={"document_candidate": True},
            provenance_ref="derivation:fixture:root",
        )
        ambiguous = ReconstructionUnit(
            id="reconstruction-unit:ambiguous-block",
            reconstruction_snapshot_ref=context.snapshot_ref,
            parent_ref=root.id,
            order_key="000001",
            reconstruction_class="block_candidate",
            evidence_refs=self.evidence_refs,
            properties={"role_hypotheses": ["text.heading", "text.prose_block"]},
            provenance_ref="derivation:fixture:block",
        )
        issue = ReconstructionIssue(
            id="reconstruction-issue:ambiguous-role",
            issue_type="role_low_confidence",
            severity="warning",
            affected_refs=(ambiguous.id,),
            message="Two document roles remain plausible.",
            suggested_action="review_role",
        )
        return StageResult(
            units=(root, ambiguous),
            issues=(issue,),
            open_state=OpenStructuralState(),
        )


def _evidence_snapshot() -> EvidenceSnapshot:
    partition_refs = (
        ArtifactRef(id="partition:0", digest="a" * 64, kind="evidence_partition"),
        ArtifactRef(id="partition:1", digest="b" * 64, kind="evidence_partition"),
    )
    return EvidenceSnapshot(
        id="snapshot:evidence:assembly",
        source_artifact_ref="source:assembly",
        extraction_activity_ref="activity:extract:assembly",
        extraction_profile_ref="extraction-profile:assembly",
        partition_refs=partition_refs,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
        snapshot_digest="c" * 64,
    )


def _engine(tmp_path: Path, now: datetime) -> tuple[ReconstructionEngine, MetadataStore]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    sql_engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    metadata.create_all(sql_engine)
    metadata_store = MetadataStore(sql_engine)
    evidence = _evidence_snapshot()
    engine = ReconstructionEngine(
        stages=(AmbiguousAssemblyStage(evidence.partition_refs),),
        blob_store=LocalBlobStore(tmp_path / "blobs"),
        metadata_store=metadata_store,
        now=lambda: now,
    )
    return engine, metadata_store


def test_assembly_persists_semantic_snapshot_and_all_evidence_accounting(tmp_path: Path):
    evidence = _evidence_snapshot()
    engine, metadata_store = _engine(tmp_path, datetime(2026, 9, 16, 12, tzinfo=UTC))

    snapshot = engine.assemble(evidence, reconstruction_profile_ref="reconstruction-profile:assembly")
    payload = engine.load_snapshot_payload(snapshot)

    assert snapshot.root_unit_refs == ("reconstruction-unit:document",)
    assert snapshot.reconstruction_validation_ref is not None
    assert payload.snapshot_ref == snapshot.id
    assert tuple(unit.id for unit in payload.units) == (
        "reconstruction-unit:document",
        "reconstruction-unit:ambiguous-block",
    )
    assert payload.units[1].parent_ref == payload.units[0].id
    assert payload.units[1].order_key == "000001"
    assert payload.issues[0].issue_type == "role_low_confidence"

    accounted = {
        (ref.id, ref.digest, ref.kind)
        for unit in payload.units
        for ref in unit.evidence_refs
    }
    expected = {(ref.id, ref.digest, ref.kind) for ref in evidence.partition_refs}
    assert accounted == expected

    registered = metadata_store.get_artifact(snapshot.id)
    assert registered is not None
    assert registered.kind == "reconstruction_snapshot"
    assert registered.digest == snapshot.snapshot_digest


def test_semantic_snapshot_digest_is_idempotent_across_activity_timestamps(tmp_path: Path):
    evidence = _evidence_snapshot()
    first_engine, _ = _engine(
        tmp_path / "first",
        datetime(2026, 9, 16, 12, tzinfo=UTC),
    )
    second_engine, _ = _engine(
        tmp_path / "second",
        datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    first = first_engine.assemble(evidence, reconstruction_profile_ref="reconstruction-profile:assembly")
    second = second_engine.assemble(evidence, reconstruction_profile_ref="reconstruction-profile:assembly")

    assert first.snapshot_digest == second.snapshot_digest
    assert first.id == second.id
    assert first.created_at != second.created_at
    assert first.reconstruction_activity_ref != second.reconstruction_activity_ref
    assert first_engine.load_snapshot_payload(first) == second_engine.load_snapshot_payload(second)
