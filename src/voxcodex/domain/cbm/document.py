from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from voxcodex.domain.common import FrozenModel


RevisionLifecycle = Literal["building", "validated", "frozen", "superseded", "invalid"]


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
    lifecycle_state: RevisionLifecycle
    created_by_activity_ref: str
    created_at: datetime
    content_digest: str | None = None

    @model_validator(mode="after")
    def validate_frozen_requirements(self) -> "CanonicalRevision":
        if self.lifecycle_state == "frozen":
            missing = [
                field_name
                for field_name in (
                    "source_mapping_manifest_ref",
                    "provenance_manifest_ref",
                    "validation_report_ref",
                    "content_digest",
                )
                if getattr(self, field_name) is None
            ]
            if missing:
                raise ValueError(
                    "frozen revision requires " + ", ".join(missing)
                )
        return self
