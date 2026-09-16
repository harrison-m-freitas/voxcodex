from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import Field

from voxcodex.domain.common import ArtifactRef, FrozenModel


ReconstructionClass = Literal[
    "document",
    "division_candidate",
    "block_candidate",
    "line_group",
    "structured_candidate",
    "auxiliary_candidate",
]


class ReconstructionProfile(FrozenModel):
    id: str
    version: str
    baseline_tolerance: float = Field(default=0.02, gt=0.0, le=1.0)
    max_inline_gap: float = Field(default=0.08, gt=0.0, le=1.0)
    region_x_tolerance: float = Field(default=0.08, ge=0.0, le=1.0)
    layout_dehyphenation: bool = False
    classification_resolve_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    heading_min_relative_font_size: float = Field(default=1.20, gt=0.0)
    running_header_min_recurrence: int = Field(default=3, ge=2)
    speaker_cue_max_chars: int = Field(default=32, ge=1)


class ReconstructionUnit(FrozenModel):
    id: str
    reconstruction_snapshot_ref: str
    parent_ref: str | None = None
    order_key: str
    reconstruction_class: ReconstructionClass
    evidence_refs: tuple[ArtifactRef, ...] = ()
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence_ref: str | None = None
    provenance_ref: str


class OpenStructuralState(FrozenModel):
    open_units: tuple[str, ...] = ()
    pending_continuations: tuple[str, ...] = ()
    unresolved_boundaries: tuple[str, ...] = ()


class ReconstructionIssue(FrozenModel):
    id: str
    issue_type: str
    severity: str
    affected_refs: tuple[str, ...] = ()
    message: str
    confidence_ref: str | None = None
    suggested_action: str | None = None


class ReconstructionSnapshot(FrozenModel):
    id: str
    source_evidence_refs: tuple[ArtifactRef, ...]
    reconstruction_activity_ref: str
    reconstruction_profile_ref: str
    root_unit_refs: tuple[str, ...] = ()
    reconstruction_validation_ref: str | None = None
    created_at: datetime
    snapshot_digest: str


class ReconstructionContext(FrozenModel):
    snapshot_ref: str
    source_evidence_refs: tuple[ArtifactRef, ...]
    reconstruction_profile_ref: str


class StageResult(FrozenModel):
    units: tuple[ReconstructionUnit, ...] = ()
    issues: tuple[ReconstructionIssue, ...] = ()
    open_state: OpenStructuralState = Field(default_factory=OpenStructuralState)


class ReconstructionStage(Protocol):
    name: str
    version: str

    def run(
        self,
        context: ReconstructionContext,
        units: tuple[ReconstructionUnit, ...],
    ) -> StageResult: ...
