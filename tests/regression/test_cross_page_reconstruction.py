from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path

import pytest

from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.digests import sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceUnit, ExtractionProfile
from voxcodex.domain.reconstruction import OpenStructuralState
from voxcodex.domain.source import SourceArtifact
from voxcodex.reconstruction.boundaries import (
    BoundaryFragment,
    collapse_recurrent_editorial,
    reconcile_partition,
)
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
        pytest.skip(f"historical reconstruction regression requires local source corpus; missing {path}")
    return path


def _require_glob_source(pattern: str) -> Path:
    matches = sorted(_data_root().glob(pattern))
    if not matches:
        pytest.skip(f"historical reconstruction regression requires local source corpus; no match for {pattern}")
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
        id=f"source:historical-regression:{checksum}",
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
) -> list[tuple[object, tuple[EvidenceUnit, ...]]]:
    source = _source(path, expected_sha256=expected_sha256)
    adapter = PdfAdapter(blob_store=LocalBlobStore(tmp_path / "blobs"))
    profile = ExtractionProfile(
        id=f"extraction-profile:cross-page:{path.stem}",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": False},
    )
    snapshot = adapter.extract(source, path, profile, page_indexes=page_indexes)
    return [adapter.load_partition(ref) for ref in snapshot.partition_refs]


def _nonempty_lines(loaded_partition: tuple[object, tuple[EvidenceUnit, ...]]) -> list[EvidenceUnit]:
    _partition, units = loaded_partition
    return [
        unit
        for unit in units
        if unit.evidence_class == "line" and unit.surface and unit.surface.strip()
    ]


def _evidence_ref(unit: EvidenceUnit) -> ArtifactRef:
    digest = sha256_bytes(unit.model_dump_json().encode("utf-8"))
    return ArtifactRef(id=unit.id, digest=digest, kind="evidence_unit")


def _fragment(
    unit: EvidenceUnit,
    *,
    fragment_id: str,
    structural_kind: str,
    opens: bool = False,
    closes: bool = False,
    recurrence_key: str | None = None,
) -> BoundaryFragment:
    return BoundaryFragment(
        id=fragment_id,
        structural_kind=structural_kind,
        surface=unit.surface or "",
        evidence_refs=(_evidence_ref(unit),),
        opens_continuation=opens,
        closes_continuation=closes,
        recurrence_key=recurrence_key,
    )


def test_f2_cross_page_open_state_preserves_both_page_evidence(tmp_path: Path):
    path = _require_exact_source("Fedra - Jean Racine - 2013.pdf")
    loaded = _extract_pages(path, tmp_path, [9, 10], expected_sha256=FEDRA_SHA256)
    last_page_10 = _nonempty_lines(loaded[0])[-1]
    first_page_11 = _nonempty_lines(loaded[1])[0]

    pending = reconcile_partition(
        (_fragment(last_page_10, fragment_id="F2:p10:last", structural_kind="speech", opens=True),),
        OpenStructuralState(),
        boundary_kind="page",
    )
    final = reconcile_partition(
        (_fragment(first_page_11, fragment_id="F2:p11:first", structural_kind="speech", closes=True),),
        pending.open_state,
        boundary_kind="page",
    )

    assert len(final.blocks) == 1
    assert len(final.blocks[0].evidence_refs) == 2
    assert final.issues == ()
    assert final.open_state.continuations == ()


def test_historical_f_rnd_mid_speech_without_prior_partition_is_explicit_issue(tmp_path: Path):
    path = _require_exact_source("Fedra - Jean Racine - 2013.pdf")
    loaded = _extract_pages(path, tmp_path, [32], expected_sha256=FEDRA_SHA256)
    first_line = _nonempty_lines(loaded[0])[0]
    fragment = _fragment(
        first_line,
        fragment_id="F-RND:p33:first",
        structural_kind="speech",
        closes=True,
    )

    result = reconcile_partition((fragment,), OpenStructuralState(), boundary_kind="page")

    assert result.blocks[0].surface == first_line.surface
    assert result.blocks[0].evidence_refs == (_evidence_ref(first_line),)
    assert result.issues[0].issue_type == "unresolved_boundary"


def test_c1_cross_page_handoff_keeps_physical_evidence_from_both_pages(tmp_path: Path):
    path = _require_exact_source(
        "Leandro Lima - As Grandes Doutrinas da Graça, Vols. 1–2 (Agathos, 2017).pdf"
    )
    loaded = _extract_pages(path, tmp_path, [5, 6])
    last_page_6 = _nonempty_lines(loaded[0])[-1]
    first_page_7 = _nonempty_lines(loaded[1])[0]

    pending = reconcile_partition(
        (_fragment(last_page_6, fragment_id="C1:p6:last", structural_kind="paragraph", opens=True),),
        OpenStructuralState(),
        boundary_kind="page",
    )
    final = reconcile_partition(
        (_fragment(first_page_7, fragment_id="C1:p7:first", structural_kind="paragraph", closes=True),),
        pending.open_state,
        boundary_kind="page",
    )

    assert len(final.blocks) == 1
    assert tuple(ref.id for ref in final.blocks[0].evidence_refs) == (
        last_page_6.id,
        first_page_7.id,
    )


def test_w1_repeated_top_page_material_does_not_duplicate_logical_header(tmp_path: Path):
    path = _require_glob_source("Testes de Invas*.pdf")
    loaded = _extract_pages(path, tmp_path, [109, 110, 111], expected_sha256=WEIDMAN_SHA256)

    top_lines_by_page: list[dict[str, EvidenceUnit]] = []
    for partition in loaded:
        candidates: dict[str, EvidenceUnit] = {}
        for unit in _nonempty_lines(partition):
            geometry = unit.normalized_geometry
            if geometry is None or geometry.y0 > 0.15:
                continue
            normalized = " ".join((unit.surface or "").split())
            if normalized and not normalized.isdigit():
                candidates.setdefault(normalized, unit)
        top_lines_by_page.append(candidates)

    repeated = set(top_lines_by_page[0])
    for page in top_lines_by_page[1:]:
        repeated &= set(page)
    assert repeated, "expected at least one repeated non-numeric top-page line in the known W1 chapter slice"
    surface = max(repeated, key=len)
    recurrence_key = f"running-header:{sha256_bytes(surface.encode('utf-8'))}"
    fragments = tuple(
        _fragment(
            page[surface],
            fragment_id=f"W1:header:{index}",
            structural_kind="running_header",
            recurrence_key=recurrence_key,
        )
        for index, page in enumerate(top_lines_by_page)
    )

    collapsed = collapse_recurrent_editorial(fragments)

    assert len(collapsed) == 1
    assert collapsed[0].occurrence_count == 3
    assert len(collapsed[0].evidence_refs) == 3
