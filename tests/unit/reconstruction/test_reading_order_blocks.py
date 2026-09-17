from __future__ import annotations

from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionProfile
from voxcodex.reconstruction.blocks import (
    VisualLineCandidate,
    VisualRegionCandidate,
    reconstruct_text_block,
)
from voxcodex.reconstruction.reading_order import solve_reading_order


def _span(unit_id: str, surface: str, *, x0: float, y0: float, x1: float, y1: float) -> EvidenceUnit:
    return EvidenceUnit(
        id=unit_id,
        snapshot_ref="snapshot:evidence:test",
        parent_ref="evidence:page:0",
        evidence_class="text_span",
        source_locator={"page_index": 0},
        surface=surface,
        normalized_geometry=NormalizedGeometry(x0=x0, y0=y0, x1=x1, y1=y1),
        provenance_ref="derivation:evidence:test",
    )


def _line(line_id: str, evidence_ref: str, *, x0: float, y0: float, x1: float, y1: float) -> VisualLineCandidate:
    return VisualLineCandidate(
        id=line_id,
        evidence_refs=(evidence_ref,),
        bbox=NormalizedGeometry(x0=x0, y0=y0, x1=x1, y1=y1),
    )


def test_reading_order_uses_region_topology_before_native_interleaving():
    left_1 = _line("line:left-1", "evidence:left-1", x0=0.10, y0=0.10, x1=0.35, y1=0.12)
    left_2 = _line("line:left-2", "evidence:left-2", x0=0.10, y0=0.20, x1=0.35, y1=0.22)
    right_1 = _line("line:right-1", "evidence:right-1", x0=0.62, y0=0.10, x1=0.88, y1=0.12)
    right_2 = _line("line:right-2", "evidence:right-2", x0=0.62, y0=0.20, x1=0.88, y1=0.22)

    # Deliberately supply right before left to ensure native/container order is not authoritative.
    regions = (
        VisualRegionCandidate(
            id="region:right",
            line_refs=(right_1.id, right_2.id),
            evidence_refs=("evidence:right-1", "evidence:right-2"),
            bbox=NormalizedGeometry(x0=0.62, y0=0.10, x1=0.88, y1=0.22),
        ),
        VisualRegionCandidate(
            id="region:left",
            line_refs=(left_1.id, left_2.id),
            evidence_refs=("evidence:left-1", "evidence:left-2"),
            bbox=NormalizedGeometry(x0=0.10, y0=0.10, x1=0.35, y1=0.22),
        ),
    )
    lines = {line.id: line for line in (left_1, left_2, right_1, right_2)}

    decision = solve_reading_order(regions, lines)

    assert decision.evidence_refs == (
        "evidence:left-1",
        "evidence:left-2",
        "evidence:right-1",
        "evidence:right-2",
    )
    assert decision.confidence_basis == "region_topology_then_line_yx"


def test_layout_dehyphenation_preserves_source_fragments_and_records_derivation():
    first = _span("evidence:first", "reconstru-", x0=0.10, y0=0.10, x1=0.30, y1=0.12)
    second = _span("evidence:second", "ção", x0=0.10, y0=0.14, x1=0.20, y1=0.16)
    profile = ReconstructionProfile(
        id="reconstruction-profile:test",
        version="0.1.0",
        layout_dehyphenation=True,
    )

    block = reconstruct_text_block((first, second), profile)

    assert block.source_surfaces == ("reconstru-", "ção")
    assert block.reconstructed_text == "reconstrução"
    assert len(block.derivations) == 1
    assert block.derivations[0].kind == "layout_dehyphenation"
    assert block.derivations[0].evidence_refs == ("evidence:first", "evidence:second")


def test_dehyphenation_is_conservative_when_continuation_is_not_lexical():
    first = _span("evidence:first", "item-", x0=0.10, y0=0.10, x1=0.20, y1=0.12)
    second = _span("evidence:second", "42", x0=0.10, y0=0.14, x1=0.15, y1=0.16)
    profile = ReconstructionProfile(
        id="reconstruction-profile:test",
        version="0.1.0",
        layout_dehyphenation=True,
    )

    block = reconstruct_text_block((first, second), profile)

    assert block.reconstructed_text == "item- 42"
    assert block.derivations == ()
