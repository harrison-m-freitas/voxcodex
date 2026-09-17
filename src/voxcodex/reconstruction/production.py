from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import median
from typing import Any

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceUnit
from voxcodex.domain.reconstruction import (
    ReconstructionContext,
    ReconstructionProfile,
    ReconstructionUnit,
    StageResult,
)
from voxcodex.materialization.mappings import RoleProfileRegistry
from voxcodex.reconstruction.blocks import group_visual_lines, group_visual_regions
from voxcodex.reconstruction.classifiers import BlockFeatures, classify_block
from voxcodex.reconstruction.structured import (
    build_figure_candidate,
    detect_formula_candidate,
    detect_table_candidate,
    detect_terminal_candidate,
)


_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "m2-pipeline-v0.1.json"
_SIGNIFICANT_ROOT_CLASSES = {"syntax_unit", "text_span", "line", "asset", "glyph_run"}


@dataclass(frozen=True, slots=True)
class _PendingUnit:
    sort_key: tuple[object, ...]
    reconstruction_class: str
    role: str
    evidence_refs: tuple[ArtifactRef, ...]
    properties: dict[str, Any]
    provenance_ref: str


def _load_config() -> dict[str, Any]:
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("m2 pipeline config must be a JSON object")
    return data


def production_reconstruction_profile() -> ReconstructionProfile:
    config = _load_config()
    values = config.get("reconstruction")
    if not isinstance(values, dict):
        raise ValueError("m2 pipeline reconstruction config is missing")
    return ReconstructionProfile(
        id="reconstruction-profile:m2-production:v0.1",
        version=str(config.get("version", "0.1.0")),
        baseline_tolerance=float(values["baseline_tolerance"]),
        max_inline_gap=float(values["max_inline_gap"]),
        region_x_tolerance=float(values["region_x_tolerance"]),
        layout_dehyphenation=bool(values["layout_dehyphenation"]),
        classification_resolve_threshold=float(
            values["classification_resolve_threshold"]
        ),
        heading_min_relative_font_size=float(
            values["heading_min_relative_font_size"]
        ),
        running_header_min_recurrence=int(
            values["running_header_min_recurrence"]
        ),
        speaker_cue_max_chars=int(values["speaker_cue_max_chars"]),
        table_axis_tolerance=float(values["table_axis_tolerance"]),
    )


class ProductionEvidenceStage:
    name = "m2-production-structure"
    version = "0.1.0"

    def __init__(
        self,
        evidence_units: tuple[EvidenceUnit, ...],
        profile: ReconstructionProfile,
    ) -> None:
        self.evidence_units = evidence_units
        self.profile = profile

    def run(
        self,
        context: ReconstructionContext,
        units: tuple[ReconstructionUnit, ...],
    ) -> StageResult:
        del units
        root = _root_unit(context, self.evidence_units)
        if any(unit.evidence_class == "syntax_unit" for unit in self.evidence_units):
            pending = _markdown_pending(self.evidence_units)
        else:
            pending = _pdf_pending(self.evidence_units, self.profile)

        children: list[ReconstructionUnit] = []
        for index, item in enumerate(sorted(pending, key=lambda value: value.sort_key), start=1):
            stable_seed = {
                "snapshot_ref": context.snapshot_ref,
                "role": item.role,
                "order_index": index,
                "evidence_refs": [ref.id for ref in item.evidence_refs],
            }
            child_id = (
                "reconstruction-unit:"
                + sha256_bytes(canonical_json_bytes(stable_seed))
            )
            children.append(
                ReconstructionUnit(
                    id=child_id,
                    reconstruction_snapshot_ref=context.snapshot_ref,
                    parent_ref=root.id,
                    order_key=f"{index:06d}",
                    reconstruction_class=item.reconstruction_class,  # type: ignore[arg-type]
                    evidence_refs=item.evidence_refs,
                    properties={"resolved_role": item.role, **item.properties},
                    provenance_ref=item.provenance_ref,
                )
            )

        return StageResult(units=(root, *children))


def _root_unit(
    context: ReconstructionContext,
    evidence_units: tuple[EvidenceUnit, ...],
) -> ReconstructionUnit:
    significant = next(
        (
            unit
            for unit in evidence_units
            if unit.evidence_class in _SIGNIFICANT_ROOT_CLASSES
        ),
        None,
    )
    evidence_refs = (_evidence_ref(significant),) if significant is not None else ()
    root_seed = {
        "snapshot_ref": context.snapshot_ref,
        "role": "document.root",
        "evidence_ref": significant.id if significant is not None else None,
    }
    return ReconstructionUnit(
        id="reconstruction-unit:" + sha256_bytes(canonical_json_bytes(root_seed)),
        reconstruction_snapshot_ref=context.snapshot_ref,
        parent_ref=None,
        order_key="000000",
        reconstruction_class="document",
        evidence_refs=evidence_refs,
        properties={"resolved_role": "document.root"},
        provenance_ref=(
            significant.provenance_ref
            if significant is not None
            else f"derivation:reconstruction-root:{context.snapshot_ref}"
        ),
    )


def _markdown_pending(
    evidence_units: tuple[EvidenceUnit, ...],
) -> tuple[_PendingUnit, ...]:
    config = _load_config()
    raw_roles = config.get("markdown_roles")
    if not isinstance(raw_roles, dict):
        raise ValueError("m2 pipeline markdown_roles config is missing")
    roles = {str(key): str(value) for key, value in raw_roles.items()}
    registry = RoleProfileRegistry.v01_defaults()

    pending: list[_PendingUnit] = []
    for unit in evidence_units:
        if unit.evidence_class != "syntax_unit":
            continue
        payload = unit.native_payload or {}
        token_type = str(payload.get("token_type", ""))
        role = roles.get(token_type)
        if role is None or registry.resolve(role) is None:
            continue
        line_start = unit.source_locator.get("line_start", 0)
        pending.append(
            _PendingUnit(
                sort_key=(int(line_start) if isinstance(line_start, int) else 0, unit.id),
                reconstruction_class="block_candidate",
                role=role,
                evidence_refs=(_evidence_ref(unit),),
                properties={"surface": unit.surface or "", "token_type": token_type},
                provenance_ref=unit.provenance_ref,
            )
        )
    return tuple(pending)


def _pdf_pending(
    evidence_units: tuple[EvidenceUnit, ...],
    profile: ReconstructionProfile,
) -> tuple[_PendingUnit, ...]:
    pending: list[_PendingUnit] = []
    registry = RoleProfileRegistry.v01_defaults()

    pages = sorted({_page_index(unit) for unit in evidence_units})
    for page_index in pages:
        page_units = tuple(
            unit for unit in evidence_units if _page_index(unit) == page_index
        )
        spans = tuple(
            unit
            for unit in page_units
            if unit.evidence_class == "text_span"
            and unit.surface
            and unit.normalized_geometry is not None
        )
        glyphs = tuple(
            unit
            for unit in page_units
            if unit.evidence_class == "glyph_run"
            and unit.surface
            and unit.normalized_geometry is not None
        )
        assets = tuple(
            unit
            for unit in page_units
            if unit.evidence_class == "asset"
            and unit.normalized_geometry is not None
        )

        consumed_span_ids: set[str] = set()

        if assets:
            figure = build_figure_candidate(assets)
            pending.append(
                _PendingUnit(
                    sort_key=(
                        page_index,
                        figure.visual_region.y0,
                        figure.visual_region.x0,
                        "figure",
                        figure.id,
                    ),
                    reconstruction_class="structured_candidate",
                    role="structured.figure",
                    evidence_refs=figure.evidence_refs,
                    properties={
                        "figure_candidate": figure.model_dump(mode="json")
                    },
                    provenance_ref=f"derivation:figure:{figure.id}",
                )
            )

        if glyphs:
            formula = detect_formula_candidate(glyphs, symbolic_representation=None)
            if formula is not None and "math_glyph_shape" in formula.detection_basis:
                pending.append(
                    _PendingUnit(
                        sort_key=(
                            page_index,
                            formula.visual_region.y0,
                            formula.visual_region.x0,
                            "formula",
                            formula.id,
                        ),
                        reconstruction_class="structured_candidate",
                        role="structured.formula",
                        evidence_refs=formula.evidence_refs,
                        properties={
                            "formula_candidate": formula.model_dump(mode="json")
                        },
                        provenance_ref=f"derivation:formula:{formula.id}",
                    )
                )

        if spans:
            by_id = {unit.id: unit for unit in spans}
            for region in group_visual_regions(spans, profile):
                region_units = tuple(
                    by_id[ref]
                    for ref in region.evidence_refs
                    if ref in by_id and ref not in consumed_span_ids
                )
                if not region_units:
                    continue

                terminal = detect_terminal_candidate(region_units)
                if terminal is not None:
                    pending.append(
                        _PendingUnit(
                            sort_key=(
                                page_index,
                                terminal.visual_region.y0,
                                terminal.visual_region.x0,
                                "terminal",
                                terminal.id,
                            ),
                            reconstruction_class="block_candidate",
                            role="technical.terminal_transcript",
                            evidence_refs=terminal.evidence_refs,
                            properties={
                                "terminal_candidate": terminal.model_dump(mode="json")
                            },
                            provenance_ref=f"derivation:terminal:{terminal.id}",
                        )
                    )
                    consumed_span_ids.update(ref.id for ref in terminal.evidence_refs)
                    continue

                table = detect_table_candidate(region_units, profile)
                if table is not None:
                    pending.append(
                        _PendingUnit(
                            sort_key=(
                                page_index,
                                table.visual_region.y0,
                                table.visual_region.x0,
                                "table",
                                table.id,
                            ),
                            reconstruction_class="structured_candidate",
                            role="structured.table",
                            evidence_refs=table.evidence_refs,
                            properties={
                                "table_candidate": table.model_dump(mode="json")
                            },
                            provenance_ref=f"derivation:table:{table.id}",
                        )
                    )
                    consumed_span_ids.update(ref.id for ref in table.evidence_refs)

            remaining = tuple(
                unit for unit in spans if unit.id not in consumed_span_ids
            )
            if remaining:
                page_sizes = [
                    _font_size(unit)
                    for unit in remaining
                    if _font_size(unit) is not None
                ]
                baseline_size = median(page_sizes) if page_sizes else 1.0
                remaining_by_id = {unit.id: unit for unit in remaining}
                for line in group_visual_lines(remaining, profile):
                    line_units = tuple(
                        remaining_by_id[ref]
                        for ref in line.evidence_refs
                        if ref in remaining_by_id
                    )
                    if not line_units:
                        continue
                    surface = " ".join(
                        (unit.surface or "").strip()
                        for unit in line_units
                        if (unit.surface or "").strip()
                    ).strip()
                    if not surface:
                        continue

                    line_sizes = [
                        _font_size(unit)
                        for unit in line_units
                        if _font_size(unit) is not None
                    ]
                    line_size = median(line_sizes) if line_sizes else baseline_size
                    relative_font_size = (
                        line_size / baseline_size if baseline_size > 0 else 1.0
                    )
                    fonts = [_font_name(unit) for unit in line_units]
                    features = BlockFeatures(
                        text=surface,
                        relative_font_size=max(relative_font_size, 0.01),
                        is_bold=any("bold" in font for font in fonts),
                        is_monospace=any(
                            any(token in font for token in ("mono", "courier", "code", "fixed"))
                            for font in fonts
                        ),
                        is_uppercase=surface == surface.upper()
                        and any(ch.isalpha() for ch in surface),
                        normalized_y=line.bbox.y0,
                        line_count=1,
                        is_small_font=relative_font_size < 0.85,
                    )
                    classification = classify_block(features, profile)
                    role = classification.resolved_role
                    if role is None or registry.resolve(role) is None:
                        role = "text.paragraph"
                    pending.append(
                        _PendingUnit(
                            sort_key=(
                                page_index,
                                line.bbox.y0,
                                line.bbox.x0,
                                "line",
                                line.id,
                            ),
                            reconstruction_class="block_candidate",
                            role=role,
                            evidence_refs=tuple(
                                _evidence_ref(unit) for unit in line_units
                            ),
                            properties={
                                "surface": surface,
                                "classification": classification.model_dump(
                                    mode="json"
                                ),
                            },
                            provenance_ref=line_units[0].provenance_ref,
                        )
                    )

    return tuple(pending)


def _page_index(unit: EvidenceUnit) -> int:
    raw = unit.source_locator.get("page_index", 0)
    return int(raw) if isinstance(raw, int) else 0


def _font_name(unit: EvidenceUnit) -> str:
    presentation = unit.presentation or {}
    return str(presentation.get("font", "")).casefold()


def _font_size(unit: EvidenceUnit) -> float | None:
    presentation = unit.presentation or {}
    raw = presentation.get("size")
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    return None


def _evidence_ref(unit: EvidenceUnit) -> ArtifactRef:
    return ArtifactRef(
        id=unit.id,
        digest=sha256_bytes(unit.model_dump_json().encode("utf-8")),
        kind="evidence_unit",
    )
