from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.execution.fingerprint import ActivityFingerprint
from voxcodex.execution.planner import (
    ExecutionConfig,
    PipelineStage,
    plan_to_cbm,
)
from voxcodex.execution.runner import execute_plan
from voxcodex.materialization.builder import CanonicalTargetContext
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import derivations, metadata, processing_activities


def _stage(name: str, *, uses_target_context: bool = False) -> PipelineStage:
    return PipelineStage(
        name=name,
        activity_type=name,
        processor=ProcessorIdentity(kind="python", name=f"m2.{name}", version="1.0.0"),
        semantic_config_digest=(name[0] * 64),
        profile_versions=(f"{name}-profile:0.1",),
        schema_versions=("m2:0.1",),
        uses_target_context=uses_target_context,
        estimated_usage={"work_units": 1},
    )


def _target() -> CanonicalTargetContext:
    return CanonicalTargetContext(
        canonical_document_ref="canonical-document:1",
        work_ref="work:1",
        edition_ref="edition:1",
        source_artifact_refs=("source:1",),
        assertion_provenance_ref="assertion:human:1",
    )


def _register_completed_pipeline(
    store: MetadataStore,
    source: ArtifactRef,
    config: ExecutionConfig,
    target: CanonicalTargetContext,
) -> tuple[ArtifactRef, ...]:
    current = (source,)
    outputs: list[ArtifactRef] = []
    now = datetime(2026, 9, 17, tzinfo=UTC)

    for index, stage in enumerate(config.stages):
        semantic_config_digest = stage.effective_semantic_config_digest(target)
        fingerprint = ActivityFingerprint.compute(
            stage.activity_type,
            stage.processor,
            semantic_config_digest,
            tuple(ref.digest for ref in current),
            stage.profile_versions,
            stage.schema_versions,
            input_order_matters=stage.input_order_matters,
        )
        output = ArtifactRef(
            id=f"artifact:{stage.name}",
            digest=(str(index + 2) * 64),
            kind=f"{stage.name}_output",
        )
        store.register_artifact(output)
        activity = ProcessingActivity(
            id=f"activity:{stage.name}",
            type=stage.activity_type,
            processor=stage.processor,
            configuration_ref=stage.semantic_config_digest,
            started_at=now,
            completed_at=now,
            status="succeeded",
        )
        store.register_activity(activity, activity_fingerprint=fingerprint)
        store.register_derivation(
            Derivation(
                id=f"derivation:{stage.name}",
                activity_ref=activity.id,
                input_refs=current,
                output_refs=(output,),
                derivation_kind="reconstructed",
            )
        )
        current = (output,)
        outputs.append(output)

    return tuple(outputs)


def test_unchanged_completed_pipeline_dry_run_reuses_every_stage_and_does_no_work():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)
    source = ArtifactRef(id="source:1", digest="a" * 64, kind="source_artifact")
    store.register_artifact(source)
    target = _target()
    config = ExecutionConfig(
        stages=(
            _stage("evidence"),
            _stage("reconstruction"),
            _stage("materialization", uses_target_context=True),
        )
    )
    outputs = _register_completed_pipeline(store, source, config, target)

    with engine.connect() as connection:
        before_activities = connection.scalar(select(func.count()).select_from(processing_activities))
        before_derivations = connection.scalar(select(func.count()).select_from(derivations))

    plan = plan_to_cbm(source, target, config, metadata_store=store)

    assert plan.required_processor_work == 0
    assert plan.reuse_count == 3
    assert plan.process_count == 0
    assert tuple(candidate.output_refs[0] for candidate in plan.reuse_candidates) == outputs
    assert all(not activity.requires_processing for activity in plan.activities)
    assert plan.estimated_usage == {"work_units": 0}

    with pytest.raises(ValidationError):
        plan.target = "other"  # type: ignore[misc]

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(processing_activities)) == before_activities
        assert connection.scalar(select(func.count()).select_from(derivations)) == before_derivations

    result = execute_plan(plan, metadata_store=store)
    assert result.final_output_refs == (outputs[-1],)
    assert result.reused_activity_count == 3
    assert result.executed_activity_count == 0

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(processing_activities)) == before_activities
        assert connection.scalar(select(func.count()).select_from(derivations)) == before_derivations


def test_fresh_source_requires_processor_work_but_planning_creates_no_activity():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)
    source = ArtifactRef(id="source:1", digest="a" * 64, kind="source_artifact")
    store.register_artifact(source)
    config = ExecutionConfig(stages=(_stage("evidence"), _stage("reconstruction")))

    plan = plan_to_cbm(source, _target(), config, metadata_store=store)

    assert plan.process_count == 2
    assert plan.required_processor_work == 2
    assert plan.reuse_count == 0
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(processing_activities)) == 0
