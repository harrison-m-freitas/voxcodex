from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.cbm.provenance import FidelityConstraint


NodeClass = Literal["root", "division", "block", "structured_block", "declaration", "asset"]
LifecycleState = Literal["building", "validated", "frozen", "superseded", "invalid"]


class CanonicalDocument(FrozenModel):
    id: str
    work_ref: str
    edition_ref: str
    source_artifact_refs: tuple[str, ...] = Field(min_length=1)
    active_revision_ref: str | None = None
    revision_refs: tuple[str, ...] = Field(min_length=1)
    created_at: datetime


class CanonicalRevision(FrozenModel):
    id: str
    canonical_document_ref: str
    revision_number: int = Field(ge=1)
    parent_revision_refs: tuple[str, ...] = ()
    schema_version: str
    root_node_ref: str
    node_registry_ref: str
    content_registry_ref: str
    entity_registry_ref: str
    semantic_registry_ref: str
    structured_payload_registry_ref: str
    source_mapping_manifest_ref: str | None = None
    fidelity_manifest_ref: str | None = None
    provenance_manifest_ref: str | None = None
    validation_report_ref: str | None = None
    lifecycle_state: LifecycleState
    created_by_activity_ref: str
    created_at: datetime
    content_digest: str | None = None

    @model_validator(mode="after")
    def frozen_revision_has_authorizing_artifacts(self) -> "CanonicalRevision":
        if self.lifecycle_state != "frozen":
            return self
        missing = [
            name
            for name in (
                "source_mapping_manifest_ref",
                "provenance_manifest_ref",
                "validation_report_ref",
                "content_digest",
            )
            if getattr(self, name) is None
        ]
        if missing:
            raise ValueError(f"frozen revision missing required artifacts: {', '.join(missing)}")
        return self


class DocumentNode(FrozenModel):
    id: str
    parent_ref: str | None = None
    order_key: str
    node_class: NodeClass
    role: str
    content_refs: tuple[str, ...] = ()
    child_refs: tuple[str, ...] = ()
    structured_payload_ref: str | None = None
    source_anchor_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()
    provenance_ref: str

    @model_validator(mode="after")
    def non_root_has_logical_parent(self) -> "DocumentNode":
        if self.node_class == "root" and self.parent_ref is not None:
            raise ValueError("root node cannot have parent_ref")
        if self.node_class != "root" and self.parent_ref is None:
            raise ValueError("non-root DocumentNode requires parent_ref")
        if "." not in self.role:
            raise ValueError("role must be namespaced")
        return self


class NodeRegistry(FrozenModel):
    id: str
    node_refs: tuple[str, ...] = ()
