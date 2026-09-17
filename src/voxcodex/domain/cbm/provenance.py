from __future__ import annotations

from pydantic import Field

from voxcodex.domain.common import FrozenModel


class NormalizedRegion(FrozenModel):
    coordinate_space: str = "normalized"
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)


class TextRange(FrozenModel):
    evidence_ref: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class SourceLocator(FrozenModel):
    source_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    region: NormalizedRegion | None = None
    text_range: TextRange | None = None


class SourceAnchor(FrozenModel):
    id: str
    source_artifact_ref: str
    locator: SourceLocator
    evidence_refs: tuple[str, ...] = ()
    extraction_ref: str
    confidence_ref: str | None = None


class SourceMappingManifest(FrozenModel):
    id: str
    source_anchor_refs: tuple[str, ...] = ()


class FidelityManifest(FrozenModel):
    id: str
    object_refs: tuple[str, ...] = ()


class ProvenanceManifest(FrozenModel):
    id: str
    derivation_refs: tuple[str, ...] = ()
    activity_refs: tuple[str, ...] = ()
