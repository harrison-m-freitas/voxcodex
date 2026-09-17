from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from voxcodex.domain.common import FrozenModel


EpistemicStatus = Literal["explicit", "derived", "inferred", "human_asserted"]
EntityClass = Literal[
    "person",
    "character",
    "organization",
    "place",
    "concept",
    "work",
    "artifact",
    "software",
    "other",
]


class Entity(FrozenModel):
    id: str
    entity_class: EntityClass
    canonical_label: str
    aliases: tuple[str, ...] = ()
    provenance_ref: str


class Annotation(FrozenModel):
    id: str
    target_ref: str
    annotation_type: str = Field(pattern=r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$")
    value: dict[str, Any]
    epistemic_status: EpistemicStatus
    evidence_refs: tuple[str, ...] = ()
    confidence_ref: str | None = None
    provenance_ref: str

    @model_validator(mode="after")
    def inferred_requires_evidence(self) -> "Annotation":
        if self.epistemic_status == "inferred" and not self.evidence_refs:
            raise ValueError("inferred annotation requires evidence_refs")
        return self


class Relation(FrozenModel):
    id: str
    subject_ref: str
    predicate: str = Field(pattern=r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$")
    object_ref: str
    epistemic_status: EpistemicStatus
    evidence_refs: tuple[str, ...] = ()
    confidence_ref: str | None = None
    provenance_ref: str

    @model_validator(mode="after")
    def inferred_requires_evidence(self) -> "Relation":
        if self.epistemic_status == "inferred" and not self.evidence_refs:
            raise ValueError("inferred relation requires evidence_refs")
        return self


class EntityRegistry(FrozenModel):
    id: str
    entity_refs: tuple[str, ...] = ()


class SemanticRegistry(FrozenModel):
    id: str
    annotation_refs: tuple[str, ...] = ()
    relation_refs: tuple[str, ...] = ()
