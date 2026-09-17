from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy import create_engine

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.execution.invalidation import compute_affected
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


def _store() -> MetadataStore:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    return MetadataStore(engine)


def _artifact(name: str, kind: str) -> ArtifactRef:
    return ArtifactRef(
        id=f"artifact:{name}",
        digest=sha256(name.encode("utf-8")).hexdigest(),
        kind=kind,
    )


def _derive(
    store: MetadataStore,
    name: str,
    *,
    inputs: tuple[ArtifactRef, ...],
    outputs: tuple[ArtifactRef, ...],
    derivation_kind: str,
) -> None:
    now = datetime(2026, 9, 17, tzinfo=UTC)
    activity = ProcessingActivity(
        id=f"activity:{name}",
        type=name,
        processor=ProcessorIdentity(kind="python", name="selective-reprocessing-test", version="1"),
        started_at=now,
        completed_at=now,
        status="succeeded",
    )
    store.register_activity(activity)
    store.register_derivation(
        Derivation(
            id=f"derivation:{name}",
            activity_ref=activity.id,
            input_refs=inputs,
            output_refs=outputs,
            derivation_kind=derivation_kind,
        )
    )


def _register(store: MetadataStore, *refs: ArtifactRef) -> None:
    for ref in refs:
        store.register_artifact(ref)


def _affected_ids(store: MetadataStore, changed: ArtifactRef, target: ArtifactRef) -> set[str]:
    graph = compute_affected(store, changed_refs=(changed,), target_refs=(target,))
    return {ref.id for ref in graph.affected_refs}


def test_scenario_a_validation_policy_change_reruns_only_validation():
    store = _store()
    evidence = _artifact("evidence-page-1", "evidence_snapshot")
    reconstruction = _artifact("reconstruction-v1", "reconstruction_snapshot")
    revision = _artifact("canonical-revision-v1", "canonical_revision")
    policy_v1 = _artifact("validation-policy-v1", "validation_policy")
    report_v1 = _artifact("validation-report-v1", "validation_report")
    policy_v2 = _artifact("validation-policy-v2", "validation_policy")
    _register(store, evidence, reconstruction, revision, policy_v1, report_v1, policy_v2)

    _derive(
        store,
        "reconstruct",
        inputs=(evidence,),
        outputs=(reconstruction,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "materialize",
        inputs=(reconstruction,),
        outputs=(revision,),
        derivation_kind="materialized",
    )
    _derive(
        store,
        "validate-v1",
        inputs=(revision, policy_v1),
        outputs=(report_v1,),
        derivation_kind="validated",
    )

    affected = _affected_ids(store, policy_v1, report_v1)

    assert affected == {report_v1.id}
    assert evidence.id not in affected
    assert reconstruction.id not in affected
    assert revision.id not in affected
    assert store.get_artifact(revision.id) == revision
    assert store.get_artifact(policy_v1.id) == policy_v1
    assert store.get_artifact(policy_v2.id) == policy_v2


def test_scenario_b_local_table_profile_change_reuses_evidence_and_unrelated_branch():
    store = _store()
    evidence_table = _artifact("evidence-table-region", "evidence_unit")
    evidence_paragraph = _artifact("evidence-paragraph-region", "evidence_unit")
    table_profile_v1 = _artifact("table-profile-v1", "reconstruction_profile")
    table_profile_v2 = _artifact("table-profile-v2", "reconstruction_profile")
    reconstruction_table = _artifact("reconstruction-table-v1", "reconstruction_unit")
    reconstruction_paragraph = _artifact("reconstruction-paragraph-v1", "reconstruction_unit")
    materialized_table = _artifact("materialized-table-v1", "canonical_table")
    materialized_paragraph = _artifact("materialized-paragraph-v1", "canonical_block")
    revision = _artifact("canonical-revision-table-case-v1", "canonical_revision")
    policy = _artifact("validation-policy-table-case", "validation_policy")
    report = _artifact("validation-report-table-case-v1", "validation_report")
    _register(
        store,
        evidence_table,
        evidence_paragraph,
        table_profile_v1,
        table_profile_v2,
        reconstruction_table,
        reconstruction_paragraph,
        materialized_table,
        materialized_paragraph,
        revision,
        policy,
        report,
    )

    _derive(
        store,
        "reconstruct-table",
        inputs=(evidence_table, table_profile_v1),
        outputs=(reconstruction_table,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "reconstruct-paragraph",
        inputs=(evidence_paragraph,),
        outputs=(reconstruction_paragraph,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "materialize-table",
        inputs=(reconstruction_table,),
        outputs=(materialized_table,),
        derivation_kind="materialized",
    )
    _derive(
        store,
        "materialize-paragraph",
        inputs=(reconstruction_paragraph,),
        outputs=(materialized_paragraph,),
        derivation_kind="materialized",
    )
    _derive(
        store,
        "assemble-revision-table-case",
        inputs=(materialized_table, materialized_paragraph),
        outputs=(revision,),
        derivation_kind="assembled",
    )
    _derive(
        store,
        "validate-table-case",
        inputs=(revision, policy),
        outputs=(report,),
        derivation_kind="validated",
    )

    affected = _affected_ids(store, table_profile_v1, report)

    assert affected == {
        reconstruction_table.id,
        materialized_table.id,
        revision.id,
        report.id,
    }
    assert evidence_table.id not in affected
    assert evidence_paragraph.id not in affected
    assert reconstruction_paragraph.id not in affected
    assert materialized_paragraph.id not in affected
    assert store.get_artifact(table_profile_v2.id) == table_profile_v2


def test_scenario_c_region_evidence_replacement_closes_reconciliation_radius_only():
    store = _store()
    region_a = _artifact("evidence-region-a", "evidence_unit")
    region_b = _artifact("evidence-region-b-neighbor", "evidence_unit")
    region_c = _artifact("evidence-region-c-independent", "evidence_unit")
    region_a_replacement = _artifact("evidence-region-a-v2", "evidence_unit")
    reconstruction_a = _artifact("reconstruction-region-a", "reconstruction_unit")
    reconstruction_b = _artifact("reconstruction-region-b", "reconstruction_unit")
    reconstruction_c = _artifact("reconstruction-region-c", "reconstruction_unit")
    reconciled_ab = _artifact("reconciled-a-b", "reconstruction_snapshot")
    materialized_ab = _artifact("materialized-a-b", "canonical_block")
    materialized_c = _artifact("materialized-c", "canonical_block")
    revision = _artifact("canonical-revision-region-case-v1", "canonical_revision")
    policy = _artifact("validation-policy-region-case", "validation_policy")
    report = _artifact("validation-report-region-case-v1", "validation_report")
    _register(
        store,
        region_a,
        region_b,
        region_c,
        region_a_replacement,
        reconstruction_a,
        reconstruction_b,
        reconstruction_c,
        reconciled_ab,
        materialized_ab,
        materialized_c,
        revision,
        policy,
        report,
    )

    _derive(
        store,
        "reconstruct-region-a",
        inputs=(region_a,),
        outputs=(reconstruction_a,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "reconstruct-region-b",
        inputs=(region_b,),
        outputs=(reconstruction_b,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "reconstruct-region-c",
        inputs=(region_c,),
        outputs=(reconstruction_c,),
        derivation_kind="reconstructed",
    )
    _derive(
        store,
        "reconcile-a-b",
        inputs=(reconstruction_a, reconstruction_b),
        outputs=(reconciled_ab,),
        derivation_kind="reconciled",
    )
    _derive(
        store,
        "materialize-a-b",
        inputs=(reconciled_ab,),
        outputs=(materialized_ab,),
        derivation_kind="materialized",
    )
    _derive(
        store,
        "materialize-c",
        inputs=(reconstruction_c,),
        outputs=(materialized_c,),
        derivation_kind="materialized",
    )
    _derive(
        store,
        "assemble-revision-region-case",
        inputs=(materialized_ab, materialized_c),
        outputs=(revision,),
        derivation_kind="assembled",
    )
    _derive(
        store,
        "validate-region-case",
        inputs=(revision, policy),
        outputs=(report,),
        derivation_kind="validated",
    )

    affected = _affected_ids(store, region_a, report)

    assert affected == {
        reconstruction_a.id,
        reconciled_ab.id,
        materialized_ab.id,
        revision.id,
        report.id,
    }
    assert reconstruction_b.id not in affected
    assert reconstruction_c.id not in affected
    assert materialized_c.id not in affected
    assert region_b.id not in affected
    assert region_c.id not in affected
    assert store.get_artifact(region_a.id) == region_a
    assert store.get_artifact(region_a_replacement.id) == region_a_replacement
