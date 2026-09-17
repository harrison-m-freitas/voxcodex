from __future__ import annotations

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionContext
from voxcodex.reconstruction.production import (
    ProductionEvidenceStage,
    production_reconstruction_profile,
)


def _syntax(token_type: str, surface: str, index: int) -> EvidenceUnit:
    return EvidenceUnit(
        id=f"evidence:syntax:{index}",
        snapshot_ref="snapshot:evidence:test",
        evidence_class="syntax_unit",
        source_locator={"line_start": index, "line_end": index + 1},
        surface=surface,
        native_payload={"token_type": token_type},
        provenance_ref="derivation:markdown:test",
    )


def _span(
    surface: str,
    *,
    index: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    font: str = "Times",
    size: float = 10.0,
    evidence_class: str = "text_span",
) -> EvidenceUnit:
    return EvidenceUnit(
        id=f"evidence:{evidence_class}:{index}",
        snapshot_ref="snapshot:evidence:test",
        evidence_class=evidence_class,  # type: ignore[arg-type]
        source_locator={"page_index": 0, "index": index},
        surface=surface,
        presentation={"font": font, "size": size, "flags": 0},
        normalized_geometry=NormalizedGeometry(x0=x0, y0=y0, x1=x1, y1=y1),
        provenance_ref="derivation:pdf:test",
    )


def _asset(index: int) -> EvidenceUnit:
    return EvidenceUnit(
        id=f"evidence:asset:{index}",
        snapshot_ref="snapshot:evidence:test",
        evidence_class="asset",
        source_locator={"page_index": 0, "xref": index},
        normalized_geometry=NormalizedGeometry(x0=0.1, y0=0.1, x1=0.4, y1=0.4),
        native_payload={"blob_sha256": "a" * 64, "byte_size": 10},
        provenance_ref="derivation:pdf:test",
    )


def _run(*evidence_units: EvidenceUnit):
    context = ReconstructionContext(
        snapshot_ref="reconstruction-snapshot:test",
        source_evidence_refs=(
            ArtifactRef(
                id="snapshot:evidence:test",
                digest="e" * 64,
                kind="evidence_snapshot",
            ),
        ),
        reconstruction_profile_ref="reconstruction-profile:m2-production:v0.1",
    )
    return ProductionEvidenceStage(
        tuple(evidence_units),
        production_reconstruction_profile(),
    ).run(context, ())


def test_markdown_stage_maps_heading_paragraph_and_fence_without_source_literals() -> None:
    result = _run(
        _syntax("heading_open", "# Heading\n", 0),
        _syntax("paragraph_open", "Body text.\n", 1),
        _syntax("fence", "~~~sh\necho hi\n~~~\n", 2),
    )

    assert result.units[0].properties["resolved_role"] == "document.root"
    assert [unit.properties["resolved_role"] for unit in result.units[1:]] == [
        "text.heading",
        "text.paragraph",
        "technical.code_block",
    ]
    assert all(unit.parent_ref == result.units[0].id for unit in result.units[1:])


def test_pdf_stage_has_one_root_and_preserves_evidence_refs() -> None:
    source = _span("Alpha", index=0, x0=0.1, y0=0.1, x1=0.4, y1=0.12)

    result = _run(source)

    assert result.units[0].properties["resolved_role"] == "document.root"
    assert result.units[1].parent_ref == result.units[0].id
    assert tuple(ref.id for ref in result.units[1].evidence_refs) == (source.id,)
    assert result.units[1].properties["resolved_role"] == "text.paragraph"


def test_unmapped_classifier_role_falls_back_to_registered_paragraph() -> None:
    source = _span(
        "fixed width line",
        index=0,
        x0=0.1,
        y0=0.2,
        x1=0.4,
        y1=0.22,
        font="Courier New",
    )

    result = _run(source)

    assert result.units[1].properties["resolved_role"] == "text.paragraph"


def test_terminal_candidate_uses_existing_detector_and_becomes_terminal_transcript() -> None:
    command = _span(
        "$ echo hi",
        index=0,
        x0=0.1,
        y0=0.2,
        x1=0.35,
        y1=0.22,
        font="Courier",
    )
    output = _span(
        "hi",
        index=1,
        x0=0.1,
        y0=0.24,
        x1=0.2,
        y1=0.26,
        font="Courier",
    )

    result = _run(command, output)
    roles = [unit.properties.get("resolved_role") for unit in result.units]

    assert "technical.terminal_transcript" in roles
    terminal = next(
        unit
        for unit in result.units
        if unit.properties.get("resolved_role") == "technical.terminal_transcript"
    )
    assert "terminal_candidate" in terminal.properties
    assert {ref.id for ref in terminal.evidence_refs} == {command.id, output.id}


def test_formula_requires_math_glyph_shape_not_geometry_alone() -> None:
    first = _span(
        "ordinary",
        index=0,
        x0=0.1,
        y0=0.1,
        x1=0.2,
        y1=0.12,
        evidence_class="glyph_run",
    )
    second = _span(
        "prose",
        index=1,
        x0=0.25,
        y0=0.16,
        x1=0.35,
        y1=0.18,
        evidence_class="glyph_run",
    )

    result = _run(first, second)

    assert "structured.formula" not in {
        unit.properties.get("resolved_role") for unit in result.units
    }


def test_math_glyph_shape_can_become_formula_candidate() -> None:
    first = _span(
        "x +",
        index=0,
        x0=0.1,
        y0=0.1,
        x1=0.2,
        y1=0.12,
        evidence_class="glyph_run",
    )
    second = _span(
        "y",
        index=1,
        x0=0.22,
        y0=0.11,
        x1=0.3,
        y1=0.13,
        evidence_class="glyph_run",
    )

    result = _run(first, second)
    formula = next(
        unit
        for unit in result.units
        if unit.properties.get("resolved_role") == "structured.formula"
    )

    assert "formula_candidate" in formula.properties
    assert {ref.id for ref in formula.evidence_refs} == {first.id, second.id}


def test_positioned_asset_becomes_figure_candidate() -> None:
    asset = _asset(1)

    result = _run(asset)
    figure = next(
        unit
        for unit in result.units
        if unit.properties.get("resolved_role") == "structured.figure"
    )

    assert "figure_candidate" in figure.properties
    assert tuple(ref.id for ref in figure.evidence_refs) == (asset.id,)
