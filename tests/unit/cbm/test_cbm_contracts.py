from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from voxcodex.domain.cbm.content import ContentFragment, DocumentNode, Surface
from voxcodex.domain.cbm.document import CanonicalDocument, CanonicalRevision
from voxcodex.domain.cbm.schema_snapshots import SCHEMA_MODELS, schema_text
from voxcodex.domain.cbm.semantic import Annotation, Relation, SemanticRegistry
from voxcodex.domain.cbm.structured import FormulaPayload, TableCell, TablePayload


SCHEMA_ROOT = Path(__file__).resolve().parents[3] / "schemas" / "cbm" / "0.1"


def test_content_fragment_requires_exactly_one_document_node_owner_and_is_frozen():
    fragment = ContentFragment(
        id="fragment:1",
        owner_node_ref="node:1",
        order_key="000010",
        fragment_class="text",
        role="text.paragraph",
        surface=Surface(text="surface", language="pt"),
        provenance_ref="derivation:1",
    )

    assert fragment.owner_node_ref == "node:1"
    with pytest.raises(ValidationError):
        fragment.owner_node_ref = "node:2"


def test_document_node_uses_controlled_node_class_but_namespaced_role():
    DocumentNode(
        id="node:1",
        parent_ref=None,
        order_key="000000",
        node_class="root",
        role="text.chapter",
        provenance_ref="derivation:1",
    )

    with pytest.raises(ValidationError):
        DocumentNode(
            id="node:2",
            parent_ref="node:1",
            order_key="000010",
            node_class="genre_specific_magic",
            role="custom.magic",
            provenance_ref="derivation:1",
        )


def test_revision_schema_version_is_revision_authority_and_frozen_requires_gate_refs():
    document = CanonicalDocument(
        id="document:1",
        work_ref="work:1",
        edition_ref="edition:1",
        source_artifact_refs=("source:1",),
        revision_refs=("revision:1",),
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
    )
    assert not hasattr(document, "schema_version")

    with pytest.raises(ValidationError):
        CanonicalRevision(
            id="revision:1",
            canonical_document_ref=document.id,
            revision_number=1,
            schema_version="0.1",
            root_node_ref="node:root",
            node_registry_ref="registry:nodes",
            content_registry_ref="registry:content",
            entity_registry_ref="registry:entities",
            semantic_registry_ref="registry:semantic",
            structured_payload_registry_ref="registry:structured",
            provenance_manifest_ref="manifest:provenance",
            lifecycle_state="frozen",
            created_by_activity_ref="activity:1",
            created_at=datetime(2026, 9, 17, tzinfo=UTC),
        )

    revision = CanonicalRevision(
        id="revision:1",
        canonical_document_ref=document.id,
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
        validation_report_ref="validation:1",
        lifecycle_state="frozen",
        created_by_activity_ref="activity:1",
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
        content_digest="a" * 64,
    )
    assert revision.schema_version == "0.1"


def test_semantic_registry_is_membership_authority_not_reverse_refs_on_targets():
    annotation = Annotation(
        id="annotation:1",
        target_ref="fragment:1",
        annotation_type="linguistic.language",
        value={"language": "pt"},
        epistemic_status="explicit",
        provenance_ref="derivation:1",
    )
    relation = Relation(
        id="relation:1",
        subject_ref="node:cue",
        predicate="document.introduces",
        object_ref="node:speech",
        epistemic_status="explicit",
        provenance_ref="derivation:1",
    )
    registry = SemanticRegistry(
        id="registry:semantic",
        annotation_refs=(annotation.id,),
        relation_refs=(relation.id,),
    )

    assert registry.annotation_refs == (annotation.id,)
    assert registry.relation_refs == (relation.id,)
    assert "annotation_refs" not in ContentFragment.model_fields
    assert "relation_refs" not in DocumentNode.model_fields


def test_table_cells_reference_content_without_owning_fragments():
    cell = TableCell(
        id="cell:1",
        row=0,
        column=0,
        row_span=1,
        column_span=1,
        cell_role="body",
        content_refs=("fragment:011",),
    )
    payload = TablePayload(id="table:1", row_count=1, column_count=1, cells=(cell,))

    assert payload.cells[0].content_refs == ("fragment:011",)
    assert "owner_node_ref" not in TableCell.model_fields


def test_formula_payload_separates_source_and_reconstructed_representations():
    payload = FormulaPayload(
        id="formula:1",
        source_representation_refs=("evidence:visual-region",),
        reconstructed_representation_refs=("artifact:mathml",),
    )

    assert payload.source_representation_refs != payload.reconstructed_representation_refs


def test_unknown_fields_are_rejected_on_core_models():
    with pytest.raises(ValidationError):
        ContentFragment(
            id="fragment:1",
            owner_node_ref="node:1",
            order_key="000010",
            fragment_class="text",
            role="text.paragraph",
            surface=Surface(text="surface", language="pt"),
            provenance_ref="derivation:1",
            invented_core_field=True,
        )


def test_json_schema_snapshots_are_complete_and_deterministic():
    expected_files = {f"{name}.schema.json" for name in SCHEMA_MODELS}
    actual_files = {path.name for path in SCHEMA_ROOT.glob("*.schema.json")}
    assert actual_files == expected_files

    for name, model in sorted(SCHEMA_MODELS.items()):
        path = SCHEMA_ROOT / f"{name}.schema.json"
        first = schema_text(model)
        second = schema_text(model)
        assert first == second
        assert path.read_text(encoding="utf-8") == first
