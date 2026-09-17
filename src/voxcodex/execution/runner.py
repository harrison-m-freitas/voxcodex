from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from pydantic import model_validator

from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.processing import Derivation, ProcessingActivity
from voxcodex.execution.fingerprint import ActivityFingerprint
from voxcodex.execution.planner import ExecutionPlan, PlannedActivity
from voxcodex.ids import new_event_id
from voxcodex.storage.metadata import MetadataStore


StageExecutor = Callable[[PlannedActivity, tuple[ArtifactRef, ...]], tuple[ArtifactRef, ...]]


class ExecutionOutputComponent(FrozenModel):
    artifact_ref: ArtifactRef
    complete: bool


class ExecutionOutputManifest(FrozenModel):
    components: tuple[ExecutionOutputComponent, ...] = ()
    aggregate_output_ref: ArtifactRef | None = None
    aggregate_complete: bool = False

    @model_validator(mode="after")
    def validate_aggregate(self) -> "ExecutionOutputManifest":
        if self.aggregate_complete and self.aggregate_output_ref is None:
            raise ValueError("a complete aggregate requires aggregate_output_ref")
        return self

    @property
    def reusable_component_refs(self) -> tuple[ArtifactRef, ...]:
        return tuple(
            component.artifact_ref
            for component in self.components
            if component.complete
        )

    @property
    def reusable_aggregate_ref(self) -> ArtifactRef | None:
        if not self.aggregate_complete:
            return None
        return self.aggregate_output_ref


class ExecutionResult(FrozenModel):
    final_output_refs: tuple[ArtifactRef, ...]
    reused_activity_count: int
    executed_activity_count: int


def execute_plan(
    plan: ExecutionPlan,
    *,
    metadata_store: MetadataStore,
    executors: Mapping[str, StageExecutor] | None = None,
) -> ExecutionResult:
    """Execute an immutable plan while preserving reuse provenance.

    Reused stages return their original outputs and create no new activity or
    derivation. Processing stages require an explicit executor and only then
    create causal records.
    """

    current_inputs: tuple[ArtifactRef, ...] = (plan.source_ref,)
    reused_count = 0
    executed_count = 0
    executors = executors or {}

    for planned in plan.activities:
        fingerprint = ActivityFingerprint.compute(
            planned.stage.activity_type,
            planned.stage.processor,
            planned.semantic_config_digest,
            tuple(ref.digest for ref in current_inputs),
            planned.stage.profile_versions,
            planned.stage.schema_versions,
            input_order_matters=planned.stage.input_order_matters,
            operational_config=plan.config.operational_config,
        )

        reusable = metadata_store.find_reusable_output(fingerprint)
        if reusable:
            current_inputs = reusable
            reused_count += 1
            continue

        executor = executors.get(planned.stage.name)
        if executor is None:
            raise RuntimeError(
                f"stage {planned.stage.name} requires processor work but no executor is configured"
            )

        # No ProcessingActivity exists for a dry-run. The causal activity is
        # created only as part of actual execution after processor work succeeds.
        outputs = tuple(executor(planned, current_inputs))
        if not outputs:
            raise ValueError(f"executor for stage {planned.stage.name} produced no outputs")
        for output in outputs:
            existing = metadata_store.get_artifact(output.id)
            if existing is None:
                metadata_store.register_artifact(output)
            elif existing != output:
                raise ValueError(f"artifact identity collision for {output.id}")

        timestamp = datetime.now(UTC)
        activity = ProcessingActivity(
            id=f"activity:execution:{new_event_id()}",
            type=planned.stage.activity_type,
            processor=planned.stage.processor,
            configuration_ref=planned.semantic_config_digest,
            started_at=timestamp,
            completed_at=timestamp,
            status="succeeded",
        )
        metadata_store.register_activity(activity, activity_fingerprint=fingerprint)
        metadata_store.register_derivation(
            Derivation(
                id=f"derivation:execution:{new_event_id()}",
                activity_ref=activity.id,
                input_refs=current_inputs,
                output_refs=outputs,
                derivation_kind=planned.stage.derivation_kind,
            )
        )
        current_inputs = outputs
        executed_count += 1

    return ExecutionResult(
        final_output_refs=current_inputs,
        reused_activity_count=reused_count,
        executed_activity_count=executed_count,
    )
