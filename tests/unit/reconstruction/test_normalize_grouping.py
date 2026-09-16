from __future__ import annotations

from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionProfile
from voxcodex.reconstruction.blocks import group_visual_lines, group_visual_regions
from voxcodex.reconstruction.normalize import build_comparison_view


def _span(
    unit_id: str,
    surface: str,
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> EvidenceUnit:
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


def _profile() -> ReconstructionProfile:
    return ReconstructionProfile(
        id="reconstruction-profile:test",
        version="0.1.0",
        baseline_tolerance=0.02,
        max_inline_gap=0.08,
        region_x_tolerance=0.08,
    )


def test_comparison_view_normalizes_ligature_without_replacing_source_surface():
    unit = _span("evidence:ligature", "ﬁnal", x0=0.1, y0=0.1, x1=0.2, y1=0.12)

    view = build_comparison_view(unit)

    assert unit.surface == "ﬁnal"
    assert view.source_surface == "ﬁnal"
    assert view.comparison_surface == "final"


def test_comparison_view_does_not_perform_logical_dehyphenation():
    unit = _span("evidence:hyphen", "reconstru-\nção", x0=0.1, y0=0.1, x1=0.3, y1=0.15)

    view = build_comparison_view(unit)

    assert view.comparison_surface == "reconstru-\nção"


def test_same_baseline_spans_group_into_line_but_distant_spans_do_not():
    spans = (
        _span("evidence:a", "A", x0=0.10, y0=0.10, x1=0.15, y1=0.12),
        _span("evidence:b", "B", x0=0.17, y0=0.101, x1=0.22, y1=0.121),
        _span("evidence:c", "C", x0=0.10, y0=0.30, x1=0.15, y1=0.32),
    )

    lines = group_visual_lines(spans, _profile())

    assert len(lines) == 2
    assert lines[0].evidence_refs == ("evidence:a", "evidence:b")
    assert lines[1].evidence_refs == ("evidence:c",)


def test_interleaved_native_order_forms_two_visual_column_regions():
    spans = (
        _span("evidence:left-1", "L1", x0=0.10, y0=0.10, x1=0.35, y1=0.12),
        _span("evidence:right-1", "R1", x0=0.62, y0=0.10, x1=0.88, y1=0.12),
        _span("evidence:left-2", "L2", x0=0.10, y0=0.16, x1=0.35, y1=0.18),
        _span("evidence:right-2", "R2", x0=0.62, y0=0.16, x1=0.88, y1=0.18),
    )

    regions = group_visual_regions(spans, _profile())

    assert len(regions) == 2
    assert regions[0].evidence_refs == ("evidence:left-1", "evidence:left-2")
    assert regions[1].evidence_refs == ("evidence:right-1", "evidence:right-2")
