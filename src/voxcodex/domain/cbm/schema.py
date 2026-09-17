from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import TypeAdapter

from voxcodex.domain.cbm.content import ContentFragment, ContentRegistry, Surface
from voxcodex.domain.cbm.document import CanonicalDocument, CanonicalRevision, DocumentNode, NodeRegistry
from voxcodex.domain.cbm.provenance import (
    Derivation,
    FidelityConstraint,
    FidelityManifest,
    ProcessingActivity,
    ProvenanceManifest,
    Region,
    SourceAnchor,
    SourceLocator,
    SourceMappingManifest,
    TextRange,
)
from voxcodex.domain.cbm.semantic import (
    Annotation,
    Confidence,
    Entity,
    EntityRegistry,
    Relation,
    SemanticRegistry,
)
from voxcodex.domain.cbm.structured import (
    FormulaPayload,
    RoleProfile,
    StructuredPayloadRegistry,
    TableCell,
    TablePayload,
)
from voxcodex.domain.cbm.validation import ValidationCheck, ValidationPolicy, ValidationReport


Schema = dict[str, Any]
SchemaFactory = Callable[[], Schema]


def _adapter_schema(adapter: TypeAdapter[Any]) -> Schema:
    return adapter.json_schema()


_FACTORIES: tuple[tuple[str, SchemaFactory], ...] = (
    (
        "document.schema.json",
        lambda: _adapter_schema(
            TypeAdapter(CanonicalDocument | CanonicalRevision | DocumentNode | NodeRegistry)
        ),
    ),
    (
        "content.schema.json",
        lambda: _adapter_schema(TypeAdapter(ContentFragment | ContentRegistry | Surface)),
    ),
    (
        "semantic.schema.json",
        lambda: _adapter_schema(
            TypeAdapter(Annotation | Confidence | Entity | EntityRegistry | Relation | SemanticRegistry)
        ),
    ),
    (
        "structured.schema.json",
        lambda: _adapter_schema(
            TypeAdapter(
                FormulaPayload
                | RoleProfile
                | StructuredPayloadRegistry
                | TableCell
                | TablePayload
            )
        ),
    ),
    (
        "provenance.schema.json",
        lambda: _adapter_schema(
            TypeAdapter(
                Derivation
                | FidelityConstraint
                | FidelityManifest
                | ProcessingActivity
                | ProvenanceManifest
                | Region
                | SourceAnchor
                | SourceLocator
                | SourceMappingManifest
                | TextRange
            )
        ),
    ),
    (
        "validation.schema.json",
        lambda: _adapter_schema(TypeAdapter(ValidationCheck | ValidationPolicy | ValidationReport)),
    ),
)


def schema_snapshots() -> dict[str, Schema]:
    """Return the deterministic physical JSON Schema set for CBM v0.1."""
    return {filename: factory() for filename, factory in _FACTORIES}
