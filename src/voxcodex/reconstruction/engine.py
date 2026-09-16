from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceSnapshot
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.domain.reconstruction import (
    ReconstructionContext,
    ReconstructionStage,
    StageResult,
)
from voxcodex.ids import new_event_id
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore


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
        evidence_ref = ArtifactRef(
            id=evidence_snapshot.id,
            digest=evidence_snapshot.snapshot_digest,
            kind="evidence_snapshot",
        )
        self._ensure_artifact(evidence_ref)

        snapshot_seed = {
            "source_evidence_refs": [evidence_ref.model_dump(mode="json")],
            "reconstruction_profile_ref": reconstruction_profile_ref,
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

        return current_result

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
