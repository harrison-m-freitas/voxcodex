from __future__ import annotations

from collections.abc import Mapping, Sequence

from voxcodex.domain.common import FrozenModel
from voxcodex.reconstruction.blocks import VisualLineCandidate, VisualRegionCandidate


class ReadingOrderDecision(FrozenModel):
    evidence_refs: tuple[str, ...]
    region_refs: tuple[str, ...]
    confidence_basis: str


def solve_reading_order(
    regions: Sequence[VisualRegionCandidate],
    lines_by_id: Mapping[str, VisualLineCandidate],
) -> ReadingOrderDecision:
    ordered_regions = sorted(
        regions,
        key=lambda region: (region.bbox.x0, region.bbox.y0, region.id),
    )
    evidence_refs: list[str] = []

    for region in ordered_regions:
        lines = [lines_by_id[line_ref] for line_ref in region.line_refs]
        ordered_lines = sorted(
            lines,
            key=lambda line: (line.bbox.y0, line.bbox.x0, line.id),
        )
        for line in ordered_lines:
            evidence_refs.extend(line.evidence_refs)

    return ReadingOrderDecision(
        evidence_refs=tuple(evidence_refs),
        region_refs=tuple(region.id for region in ordered_regions),
        confidence_basis="region_topology_then_line_yx",
    )
