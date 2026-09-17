from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from pydantic import Field

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionProfile


class TableCellCandidate(FrozenModel):
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    surface: str | None = None
    evidence_refs: tuple[ArtifactRef, ...]


class TableCandidate(FrozenModel):
    id: str
    row_count: int = Field(ge=1)
    column_count: int = Field(ge=1)
    cells: tuple[TableCellCandidate, ...]
    evidence_refs: tuple[ArtifactRef, ...]
    visual_region: NormalizedGeometry
    detection_basis: tuple[str, ...] = ("geometry_grid",)


class TechnicalBlockCandidate(FrozenModel):
    id: str
    evidence_refs: tuple[ArtifactRef, ...]
    visual_region: NormalizedGeometry
    detection_basis: tuple[str, ...]


class TerminalLineCandidate(FrozenModel):
    evidence_ref: ArtifactRef
    prompt: str | None = None
    input_text: str | None = None
    output_text: str | None = None


class TerminalCandidate(TechnicalBlockCandidate):
    lines: tuple[TerminalLineCandidate, ...]


class FormulaCandidate(FrozenModel):
    id: str
    evidence_refs: tuple[ArtifactRef, ...]
    visual_region: NormalizedGeometry
    symbolic_representation: str | None = None
    detection_basis: tuple[str, ...]


class FigurePanelCandidate(FrozenModel):
    evidence_ref: ArtifactRef
    visual_region: NormalizedGeometry
    blob_sha256: str | None = None


class FigureCandidate(FrozenModel):
    id: str
    evidence_refs: tuple[ArtifactRef, ...]
    visual_region: NormalizedGeometry
    panels: tuple[FigurePanelCandidate, ...]
    detection_basis: tuple[str, ...] = ("asset_geometry",)


class FootnoteLinkCandidate(FrozenModel):
    id: str
    marker_ref: ArtifactRef
    note_body_refs: tuple[ArtifactRef, ...]
    marker_surface: str
    note_surface: str
    detection_basis: tuple[str, ...]


class ReferenceCandidate(FrozenModel):
    id: str
    evidence_ref: ArtifactRef
    source_surface: str
    target_label: str
    resolved_target_ref: str | None = None
    detection_basis: tuple[str, ...] = ("reference_label_shape",)


def detect_table_candidate(
    units: Sequence[EvidenceUnit],
    profile: ReconstructionProfile,
) -> TableCandidate | None:
    positioned = [
        unit
        for unit in units
        if unit.normalized_geometry is not None and unit.surface is not None
    ]
    if len(positioned) < 4:
        return None

    row_centers = _cluster_axis(
        [_center_y(unit.normalized_geometry) for unit in positioned],
        profile.table_axis_tolerance,
    )
    column_centers = _cluster_axis(
        [_center_x(unit.normalized_geometry) for unit in positioned],
        profile.table_axis_tolerance,
    )
    if len(row_centers) < 2 or len(column_centers) < 2:
        return None

    cells: list[TableCellCandidate] = []
    occupied: set[tuple[int, int]] = set()
    for unit in positioned:
        geometry = unit.normalized_geometry
        assert geometry is not None
        row_index = _nearest_axis(_center_y(geometry), row_centers)
        column_index = _nearest_axis(_center_x(geometry), column_centers)
        coordinate = (row_index, column_index)
        if coordinate in occupied:
            return None
        occupied.add(coordinate)
        cells.append(
            TableCellCandidate(
                row_index=row_index,
                column_index=column_index,
                surface=unit.surface,
                evidence_refs=(_evidence_ref(unit),),
            )
        )

    cells.sort(key=lambda cell: (cell.row_index, cell.column_index))
    evidence_refs = tuple(ref for cell in cells for ref in cell.evidence_refs)
    region = _bbox([unit.normalized_geometry for unit in positioned if unit.normalized_geometry])
    candidate_id = _stable_id(
        "table-candidate",
        {
            "cells": [cell.model_dump(mode="json") for cell in cells],
            "row_count": len(row_centers),
            "column_count": len(column_centers),
        },
    )
    return TableCandidate(
        id=candidate_id,
        row_count=len(row_centers),
        column_count=len(column_centers),
        cells=tuple(cells),
        evidence_refs=evidence_refs,
        visual_region=region,
    )


def detect_terminal_candidate(units: Sequence[EvidenceUnit]) -> TerminalCandidate | None:
    positioned = [
        unit
        for unit in units
        if unit.surface is not None and unit.normalized_geometry is not None
    ]
    if not positioned:
        return None
    positioned.sort(key=lambda unit: (unit.normalized_geometry.y0, unit.normalized_geometry.x0, unit.id))

    has_monospace = any(_looks_monospace(unit) for unit in positioned)
    has_prompt = any(_split_prompt(unit.surface or "")[0] is not None for unit in positioned)
    if not has_prompt or (not has_monospace and len(positioned) < 2):
        return None

    lines: list[TerminalLineCandidate] = []
    for unit in positioned:
        surface = unit.surface or ""
        prompt, input_text = _split_prompt(surface)
        if prompt is not None:
            lines.append(
                TerminalLineCandidate(
                    evidence_ref=_evidence_ref(unit),
                    prompt=prompt,
                    input_text=input_text,
                )
            )
        else:
            lines.append(
                TerminalLineCandidate(
                    evidence_ref=_evidence_ref(unit),
                    output_text=surface,
                )
            )

    basis: list[str] = ["prompt_pattern"]
    if has_monospace:
        basis.insert(0, "monospace")
    basis.append("line_sequence")
    evidence_refs = tuple(line.evidence_ref for line in lines)
    region = _bbox([unit.normalized_geometry for unit in positioned if unit.normalized_geometry])
    return TerminalCandidate(
        id=_stable_id(
            "terminal-candidate",
            {
                "evidence_refs": [ref.model_dump(mode="json") for ref in evidence_refs],
                "lines": [line.model_dump(mode="json") for line in lines],
            },
        ),
        evidence_refs=evidence_refs,
        visual_region=region,
        detection_basis=tuple(basis),
        lines=tuple(lines),
    )


def detect_formula_candidate(
    units: Sequence[EvidenceUnit],
    *,
    symbolic_representation: str | None = None,
) -> FormulaCandidate | None:
    positioned = [unit for unit in units if unit.normalized_geometry is not None]
    if len(positioned) < 2:
        return None

    surfaces = tuple((unit.surface or "") for unit in positioned)
    math_shape = any(any(symbol in surface for symbol in "+−-=×÷∑∫√∞≤≥()[]{}") for surface in surfaces)
    y_centers = [_center_y(unit.normalized_geometry) for unit in positioned]
    script_geometry = max(y_centers) - min(y_centers) >= 0.02
    if not math_shape and not script_geometry:
        return None

    evidence_refs = tuple(_evidence_ref(unit) for unit in positioned)
    region = _bbox([unit.normalized_geometry for unit in positioned if unit.normalized_geometry])
    basis = []
    if math_shape:
        basis.append("math_glyph_shape")
    if script_geometry:
        basis.append("relative_vertical_geometry")
    if symbolic_representation is None:
        basis.append("visual_region_without_symbolic_parse")
    return FormulaCandidate(
        id=_stable_id(
            "formula-candidate",
            {
                "evidence_refs": [ref.model_dump(mode="json") for ref in evidence_refs],
                "symbolic_representation": symbolic_representation,
            },
        ),
        evidence_refs=evidence_refs,
        visual_region=region,
        symbolic_representation=symbolic_representation,
        detection_basis=tuple(basis),
    )


def build_figure_candidate(assets: Sequence[EvidenceUnit]) -> FigureCandidate:
    positioned = [
        unit
        for unit in assets
        if unit.evidence_class == "asset" and unit.normalized_geometry is not None
    ]
    if not positioned:
        raise ValueError("figure candidate requires at least one positioned asset evidence unit")
    positioned.sort(key=lambda unit: (unit.normalized_geometry.x0, unit.normalized_geometry.y0, unit.id))
    panels = tuple(
        FigurePanelCandidate(
            evidence_ref=_evidence_ref(unit),
            visual_region=unit.normalized_geometry,
            blob_sha256=str(unit.native_payload.get("blob_sha256"))
            if unit.native_payload.get("blob_sha256")
            else None,
        )
        for unit in positioned
    )
    evidence_refs = tuple(panel.evidence_ref for panel in panels)
    region = _bbox([panel.visual_region for panel in panels])
    return FigureCandidate(
        id=_stable_id(
            "figure-candidate",
            {"evidence_refs": [ref.model_dump(mode="json") for ref in evidence_refs]},
        ),
        evidence_refs=evidence_refs,
        visual_region=region,
        panels=panels,
    )


def link_footnote_candidate(
    marker: EvidenceUnit,
    note_body: EvidenceUnit,
) -> FootnoteLinkCandidate | None:
    marker_surface = (marker.surface or "").strip()
    note_surface = (note_body.surface or "").strip()
    if not marker_surface or not note_surface:
        return None
    escaped = re.escape(marker_surface)
    if not re.match(rf"^{escaped}(?:[.)]|\s)", note_surface):
        return None
    marker_ref = _evidence_ref(marker)
    body_ref = _evidence_ref(note_body)
    return FootnoteLinkCandidate(
        id=_stable_id(
            "footnote-link",
            {
                "marker_ref": marker_ref.model_dump(mode="json"),
                "body_ref": body_ref.model_dump(mode="json"),
            },
        ),
        marker_ref=marker_ref,
        note_body_refs=(body_ref,),
        marker_surface=marker_surface,
        note_surface=note_surface,
        detection_basis=("matching_marker_shape", "separate_marker_and_body_evidence"),
    )


def detect_reference_candidate(unit: EvidenceUnit) -> ReferenceCandidate | None:
    surface = unit.surface or ""
    match = re.search(
        r"\b(?:Figura|Figure|Fig\.|Tabela|Table)\s+\d+(?:\.\d+)*",
        surface,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    evidence_ref = _evidence_ref(unit)
    target_label = match.group(0)
    return ReferenceCandidate(
        id=_stable_id(
            "reference-candidate",
            {
                "evidence_ref": evidence_ref.model_dump(mode="json"),
                "target_label": target_label,
            },
        ),
        evidence_ref=evidence_ref,
        source_surface=surface,
        target_label=target_label,
    )


def resolve_reference_candidate(
    candidate: ReferenceCandidate,
    targets: Mapping[str, str],
) -> ReferenceCandidate:
    return candidate.model_copy(
        update={"resolved_target_ref": targets.get(candidate.target_label)},
    )


def _evidence_ref(unit: EvidenceUnit) -> ArtifactRef:
    return ArtifactRef(
        id=unit.id,
        digest=sha256_bytes(unit.model_dump_json().encode("utf-8")),
        kind="evidence_unit",
    )


def _cluster_axis(values: Sequence[float], tolerance: float) -> tuple[float, ...]:
    clusters: list[list[float]] = []
    for value in sorted(values):
        if not clusters or abs(value - (sum(clusters[-1]) / len(clusters[-1]))) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return tuple(sum(cluster) / len(cluster) for cluster in clusters)


def _nearest_axis(value: float, centers: Sequence[float]) -> int:
    return min(range(len(centers)), key=lambda index: abs(value - centers[index]))


def _split_prompt(surface: str) -> tuple[str | None, str | None]:
    match = re.match(r"^\s*([$#>])\s*(.*)$", surface)
    if match is None:
        return None, None
    return match.group(1), match.group(2)


def _looks_monospace(unit: EvidenceUnit) -> bool:
    font = str(unit.presentation.get("font", "")).lower()
    return any(token in font for token in ("mono", "courier", "code", "fixed"))


def _center_x(geometry: NormalizedGeometry) -> float:
    return (geometry.x0 + geometry.x1) / 2.0


def _center_y(geometry: NormalizedGeometry) -> float:
    return (geometry.y0 + geometry.y1) / 2.0


def _bbox(geometries: Sequence[NormalizedGeometry]) -> NormalizedGeometry:
    if not geometries:
        raise ValueError("candidate requires normalized geometry")
    return NormalizedGeometry(
        x0=min(geometry.x0 for geometry in geometries),
        y0=min(geometry.y0 for geometry in geometries),
        x1=max(geometry.x1 for geometry in geometries),
        y1=max(geometry.y1 for geometry in geometries),
    )


def _stable_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(payload))}"
