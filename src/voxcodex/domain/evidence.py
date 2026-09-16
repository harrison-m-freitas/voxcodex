from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, FiniteFloat

from voxcodex.domain.common import ArtifactRef, FrozenModel


EvidenceClass = Literal[
    "physical_page",
    "region",
    "line",
    "text_span",
    "glyph_run",
    "asset",
    "syntax_unit",
]


class NativeGeometry(FrozenModel):
    coordinate_space: str
    bbox: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]


class NormalizedGeometry(FrozenModel):
    x0: FiniteFloat = Field(ge=0.0, le=1.0)
    y0: FiniteFloat = Field(ge=0.0, le=1.0)
    x1: FiniteFloat = Field(ge=0.0, le=1.0)
    y1: FiniteFloat = Field(ge=0.0, le=1.0)


class EvidenceUnit(FrozenModel):
    id: str
    snapshot_ref: str
    parent_ref: str | None = None
    evidence_class: EvidenceClass
    source_locator: dict[str, Any]
    surface: str | None = None
    presentation: dict[str, Any] | None = None
    native_geometry: NativeGeometry | None = None
    normalized_geometry: NormalizedGeometry | None = None
    native_payload: dict[str, Any] | None = None
    confidence_ref: str | None = None
    provenance_ref: str


class EvidencePartition(FrozenModel):
    id: str
    source_artifact_ref: str
    partition_key: str
    unit_refs: tuple[str, ...] = ()
    partition_digest: str
    provenance_ref: str


class EvidenceSnapshot(FrozenModel):
    id: str
    source_artifact_ref: str
    extraction_activity_ref: str
    extraction_profile_ref: str
    partition_refs: tuple[ArtifactRef, ...] = ()
    created_at: datetime
    snapshot_digest: str


class ExtractionProfile(FrozenModel):
    id: str
    adapter: str
    adapter_version: str
    options: dict[str, Any] = Field(default_factory=dict)
