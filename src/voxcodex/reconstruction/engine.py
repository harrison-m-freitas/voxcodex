from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.evidence import EvidenceSnapshot
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.domain.reconstruction import (
    OpenStructuralState,
    ReconstructionContext,
    ReconstructionIssue,
    ReconstructionSnapshot,
    ReconstructionStage,
    ReconstructionUnit,
    StageResult,
)
from voxcodex.ids import new_event_id
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore


class ReconstructionSnapshotPayload(FrozenModel):
    snapshot_ref: str
    source_evidence_refs: tuple[ArtifactRef, ...]
    reconstruction_profile_ref: str
    root_unit_refs: tuple[str, ...]
    units: tuple[ReconstructionUnit, ...]
    issues: tuple[ReconstructionIssue, ...]
    open_state: OpenStructuralState
    reconstruction_validation_ref: str


class ReconstructionEngine:
    def __init__(
        self,
        *,
        stages: Sequence[ReconstructionStage],
        blob_store: LocalBlobStore,
        metadata_store: MetadataStore,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.stages = tuple(stages)
        self.blob_store = blob_store
        self.metadata_store = metadata_store
        self.now = now or (lambda: datetime.now(UTC))

    def run(
        self,
        evidence_snapshot: EvidenceSnapshot,
        *,
        reconstruction_profile_ref: str,
    ) -> StageResult:
        result, _context, _last_output_ref = self._execute(
            evidence_snapshot,
            reconstruction_profile_ref=reconstruction_profile_ref,
        )
        return result

    def assemble(
        self,
        evidence_snapshot: EvidenceSnapshot,
        *,
        reconstruction_profile_ref: str,
    ) -> ReconstructionSnapshot:
        result, context, last_output_ref = self._execute(
            evidence_snapshot,
            reconstruction_profile_ref=reconstruction_profile_ref,
        )
        timestamp = self.now()
        activity = ProcessingActivity(
            id=f"activity:reconstruction-assembly:{new_event_id()}",
            type="reconstruction_assembly",
            processor=ProcessorIdentity(
                kind="python",
                name="reconstruction.assembly",
                version="0.1.0",
            ),
            configuration_ref=reconstruction_profile_ref,
            started_at=timestamp,
            completed_at=timestamp,
            status="succeeded",
        )
        self.metadata_store.register_activity(activity)

        validation_ref = self._persist_reconstruction_validation(
            context=context,
            result=result,
        )
        root_unit_refs = tuple(unit.id for unit in result.units if unit.parent_ref is None)
        payload = ReconstructionSnapshotPayload(
            snapshot_ref=context.snapshot_ref,
            source_evidence_refs=context.source_evidence_refs,
            reconstruction_profile_ref=reconstruction_profile_ref,
            root_unit_refs=root_unit_refs,
            units=result.units,
            issues=result.issues,
            open_state=result.open_state,
            reconstruction_validation_ref=validation_ref.id,
        )
        snapshot_blob = self.blob_store.put_bytes(
            canonical_json_bytes(payload.model_dump(mode="json"))
        )
        snapshot_ref = ArtifactRef(
            id=context.snapshot_ref,
            digest=snapshot_blob.sha256,
            kind="reconstruction_snapshot",
        )
        self._ensure_artifact(snapshot_ref)

        self.metadata_store.register_derivation(
            Derivation(
                id=f"derivation:reconstruction-assembly:{new_event_id()}",
                activity_ref=activity.id,
                input_refs=(last_output_ref,),
                output_refs=(validation_ref, snapshot_ref),
                derivation_kind="assembled",
            )
        )

        return ReconstructionSnapshot(
            id=snapshot_ref.id,
            source_evidence_refs=context.source_evidence_refs,
            reconstruction_activity_ref=activity.id,
            reconstruction_profile_ref=reconstruction_profile_ref,
            root_unit_refs=root_unit_refs,
            reconstruction_validation_ref=validation_ref.id,
            created_at=timestamp,
            snapshot_digest=snapshot_ref.digest,
        )

    def load_snapshot_payload(
        self,
        snapshot: ReconstructionSnapshot,
    ) -> ReconstructionSnapshotPayload:
        data = self.blob_store.read_digest(snapshot.snapshot_digest)
        return ReconstructionSnapshotPayload.model_validate_json(data)

    def _execute(
        self,
        evidence_snapshot: EvidenceSnapshot,
        *,
        reconstruction_profile_ref: str,
    ) -> tuple[StageResult, ReconstructionContext, ArtifactRef]:
        evidence_ref = ArtifactRef(
            id=evidence_snapshot.id,
            digest=evidence_snapshot.snapshot_digest,
            kind="evidence_snapshot",
        )
        self._ensure_artifact(evidence_ref)

        snapshot_seed = {
            "source_evidence_refs": [evidence_ref.model_dump(mode="json")],
            "reconstruction_profile_ref": reconstruction_profile_ref,
            "stages": [
                {"name": stage.name, "version": stage.version}
                for stage in self.stages
            ],
        }
        snapshot_ref = f"reconstruction-snapshot:{sha256_bytes(canonical_json_bytes(snapshot_seed))}"
        context = ReconstructionContext(
            snapshot_ref=snapshot_ref,
            source_evidence_refs=(evidence_ref,),
            reconstruction_profile_ref=reconstruction_profile_ref,
        )

        current_result = StageResult()
        current_input_ref = evidence_ref

        for index, stage in enumerate(self.stages):
            current_result = stage.run(context, current_result.units)
            output_ref = self._persist_stage_result(
                stage=stage,
                stage_index=index,
                context=context,
                result=current_result,
            )
            self._record_stage_derivation(
                stage=stage,
                input_ref=current_input_ref,
                output_ref=output_ref,
                reconstruction_profile_ref=reconstruction_profile_ref,
            )
            current_input_ref = output_ref

        return current_result, context, current_input_ref

    def _persist_stage_result(
        self,
        *,
        stage: ReconstructionStage,
        stage_index: int,
        context: ReconstructionContext,
        result: StageResult,
    ) -> ArtifactRef:
        payload = {
            "stage": {
                "name": stage.name,
                "version": stage.version,
                "index": stage_index,
            },
            "context": context.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
        }
        data = canonical_json_bytes(payload)
        blob = self.blob_store.put_bytes(data)
        artifact = ArtifactRef(
            id=f"reconstruction-stage:{stage.name}:{blob.sha256}",
            digest=blob.sha256,
            kind="reconstruction_stage_output",
        )
        self._ensure_artifact(artifact)
        return artifact

    def _persist_reconstruction_validation(
        self,
        *,
        context: ReconstructionContext,
        result: StageResult,
    ) -> ArtifactRef:
        payload = {
            "snapshot_ref": context.snapshot_ref,
            "reconstruction_profile_ref": context.reconstruction_profile_ref,
            "issues": [issue.model_dump(mode="json") for issue in result.issues],
            "open_state": result.open_state.model_dump(mode="json"),
        }
        blob = self.blob_store.put_bytes(canonical_json_bytes(payload))
        artifact = ArtifactRef(
            id=f"reconstruction-validation:{blob.sha256}",
            digest=blob.sha256,
            kind="reconstruction_validation",
        )
        self._ensure_artifact(artifact)
        return artifact

    def _record_stage_derivation(
        self,
        *,
        stage: ReconstructionStage,
        input_ref: ArtifactRef,
        output_ref: ArtifactRef,
        reconstruction_profile_ref: str,
    ) -> None:
        timestamp = self.now()
        activity = ProcessingActivity(
            id=f"activity:reconstruction:{new_event_id()}",
            type="reconstruction_stage",
            processor=ProcessorIdentity(
                kind="python",
                name=f"reconstruction.{stage.name}",
                version=stage.version,
            ),
            configuration_ref=reconstruction_profile_ref,
            started_at=timestamp,
            completed_at=timestamp,
            status="succeeded",
        )
        self.metadata_store.register_activity(activity)
        self.metadata_store.register_derivation(
            Derivation(
                id=f"derivation:reconstruction:{new_event_id()}",
                activity_ref=activity.id,
                input_refs=(input_ref,),
                output_refs=(output_ref,),
                derivation_kind="reconstructed",
            )
        )

    def _ensure_artifact(self, artifact: ArtifactRef) -> None:
        existing = self.metadata_store.get_artifact(artifact.id)
        if existing is None:
            self.metadata_store.register_artifact(artifact)
            return
        if existing != artifact:
            raise ValueError(
                f"artifact identity collision for {artifact.id}: "
                f"existing={existing.model_dump()} incoming={artifact.model_dump()}"
            )
