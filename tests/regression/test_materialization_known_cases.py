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
from voxcodex.materialization.anchors import AnchorEvidence, build_source_anchors
from voxcodex.materialization.mappings import (
    RoleProfileRegistry,
    materialize_formula_payload,
    materialize_table_payload,
)
from voxcodex.reconstruction.structured import (
    detect_formula_candidate,
    detect_table_candidate,
    detect_terminal_candidate,
)
from voxcodex.storage.blobs import LocalBlobStore


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPO_ROOT / "data"
FEDRA_SHA256 = "ec048480453a3e04d54188d06fac15b55dea8270f7f971acf2d0bbcfd6c5ef59"
WEIDMAN_SHA256 = "db06828cb749082e0885060f2a3ff23ee8a175b78f7d6dfefe184bb172b735bd"


def _data_root() -> Path:
    override = os.environ.get("VOXCODEX_KNOWN_CORPUS_DIR")
    return Path(override) if override else DEFAULT_DATA_ROOT


def _require_exact(name: str) -> Path:
    path = _data_root() / name
    if not path.is_file():
        pytest.skip(f"known materialization regression requires local source corpus; missing {path}")
    return path


def _require_glob(pattern: str) -> Path:
    matches = sorted(_data_root().glob(pattern))
    if not matches:
        pytest.skip(f"known materialization regression requires local source corpus; no match for {pattern}")
    if len(matches) != 1:
        raise AssertionError(f"expected one source for {pattern!r}; found {matches}")
    return matches[0]


def _source(path: Path, expected_sha256: str | None = None) -> SourceArtifact:
    data = path.read_bytes()
    checksum = sha256_bytes(data)
    if expected_sha256 is not None:
        assert checksum == expected_sha256
    return SourceArtifact(
        id=f"source:materialization-regression:{checksum}",
        media_type="application/pdf",
        original_filename=path.name,
        byte_size=len(data),
        checksum=checksum,
        acquisition_kind="local_regression_corpus",
        original_uri=None,
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
    )


def _extract(path: Path, tmp_path: Path, pages: list[int], expected_sha256: str | None = None):
    source = _source(path, expected_sha256)
    adapter = PdfAdapter(blob_store=LocalBlobStore(tmp_path / "blobs"))
    profile = ExtractionProfile(
        id=f"extraction-profile:materialization:{path.stem}",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": True},
    )
    snapshot = adapter.extract(source, path, profile, page_indexes=pages)
    loaded = [adapter.load_partition(ref) for ref in snapshot.partition_refs]
    return source, loaded


def _spans(loaded) -> list[EvidenceUnit]:
    return [
        unit
        for _partition, units in loaded
        for unit in units
        if unit.evidence_class == "text_span" and unit.surface and unit.normalized_geometry is not None
    ]


def _anchor_input(source: SourceArtifact, unit: EvidenceUnit, page_index: int) -> AnchorEvidence:
    geometry = unit.normalized_geometry
    assert geometry is not None
    return AnchorEvidence(
        evidence_ref=unit.id,
        source_artifact_ref=source.id,
        extraction_ref="activity:known-materialization",
        source_page_index=page_index,
        x0=geometry.x0,
        y0=geometry.y0,
        x1=geometry.x1,
        y1=geometry.y1,
    )


def test_f1_drama_role_and_physical_anchor_materialize_from_known_page(tmp_path: Path):
    path = _require_exact("Fedra - Jean Racine - 2013.pdf")
    source, loaded = _extract(path, tmp_path, [5], FEDRA_SHA256)
    span = _spans(loaded)[0]
    mapping = RoleProfileRegistry.v01_defaults().resolve("drama.speaker_cue")
    anchors = build_source_anchors("node:f1:speaker", (_anchor_input(source, span, 5),))

    assert mapping is not None and mapping.cbm_role == "drama.speaker_cue"
    assert anchors[0].locator.source_page_index == 5


def test_w2_table_candidate_materializes_cell_topology(tmp_path: Path):
    path = _require_glob("Testes de Invas*.pdf")
    _source_obj, loaded = _extract(path, tmp_path, [95], WEIDMAN_SHA256)
    spans = _spans(loaded)
    target = next((unit for unit in spans if (unit.surface or "").strip() == "011"), None)
    assert target is not None, "PROCESSING_FAILURE: W2 literal 011 missing before materialization"
    geometry = target.normalized_geometry
    assert geometry is not None
    center_y = (geometry.y0 + geometry.y1) / 2.0
    band = [
        unit for unit in spans
        if unit.normalized_geometry is not None
        and abs(((unit.normalized_geometry.y0 + unit.normalized_geometry.y1) / 2.0) - center_y) <= 0.14
    ]
    candidate = detect_table_candidate(
        band,
        ReconstructionProfile(id="reconstruction-profile:w2-materialization", version="0.1.0", table_axis_tolerance=0.025),
    )
    assert candidate is not None, "PROCESSING_FAILURE: W2 table candidate missing"
    content_map = {ref.id: f"fragment:{index}" for index, ref in enumerate(candidate.evidence_refs)}
    payload = materialize_table_payload(candidate, content_refs_by_evidence=content_map)

    assert payload.row_count == candidate.row_count
    assert payload.column_count == candidate.column_count
    assert payload.cells


def test_c1_cross_page_evidence_materializes_multiple_physical_anchors(tmp_path: Path):
    path = _require_exact("Leandro Lima - As Grandes Doutrinas da Graça, Vols. 1–2 (Agathos, 2017).pdf")
    source, loaded = _extract(path, tmp_path, [5, 6])
    page_spans = [[unit for unit in units if unit.evidence_class == "text_span" and unit.normalized_geometry] for _p, units in loaded]
    inputs = (
        _anchor_input(source, page_spans[0][-1], 5),
        _anchor_input(source, page_spans[1][0], 6),
    )
    anchors = build_source_anchors("node:c1:cross-page", inputs)

    assert tuple(anchor.locator.source_page_index for anchor in anchors) == (5, 6)


def test_c3_formula_materialization_keeps_visual_source_representation(tmp_path: Path):
    path = _require_exact("Calculus 8Ed James Stewart.pdf")
    _source_obj, loaded = _extract(path, tmp_path, [82, 86, 138, 144])
    candidates = []
    for _partition, units in loaded:
        glyphs = [unit for unit in units if unit.evidence_class in {"glyph_run", "text_span"} and unit.surface and unit.normalized_geometry]
        candidate = detect_formula_candidate(glyphs, symbolic_representation=None) if glyphs else None
        if candidate is not None:
            candidates.append(candidate)
    assert candidates, "PROCESSING_FAILURE: C3 formula candidate missing"
    payload = materialize_formula_payload(candidates[0])

    assert payload.source_representation_refs
    assert payload.reconstructed_representation_refs == ()


def test_w_rnd_terminal_input_role_is_registered_for_materialization(tmp_path: Path):
    path = _require_glob("Testes de Invas*.pdf")
    _source_obj, loaded = _extract(path, tmp_path, [557], WEIDMAN_SHA256)
    candidate = detect_terminal_candidate(_spans(loaded))
    assert candidate is not None, "PROCESSING_FAILURE: W-RND terminal candidate missing"
    mapping = RoleProfileRegistry.v01_defaults().resolve("technical.terminal_input")

    assert mapping is not None
    assert any(line.input_text is not None for line in candidate.lines)
