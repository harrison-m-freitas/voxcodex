from __future__ import annotations

from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionProfile
from voxcodex.reconstruction.structured import (
    build_figure_candidate,
    detect_formula_candidate,
    detect_reference_candidate,
    detect_table_candidate,
    detect_terminal_candidate,
    link_footnote_candidate,
    resolve_reference_candidate,
)


def _unit(
    unit_id: str,
    surface: str | None,
    *,
    evidence_class: str = "text_span",
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    font: str | None = None,
) -> EvidenceUnit:
    return EvidenceUnit(
        id=unit_id,
        snapshot_ref="snapshot:evidence:structured",
        parent_ref="evidence:page:0",
        evidence_class=evidence_class,
        source_locator={"page_index": 0},
        surface=surface,
        presentation={"font": font} if font else {},
        normalized_geometry=NormalizedGeometry(x0=x0, y0=y0, x1=x1, y1=y1),
        native_payload={"blob_sha256": "f" * 64} if evidence_class == "asset" else {},
        provenance_ref="derivation:evidence:structured",
    )


def _profile() -> ReconstructionProfile:
    return ReconstructionProfile(
        id="reconstruction-profile:structured",
        version="0.1.0",
        table_axis_tolerance=0.04,
    )


def test_table_candidate_preserves_row_column_topology_from_geometry():
    units = (
        _unit("evidence:r0c0", "Nome", x0=0.10, y0=0.10, x1=0.30, y1=0.13),
        _unit("evidence:r0c1", "Valor", x0=0.55, y0=0.10, x1=0.75, y1=0.13),
        _unit("evidence:r1c0", "Alpha", x0=0.10, y0=0.20, x1=0.30, y1=0.23),
        _unit("evidence:r1c1", "011", x0=0.55, y0=0.20, x1=0.75, y1=0.23),
    )

    candidate = detect_table_candidate(units, _profile())

    assert candidate is not None
    assert candidate.row_count == 2
    assert candidate.column_count == 2
    assert {(cell.row_index, cell.column_index, cell.surface) for cell in candidate.cells} == {
        (0, 0, "Nome"),
        (0, 1, "Valor"),
        (1, 0, "Alpha"),
        (1, 1, "011"),
    }
    assert next(cell for cell in candidate.cells if cell.surface == "011").surface == "011"


def test_terminal_candidate_distinguishes_prompt_input_and_output_without_exact_commands():
    units = (
        _unit("evidence:t0", "$ qx-run --probe", x0=0.10, y0=0.10, x1=0.50, y1=0.13, font="MonoSynthetic"),
        _unit("evidence:t1", "synthetic-result", x0=0.10, y0=0.15, x1=0.45, y1=0.18, font="MonoSynthetic"),
        _unit("evidence:t2", "# nx-check", x0=0.10, y0=0.20, x1=0.40, y1=0.23, font="MonoSynthetic"),
    )

    candidate = detect_terminal_candidate(units)

    assert candidate is not None
    assert candidate.lines[0].prompt == "$"
    assert candidate.lines[0].input_text == "qx-run --probe"
    assert candidate.lines[0].output_text is None
    assert candidate.lines[1].prompt is None
    assert candidate.lines[1].input_text is None
    assert candidate.lines[1].output_text == "synthetic-result"
    assert candidate.lines[2].prompt == "#"
    assert candidate.lines[2].input_text == "nx-check"
    assert "monospace" in candidate.detection_basis
    assert "prompt_pattern" in candidate.detection_basis


def test_formula_candidate_preserves_visual_region_without_symbolic_parse():
    units = (
        _unit("evidence:fx", "x", x0=0.20, y0=0.30, x1=0.25, y1=0.35),
        _unit("evidence:f2", "2", x0=0.25, y0=0.26, x1=0.28, y1=0.30),
        _unit("evidence:fplus", "+", x0=0.31, y0=0.30, x1=0.34, y1=0.35),
        _unit("evidence:fy", "y", x0=0.37, y0=0.30, x1=0.42, y1=0.35),
    )

    candidate = detect_formula_candidate(units, symbolic_representation=None)

    assert candidate is not None
    assert candidate.symbolic_representation is None
    assert tuple(ref.id for ref in candidate.evidence_refs) == (
        "evidence:fx",
        "evidence:f2",
        "evidence:fplus",
        "evidence:fy",
    )
    assert candidate.visual_region.x0 == 0.20
    assert candidate.visual_region.y0 == 0.26
    assert candidate.visual_region.x1 == 0.42
    assert candidate.visual_region.y1 == 0.35


def test_figure_candidate_preserves_asset_regions_and_blob_refs():
    assets = (
        _unit("evidence:asset-a", None, evidence_class="asset", x0=0.10, y0=0.40, x1=0.45, y1=0.70),
        _unit("evidence:asset-b", None, evidence_class="asset", x0=0.50, y0=0.40, x1=0.90, y1=0.70),
    )

    candidate = build_figure_candidate(assets)

    assert len(candidate.panels) == 2
    assert candidate.panels[0].blob_sha256 == "f" * 64
    assert candidate.visual_region.x0 == 0.10
    assert candidate.visual_region.x1 == 0.90


def test_footnote_link_candidate_keeps_marker_and_body_separate():
    marker = _unit("evidence:marker", "7", x0=0.40, y0=0.20, x1=0.42, y1=0.22)
    body = _unit("evidence:note", "7 Nota sintética.", x0=0.10, y0=0.82, x1=0.70, y1=0.87)

    candidate = link_footnote_candidate(marker, body)

    assert candidate is not None
    assert candidate.marker_ref.id == marker.id
    assert candidate.note_body_refs[0].id == body.id
    assert candidate.marker_surface == "7"
    assert candidate.note_surface == "7 Nota sintética."


def test_reference_detection_is_distinct_from_target_resolution():
    unit = _unit(
        "evidence:reference",
        "Consulte a Figura 9.7 para detalhes.",
        x0=0.10,
        y0=0.50,
        x1=0.70,
        y1=0.54,
    )

    detected = detect_reference_candidate(unit)

    assert detected is not None
    assert detected.target_label == "Figura 9.7"
    assert detected.resolved_target_ref is None
    resolved = resolve_reference_candidate(detected, {"Figura 9.7": "figure:synthetic-97"})
    assert detected.resolved_target_ref is None
    assert resolved.resolved_target_ref == "figure:synthetic-97"
