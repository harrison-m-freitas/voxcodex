from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import Field

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.processing import ProcessorIdentity
from voxcodex.execution.fingerprint import ActivityFingerprint
from voxcodex.materialization.builder import CanonicalTargetContext
from voxcodex.storage.metadata import MetadataStore


class PipelineStage(FrozenModel):
    name: str
    activity_type: str
    processor: ProcessorIdentity
    semantic_config_digest: str
    profile_versions: tuple[str, ...] = ()
    schema_versions: tuple[str, ...] = ()
    input_order_matters: bool = True
    uses_target_context: bool = False
    derivation_kind: str = "reconstructed"
    estimated_usage: dict[str, float] = Field(default_factory=dict)

    def effective_semantic_config_digest(self, target_context: CanonicalTargetContext) -> str:
        if not self.uses_target_context:
            return self.semantic_config_digest
        payload = {
            "semantic_config_digest": self.semantic_config_digest,
            "target_context": target_context.model_dump(mode="json"),
        }
        return sha256_bytes(canonical_json_bytes(payload))


class ExecutionConfig(FrozenModel):
    stages: tuple[PipelineStage, ...] = Field(min_length=1)
    operational_config: dict[str, Any] = Field(default_factory=dict)


class ReuseCandidate(FrozenModel):
    stage_name: str
    activity_fingerprint: str
    output_refs: tuple[ArtifactRef, ...]
    producing_activity_ref: str


class InvalidatedArtifact(FrozenModel):
    artifact_ref: ArtifactRef
    reason: str


class PlannedActivity(FrozenModel):
    stage: PipelineStage
    semantic_config_digest: str
    input_refs: tuple[ArtifactRef, ...]
    activity_fingerprint: str | None
    requires_processing: bool
    reuse_output_refs: tuple[ArtifactRef, ...] = ()


class ExecutionPlan(FrozenModel):
    target: str = "cbm"
    source_ref: ArtifactRef
    target_context: CanonicalTargetContext
    config: ExecutionConfig
    activities: tuple[PlannedActivity, ...]
    reuse_candidates: tuple[ReuseCandidate, ...] = ()
    invalidated_artifacts: tuple[InvalidatedArtifact, ...] = ()
    estimated_usage: dict[str, float] = Field(default_factory=dict)

    @property
    def reuse_count(self) -> int:
        return sum(1 for activity in self.activities if not activity.requires_processing)

    @property
    def process_count(self) -> int:
        return sum(1 for activity in self.activities if activity.requires_processing)

    @property
    def required_processor_work(self) -> int:
        return self.process_count


def plan_to_cbm(
    source_ref: ArtifactRef,
    target_context: CanonicalTargetContext,
    config: ExecutionConfig,
    *,
    metadata_store: MetadataStore,
) -> ExecutionPlan:
    """Build an immutable dry-run plan without creating causal records."""

    current_inputs: tuple[ArtifactRef, ...] = (source_ref,)
    inputs_are_materialized = True
    planned: list[PlannedActivity] = []
    reuse_candidates: list[ReuseCandidate] = []

    usage_dimensions: set[str] = {
        key for stage in config.stages for key in stage.estimated_usage
    }
    estimated_usage: dict[str, float] = {key: 0.0 for key in sorted(usage_dimensions)}

    for stage in config.stages:
        semantic_config_digest = stage.effective_semantic_config_digest(target_context)
        fingerprint: str | None = None
        reusable_outputs: tuple[ArtifactRef, ...] = ()

        if inputs_are_materialized:
            fingerprint = ActivityFingerprint.compute(
                stage.activity_type,
                stage.processor,
                semantic_config_digest,
                tuple(ref.digest for ref in current_inputs),
                stage.profile_versions,
                stage.schema_versions,
                input_order_matters=stage.input_order_matters,
                operational_config=config.operational_config,
            )
            reusable_outputs = metadata_store.find_reusable_output(fingerprint)

        if reusable_outputs:
            producer = metadata_store.get_producing_activity(reusable_outputs[0])
            if producer is None:
                raise ValueError(
                    f"reusable outputs for stage {stage.name} have no producing activity"
                )
            reuse_candidates.append(
                ReuseCandidate(
                    stage_name=stage.name,
                    activity_fingerprint=fingerprint or "",
                    output_refs=reusable_outputs,
                    producing_activity_ref=producer.id,
                )
            )
            planned.append(
                PlannedActivity(
                    stage=stage,
                    semantic_config_digest=semantic_config_digest,
                    input_refs=current_inputs,
                    activity_fingerprint=fingerprint,
                    requires_processing=False,
                    reuse_output_refs=reusable_outputs,
                )
            )
            current_inputs = reusable_outputs
            continue

        planned.append(
            PlannedActivity(
                stage=stage,
                semantic_config_digest=semantic_config_digest,
                input_refs=current_inputs,
                activity_fingerprint=fingerprint,
                requires_processing=True,
            )
        )
        for key, value in stage.estimated_usage.items():
            estimated_usage[key] = estimated_usage.get(key, 0.0) + float(value)

        # The actual output digest is unknown until execution. Downstream stages
        # therefore remain process-required and do not perform speculative cache lookups.
        inputs_are_materialized = False
        pending_seed = {
            "stage": stage.name,
            "activity_fingerprint": fingerprint,
            "semantic_config_digest": semantic_config_digest,
        }
        pending_digest = sha256_bytes(canonical_json_bytes(pending_seed))
        current_inputs = (
            ArtifactRef(
                id=f"planned-output:{stage.name}:{pending_digest}",
                digest=pending_digest,
                kind="planned_semantic_output",
            ),
        )

    return ExecutionPlan(
        source_ref=source_ref,
        target_context=target_context,
        config=config,
        activities=tuple(planned),
        reuse_candidates=tuple(reuse_candidates),
        estimated_usage=estimated_usage,
    )
