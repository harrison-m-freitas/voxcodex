from __future__ import annotations

from pydantic import Field

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.provenance import NormalizedRegion, SourceAnchor, SourceLocator
from voxcodex.domain.common import FrozenModel


class AnchorEvidence(FrozenModel):
    evidence_ref: str
    source_artifact_ref: str
    extraction_ref: str
    source_page_index: int | None = Field(default=None, ge=0)
    printed_page_label: str | None = None
    x0: float | None = Field(default=None, ge=0.0, le=1.0)
    y0: float | None = Field(default=None, ge=0.0, le=1.0)
    x1: float | None = Field(default=None, ge=0.0, le=1.0)
    y1: float | None = Field(default=None, ge=0.0, le=1.0)


def _region(evidence: AnchorEvidence) -> NormalizedRegion | None:
    coordinates = (evidence.x0, evidence.y0, evidence.x1, evidence.y1)
    if all(value is None for value in coordinates):
        return None
    if any(value is None for value in coordinates):
        raise ValueError("source anchor geometry requires x0, y0, x1, and y1 together")
    assert evidence.x0 is not None
    assert evidence.y0 is not None
    assert evidence.x1 is not None
    assert evidence.y1 is not None
    if evidence.x1 <= evidence.x0 or evidence.y1 <= evidence.y0:
        raise ValueError("source anchor geometry must have positive width and height")
    return NormalizedRegion(
        x=evidence.x0,
        y=evidence.y0,
        width=evidence.x1 - evidence.x0,
        height=evidence.y1 - evidence.y0,
    )


def build_source_anchors(
    object_ref: str,
    evidence: tuple[AnchorEvidence, ...],
) -> tuple[SourceAnchor, ...]:
    anchors: list[SourceAnchor] = []
    ordered = sorted(
        evidence,
        key=lambda item: (
            item.source_artifact_ref,
            item.source_page_index if item.source_page_index is not None else -1,
            item.evidence_ref,
        ),
    )
    for item in ordered:
        locator = SourceLocator(
            source_page_index=item.source_page_index,
            printed_page_label=item.printed_page_label,
            region=_region(item),
        )
        seed = {
            "object_ref": object_ref,
            "evidence_ref": item.evidence_ref,
            "source_artifact_ref": item.source_artifact_ref,
            "extraction_ref": item.extraction_ref,
            "locator": locator.model_dump(mode="json", exclude_none=True),
        }
        anchors.append(
            SourceAnchor(
                id=f"source-anchor:{sha256_bytes(canonical_json_bytes(seed))}",
                source_artifact_ref=item.source_artifact_ref,
                locator=locator,
                evidence_refs=(item.evidence_ref,),
                extraction_ref=item.extraction_ref,
            )
        )
    return tuple(anchors)
