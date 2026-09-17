from __future__ import annotations

from datetime import UTC, datetime

from voxcodex.domain.cbm.content import DocumentNode, FidelityConstraint
from voxcodex.domain.cbm.document import CanonicalRevision
from voxcodex.domain.cbm.structured import TableCell, TablePayload
from voxcodex.validation.engine import RevisionValidationBundle, validate_revision
from voxcodex.validation.policies import EvidenceAccountability, m2_poc_strict


def _revision(**overrides) -> CanonicalRevision:
    values = dict(
        id="revision:test",
        canonical_document_ref="document:test",
        revision_number=1,
        schema_version="0.1",
        root_node_ref="node:root",
        node_registry_ref="registry:nodes",
        content_registry_ref="registry:content",
        entity_registry_ref="registry:entities",
        semantic_registry_ref="registry:semantic",
        structured_payload_registry_ref="registry:structured",
        source_mapping_manifest_ref="manifest:source",
        provenance_manifest_ref="manifest:provenance",
        lifecycle_state="validated",
        created_by_activity_ref="activity:materialize",
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
    )
    values.update(overrides)
    return CanonicalRevision(**values)


def _node(node_id: str, parent_ref: str | None, *, role: str = "text.paragraph", node_class: str = "block"):
    return DocumentNode(
        id=node_id,
        parent_ref=parent_ref,
        order_key=node_id,
        node_class=node_class,
        role=role,
        source_anchor_refs=(f"anchor:{node_id}",),
        provenance_ref="derivation:test",
    )


def _bundle(*, nodes: tuple[DocumentNode, ...], tables: tuple[TablePayload, ...] = (), accountability=(), weakening=()):
    return RevisionValidationBundle(
        revision=_revision(),
        nodes=nodes,
        tables=tables,
        source_anchor_refs=tuple(anchor for node in nodes for anchor in node.source_anchor_refs),
        provenance_refs=("derivation:test",),
        evidence_accountability=accountability,
        fidelity_weakening_attempts=weakening,
    )


def _codes(report):
    return {check.code: check for check in report.checks}


def test_dangling_parent_ref_is_blocking():
    report = validate_revision(
        _bundle(nodes=(_node("node:root", None, role="text.chapter", node_class="division"), _node("node:child", "node:missing"))),
        m2_poc_strict(),
    )
    check = _codes(report)["structure.dangling_ref"]
    assert check.status == "FAIL"
    assert report.result == "FAIL"


def test_tree_cycle_is_blocking():
    nodes = (
        _node("node:root", "node:b", role="text.chapter", node_class="division"),
        _node("node:b", "node:root"),
    )
    report = validate_revision(_bundle(nodes=nodes), m2_poc_strict())
    assert _codes(report)["structure.tree_cycle"].status == "FAIL"


def test_illegal_role_node_class_pair_is_blocking():
    nodes = (_node("node:root", None, role="structured.table", node_class="block"),)
    report = validate_revision(_bundle(nodes=nodes), m2_poc_strict())
    assert _codes(report)["schema.role_node_class"].status == "FAIL"


def test_malformed_table_topology_is_blocking():
    table = TablePayload(
        id="table:bad",
        row_count=1,
        column_count=1,
        cells=(
            TableCell(id="cell:1", row=0, column=0, cell_role="body"),
            TableCell(id="cell:2", row=0, column=0, cell_role="body"),
        ),
    )
    report = validate_revision(
        _bundle(nodes=(_node("node:root", None, role="text.chapter", node_class="division"),), tables=(table,)),
        m2_poc_strict(),
    )
    assert _codes(report)["structure.table_topology"].status == "FAIL"


def test_missing_source_accountability_is_blocking():
    node = _node("node:root", None, role="text.chapter", node_class="division").model_copy(update={"source_anchor_refs": ()})
    report = validate_revision(_bundle(nodes=(node,)), m2_poc_strict())
    assert _codes(report)["traceability.source_accountability"].status == "FAIL"


def test_child_fidelity_weakening_is_blocking():
    root = _node("node:root", None, role="text.chapter", node_class="division").model_copy(
        update={"fidelity_constraints": (FidelityConstraint(dimension="character"),)}
    )
    child = _node("node:child", "node:root")
    report = validate_revision(
        _bundle(nodes=(root, child), weakening=("node:child:character",)),
        m2_poc_strict(),
    )
    assert _codes(report)["fidelity.inherited_weakening"].status == "FAIL"


def test_significant_suspected_loss_blocks_strict_freeze():
    accountability = (
        EvidenceAccountability(
            evidence_ref="evidence:significant",
            significance="significant",
            classification="suspected_loss",
            canonical_ref=None,
        ),
    )
    report = validate_revision(
        _bundle(nodes=(_node("node:root", None, role="text.chapter", node_class="division"),), accountability=accountability),
        m2_poc_strict(),
    )
    assert _codes(report)["coverage.significant_suspected_loss"].status == "FAIL"
    assert report.result == "FAIL"


def test_unresolved_non_significant_evidence_warns_but_does_not_fail():
    accountability = (
        EvidenceAccountability(
            evidence_ref="evidence:decorative",
            significance="non_significant",
            classification="unresolved",
            canonical_ref=None,
        ),
    )
    report = validate_revision(
        _bundle(nodes=(_node("node:root", None, role="text.chapter", node_class="division"),), accountability=accountability),
        m2_poc_strict(),
    )
    assert _codes(report)["coverage.unresolved_non_significant"].status == "WARN"
    assert report.result == "WARN"
