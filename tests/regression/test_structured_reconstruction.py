from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path

import pytest

from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.digests import sha256_bytes
from voxcodex.domain.evidence import EvidenceUnit, ExtractionProfile
from voxcodex.domain.reconstruction import ReconstructionProfile
from voxcodex.domain.source import SourceArtifact
from voxcodex.reconstruction.structured import (
    build_figure_candidate,
    detect_formula_candidate,
    detect_table_candidate,
    detect_terminal_candidate,
)
from voxcodex.storage.blobs import LocalBlobStore


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPO_ROOT / "data"
WEIDMAN_SHA256 = "db06828cb749082e0885060f2a3ff23ee8a175b78f7d6dfefe184bb172b735bd"


def _data_root() -> Path:
    override = os.environ.get("VOXCODEX_KNOWN_CORPUS_DIR")
    return Path(override) if override else DEFAULT_DATA_ROOT


def _require_exact_source(relative_name: str) -> Path:
    path = _data_root() / relative_name
    if not path.is_file():
        pytest.skip(f"structured reconstruction regression requires local source corpus; missing {path}")
    return path


def _require_glob_source(pattern: str) -> Path:
    matches = sorted(_data_root().glob(pattern))
    if not matches:
        pytest.skip(f"structured reconstruction regression requires local source corpus; no match for {pattern}")
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one source matching {pattern!r}, found {matches}")
    return matches[0]


def _source(path: Path, *, expected_sha256: str | None = None) -> SourceArtifact:
    data = path.read_bytes()
    checksum = sha256_bytes(data)
    if expected_sha256 is not None:
        assert checksum == expected_sha256
    return SourceArtifact(
        id=f"source:structured-regression:{checksum}",
        media_type="application/pdf",
        original_filename=path.name,
        byte_size=len(data),
        checksum=checksum,
        acquisition_kind="local_regression_corpus",
        original_uri=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def _extract(
    path: Path,
    tmp_path: Path,
    pages: list[int],
    *,
    expected_sha256: str | None = None,
    glyph_runs: bool = False,
) -> list[tuple[object, tuple[EvidenceUnit, ...]]]:
    source = _source(path, expected_sha256=expected_sha256)
    adapter = PdfAdapter(blob_store=LocalBlobStore(tmp_path / "blobs"))
    profile = ExtractionProfile(
        id=f"extraction-profile:structured:{path.stem}:{'glyphs' if glyph_runs else 'lean'}",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": glyph_runs},
    )
    snapshot = adapter.extract(source, path, profile, page_indexes=pages)
    return [adapter.load_partition(ref) for ref in snapshot.partition_refs]


def _spans(loaded) -> list[EvidenceUnit]:
    return [
        unit
        for _partition, units in loaded
        for unit in units
        if unit.evidence_class == "text_span" and unit.surface and unit.normalized_geometry is not None
    ]


def test_w1_terminal_candidate_is_detectable_from_physical_signals(tmp_path: Path):
    path = _require_glob_source("Testes de Invas*.pdf")
    loaded = _extract(path, tmp_path, [111], expected_sha256=WEIDMAN_SHA256)
    spans = _spans(loaded)
    technical = [
        unit
        for unit in spans
        if any(token in str(unit.presentation.get("font", "")).lower() for token in ("mono", "courier"))
        or (unit.surface or "").lstrip().startswith(("$", "#", ">"))
    ]

    candidate = detect_terminal_candidate(technical)

    assert candidate is not None, "PROCESSING_FAILURE: W1 terminal evidence was present but not reconstructed"
    assert candidate.evidence_refs
    assert any(line.input_text is not None for line in candidate.lines)
    assert any(line.output_text is not None for line in candidate.lines)


def test_w2_table_candidate_preserves_surface_011_and_grid_topology(tmp_path: Path):
    path = _require_glob_source("Testes de Invas*.pdf")
    loaded = _extract(path, tmp_path, [95], expected_sha256=WEIDMAN_SHA256)
    spans = _spans(loaded)
    target = next((unit for unit in spans if (unit.surface or "").strip() == "011"), None)
    assert target is not None, "PROCESSING_FAILURE: W2 literal surface 011 was not available in Evidence"
    target_geometry = target.normalized_geometry
    assert target_geometry is not None
    target_y = (target_geometry.y0 + target_geometry.y1) / 2.0
    table_band = [
        unit
        for unit in spans
        if unit.normalized_geometry is not None
        and abs(((unit.normalized_geometry.y0 + unit.normalized_geometry.y1) / 2.0) - target_y) <= 0.14
    ]

    candidate = detect_table_candidate(
        table_band,
        ReconstructionProfile(id="reconstruction-profile:w2", version="0.1.0", table_axis_tolerance=0.025),
    )

    assert candidate is not None, "PROCESSING_FAILURE: W2 table topology was not reconstructed"
    assert candidate.row_count >= 2
    assert candidate.column_count >= 2
    assert any(cell.surface and cell.surface.strip() == "011" for cell in candidate.cells)


def test_c3_formula_and_figure_candidates_preserve_visual_evidence(tmp_path: Path):
    path = _require_exact_source("Calculus 8Ed James Stewart.pdf")
    loaded = _extract(path, tmp_path, [82, 86, 138, 144], glyph_runs=True)

    formula_candidates = []
    figure_candidates = []
    for _partition, units in loaded:
        glyphs = [
            unit
            for unit in units
            if unit.evidence_class in {"glyph_run", "text_span"}
            and unit.normalized_geometry is not None
            and unit.surface
        ]
        assets = [
            unit
            for unit in units
            if unit.evidence_class == "asset" and unit.normalized_geometry is not None
        ]
        if glyphs:
            candidate = detect_formula_candidate(glyphs, symbolic_representation=None)
            if candidate is not None:
                formula_candidates.append(candidate)
        if assets:
            figure_candidates.append(build_figure_candidate(assets))

    assert formula_candidates, "PROCESSING_FAILURE: C3 mathematical visual evidence produced no FormulaCandidate"
    assert any(candidate.symbolic_representation is None for candidate in formula_candidates)
    assert figure_candidates, "PROCESSING_FAILURE: C3 figure assets produced no FigureCandidate"
    assert all(candidate.evidence_refs for candidate in formula_candidates)
    assert all(candidate.evidence_refs for candidate in figure_candidates)
