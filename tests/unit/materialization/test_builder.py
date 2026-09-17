from __future__ import annotations

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.reconstruction import ReconstructionUnit
from voxcodex.materialization.builder import (
    CanonicalTargetContext,
    MaterializationIssue,
    build_canonical_draft,
    shard_registry_objects,
)
from voxcodex.materialization.mappings import RoleMappingRegistry


def _ref(name: str) -> ArtifactRef:
    return ArtifactRef(id=f"evidence:{name}", digest=(name[0] * 64), kind="evidence_unit")


def _unit(unit_id: str, order_key: str, role: str) -> ReconstructionUnit:
    return ReconstructionUnit(
        id=unit_id,
        reconstruction_snapshot_ref="reconstruction-snapshot:test",
        parent_ref=None,
        order_key=order_key,
        reconstruction_class="block_candidate",
        evidence_refs=(_ref(unit_id[-1]),),
        properties={"resolved_role": role, "surface": unit_id},
        provenance_ref="derivation:reconstruction:test",
    )


def test_registry_sharding_is_deterministic_across_python_insertion_order():
    objects_a = {
        "node:c": {"id": "node:c", "order_key": "30"},
        "node:a": {"id": "node:a", "order_key": "10"},
        "node:b": {"id": "node:b", "order_key": "20"},
    }
    objects_b = dict(reversed(tuple(objects_a.items())))

    first = shard_registry_objects("nodes", objects_a, max_objects_per_shard=2)
    second = shard_registry_objects("nodes", objects_b, max_objects_per_shard=2)

    assert first.manifest_digest == second.manifest_digest
    assert first.shard_digests == second.shard_digests
    assert first.object_refs == ("node:a", "node:b", "node:c")
    assert tuple(len(shard.object_refs) for shard in first.shards) == (2, 1)


def test_builder_uses_target_identity_and_stable_reconstruction_keys():
    context = CanonicalTargetContext(
        work_ref="work:fedra",
        edition_ref="edition:centaur-2013",
        source_artifact_refs=("source:fedra",),
        assertion_provenance_ref="assertion:intake:1",
    )
    mappings = RoleMappingRegistry.v01_defaults()
    units = (
        _unit("unit:2", "000020", "text.paragraph"),
        _unit("unit:1", "000010", "text.heading"),
    )

    first = build_canonical_draft(
        reconstruction_snapshot_digest="a" * 64,
        units=units,
        target_context=context,
        role_mappings=mappings,
    )
    second = build_canonical_draft(
        reconstruction_snapshot_digest="a" * 64,
        units=tuple(reversed(units)),
        target_context=context,
        role_mappings=mappings,
    )

    assert first.canonical_document.id == second.canonical_document.id
    assert tuple(node.id for node in first.nodes) == tuple(node.id for node in second.nodes)
    assert tuple(node.order_key for node in first.nodes) == ("000010", "000020")
    assert first.issues == ()


def test_unregistered_resolved_role_emits_materialization_issue_without_silent_drop():
    context = CanonicalTargetContext(
        canonical_document_ref="document:existing",
        work_ref="work:test",
        edition_ref="edition:test",
        source_artifact_refs=("source:test",),
        assertion_provenance_ref="assertion:intake:test",
    )
    unit = _unit("unit:x", "000010", "experimental.unregistered_role")

    draft = build_canonical_draft(
        reconstruction_snapshot_digest="b" * 64,
        units=(unit,),
        target_context=context,
        role_mappings=RoleMappingRegistry.v01_defaults(),
    )

    assert draft.nodes == ()
    assert draft.unmaterialized_unit_refs == (unit.id,)
    assert draft.issues == (
        MaterializationIssue(
            id=draft.issues[0].id,
            issue_type="unmapped_role",
            classification="MODEL_GAP",
            affected_refs=(unit.id,),
            message="resolved reconstruction role has no registered CBM v0.1 mapping: experimental.unregistered_role",
        ),
    )
