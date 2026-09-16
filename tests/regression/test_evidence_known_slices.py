from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path

import pytest

from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.digests import sha256_bytes
from voxcodex.domain.evidence import ExtractionProfile
from voxcodex.domain.source import SourceArtifact
from voxcodex.storage.blobs import LocalBlobStore


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPO_ROOT / "data"

FEDRA_SHA256 = "ec048480453a3e04d54188d06fac15b55dea8270f7f971acf2d0bbcfd6c5ef59"
WEIDMAN_SHA256 = "db06828cb749082e0885060f2a3ff23ee8a175b78f7d6dfefe184bb172b735bd"


def _data_root() -> Path:
    override = os.environ.get("VOXCODEX_KNOWN_CORPUS_DIR")
    return Path(override) if override else DEFAULT_DATA_ROOT


def _require_exact_source(relative_name: str) -> Path:
    path = _data_root() / relative_name
    if not path.is_file():
        pytest.skip(
            "known-slice regression requires the local, intentionally unversioned source corpus; "
            f"missing {path}"
        )
    return path


def _require_glob_source(pattern: str) -> Path:
    matches = sorted(_data_root().glob(pattern))
    if not matches:
        pytest.skip(
            "known-slice regression requires the local, intentionally unversioned source corpus; "
            f"no match for {_data_root() / pattern}"
        )
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one source matching {pattern!r}, found {matches}")
    return matches[0]


def _source(path: Path, *, expected_sha256: str | None = None) -> SourceArtifact:
    data = path.read_bytes()
    checksum = sha256_bytes(data)
    if expected_sha256 is not None:
        assert checksum == expected_sha256, (
            f"wrong fixed edition for {path.name}: expected {expected_sha256}, got {checksum}"
        )
    return SourceArtifact(
        id=f"source:regression:{checksum}",
        media_type="application/pdf",
        original_filename=path.name,
        byte_size=len(data),
        checksum=checksum,
        acquisition_kind="local_regression_corpus",
        original_uri=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def _extract_pages(
    path: Path,
    tmp_path: Path,
    page_indexes: list[int],
    *,
    expected_sha256: str | None = None,
    glyph_runs: bool = False,
):
    source = _source(path, expected_sha256=expected_sha256)
    store = LocalBlobStore(tmp_path / "blobs")
    adapter = PdfAdapter(blob_store=store)
    profile = ExtractionProfile(
        id=f"extraction-profile:regression:{path.stem}:{'glyphs' if glyph_runs else 'lean'}",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": glyph_runs},
    )
    snapshot = adapter.extract(source, path, profile, page_indexes=page_indexes)
    loaded = [adapter.load_partition(ref) for ref in snapshot.partition_refs]
    return snapshot, loaded


def _all_units(loaded):
    return [unit for _partition, units in loaded for unit in units]


def _emit_digest(case_id: str, snapshot) -> None:
    partition_digests = ",".join(ref.digest for ref in snapshot.partition_refs)
    print(
        f"KNOWN_SLICE {case_id} snapshot_digest={snapshot.snapshot_digest} "
        f"partition_digests={partition_digests}"
    )


def test_f1_fedra_page_6_retains_surface_lineation_and_geometry(tmp_path: Path):
    path = _require_exact_source("Fedra - Jean Racine - 2013.pdf")
    snapshot, loaded = _extract_pages(
        path,
        tmp_path,
        [5],
        expected_sha256=FEDRA_SHA256,
    )
    units = _all_units(loaded)
    lines = [unit for unit in units if unit.evidence_class == "line"]
    spans = [unit for unit in units if unit.evidence_class == "text_span"]
    surface = "\n".join(unit.surface or "" for unit in spans)

    assert len(snapshot.partition_refs) == 1
    assert len(lines) >= 10
    assert "ATO PRIMEIRO" in surface
    assert "CENA I" in surface
    assert "HIPÓLITO" in surface
    assert all(unit.native_geometry is not None for unit in spans if unit.surface)
    assert all(unit.normalized_geometry is not None for unit in spans if unit.surface)
    _emit_digest("F1", snapshot)


def test_w1_weidman_page_112_retains_typography_layout_and_literal_surface(tmp_path: Path):
    path = _require_glob_source("Testes de Invas*.pdf")
    snapshot, loaded = _extract_pages(
        path,
        tmp_path,
        [111],
        expected_sha256=WEIDMAN_SHA256,
    )
    units = _all_units(loaded)
    spans = [unit for unit in units if unit.evidence_class == "text_span" and unit.surface]
    surface = "\n".join(unit.surface or "" for unit in spans)
    fonts = {str(unit.presentation.get("font")) for unit in spans if unit.presentation.get("font")}
    sizes = {unit.presentation.get("size") for unit in spans if unit.presentation.get("size") is not None}

    assert "chmod 744 pingscript.sh" in surface
    assert len(fonts) >= 2
    assert len(sizes) >= 2
    assert all(unit.normalized_geometry is not None for unit in spans)
    _emit_digest("W1", snapshot)


def test_c1_multicolumn_slices_retain_physical_geometry(tmp_path: Path):
    path = _require_exact_source(
        "Leandro Lima - As Grandes Doutrinas da Graça, Vols. 1–2 (Agathos, 2017).pdf"
    )
    snapshot, loaded = _extract_pages(path, tmp_path, [5, 6, 37, 38])
    units = _all_units(loaded)
    spans = [unit for unit in units if unit.evidence_class == "text_span" and unit.surface]
    x0_values = [unit.normalized_geometry.x0 for unit in spans if unit.normalized_geometry is not None]

    assert len(snapshot.partition_refs) == 4
    assert spans
    assert x0_values
    assert min(x0_values) < 0.4
    assert max(x0_values) > 0.5
    assert all(unit.native_geometry is not None for unit in spans)
    _emit_digest("C1", snapshot)


def test_c3_math_slices_retain_glyph_layout_and_visual_assets(tmp_path: Path):
    path = _require_exact_source("Calculus 8Ed James Stewart.pdf")
    snapshot, loaded = _extract_pages(
        path,
        tmp_path,
        [82, 86, 138, 144],
        glyph_runs=True,
    )
    units = _all_units(loaded)
    glyphs = [unit for unit in units if unit.evidence_class == "glyph_run"]
    assets = [unit for unit in units if unit.evidence_class == "asset"]
    spans = [unit for unit in units if unit.evidence_class == "text_span" and unit.surface]

    assert len(snapshot.partition_refs) == 4
    assert glyphs
    assert assets
    assert spans
    assert any(unit.native_geometry is not None for unit in glyphs)
    assert any(unit.normalized_geometry is not None for unit in glyphs)
    assert any(unit.normalized_geometry is not None for unit in assets)
    _emit_digest("C3", snapshot)
