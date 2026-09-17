from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from voxcodex.domain.cbm.content import ContentFragment, Surface
from voxcodex.domain.cbm.document import CanonicalDocument, CanonicalRevision, DocumentNode
from voxcodex.domain.cbm.semantic import Annotation, Relation, SemanticRegistry
from voxcodex.domain.cbm.structured import FormulaPayload, TableCell


def test_content_fragment_requires_exactly_one_document_node_owner() -> None:
    with pytest.raises(ValidationError):
        ContentFragment(
            id="fragment:1",
            order_key="000001",
            fragment_class="text",
            role="text.paragraph",
            surface=Surface(text="alpha", language="pt"),
            provenance_ref="activity:1",
        )

    fragment = ContentFragment(
        id="fragment:1",
        owner_node_ref="node:paragraph",
        order_key="000001",
        fragment_class="text",
        role="text.paragraph",
        surface=Surface(text="alpha", language="pt"),
        provenance_ref="activity:1",
    )
    assert fragment.owner_node_ref == "node:paragraph"


def test_semantic_registry_is_membership_authority_without_reverse_refs() -> None:
    annotation = Annotation(
        id="annotation:1",
        target_ref="node:paragraph",
        annotation_type="linguistic.normalization",
        value={"normalized_text": "alpha"},
        epistemic_status="source_supported",
        evidence_refs=("anchor:1",),
        provenance_ref="activity:1",
    )
    relation = Relation(
        id="relation:1",
        subject_ref="node:paragraph",
        predicate="semantic.refers_to",
        object_ref="entity:1",
        epistemic_status="asserted",
        evidence_refs=("anchor:1",),
        provenance_ref="activity:1",
    )
    registry = SemanticRegistry(
        id="semantic-registry:1",
        annotation_refs=(annotation.id,),
        relation_refs=(relation.id,),
    )

    assert registry.annotation_refs == ("annotation:1",)
    assert registry.relation_refs == ("relation:1",)
    assert "annotation_refs" not in DocumentNode.model_fields
    assert "relation_refs" not in DocumentNode.model_fields


def test_table_cell_content_refs_are_non_owning() -> None:
    cell = TableCell(
        id="table-cell:1",
        row_index=0,
        column_index=0,
        row_span=1,
        column_span=1,
        content_refs=("fragment:1",),
    )

    assert cell.content_refs == ("fragment:1",)
    assert "owner_node_ref" not in TableCell.model_fields


def test_formula_payload_separates_source_and_reconstructed_representations() -> None:
    payload = FormulaPayload(
        id="formula:1",
        source_representation_refs=("anchor:formula",),
        reconstructed_representation_refs=("artifact:mathml",),
        fidelity_constraints=(),
    )

    assert payload.source_representation_refs == ("anchor:formula",)
    assert payload.reconstructed_representation_refs == ("artifact:mathml",)


def test_schema_version_belongs_to_revision_not_document() -> None:
    assert "schema_version" not in CanonicalDocument.model_fields
    assert CanonicalRevision.model_fields["schema_version"].is_required()


def test_cbm_models_are_frozen() -> None:
    node = DocumentNode(
        id="node:root",
        parent_ref=None,
        order_key="000000",
        node_class="root",
        role="text.root",
        provenance_ref="activity:1",
    )

    with pytest.raises(ValidationError):
        node.role = "text.chapter"


def test_canonical_revision_frozen_requirements_are_representable() -> None:
    revision = CanonicalRevision(
        id="revision:1",
        canonical_document_ref="document:1",
        revision_number=1,
        parent_revision_refs=(),
        schema_version="0.1",
        root_node_ref="node:root",
        node_registry_ref="registry:nodes",
        content_registry_ref="registry:content",
        entity_registry_ref="registry:entities",
        semantic_registry_ref="registry:semantic",
        structured_payload_registry_ref="registry:structured",
        source_mapping_manifest_ref="manifest:source",
        fidelity_manifest_ref=None,
        provenance_manifest_ref="manifest:provenance",
        validation_report_ref="validation:1",
        lifecycle_state="frozen",
        created_by_activity_ref="activity:materialize",
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
        content_digest="a" * 64,
    )

    assert revision.schema_version == "0.1"
    assert revision.source_mapping_manifest_ref == "manifest:source"
    assert revision.provenance_manifest_ref == "manifest:provenance"
    assert revision.validation_report_ref == "validation:1"
    assert revision.content_digest == "a" * 64
