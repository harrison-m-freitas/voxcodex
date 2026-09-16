from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tests.fixtures.pdf_factory import build_inspectable_pdf
from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.digests import sha256_bytes
from voxcodex.domain.evidence import ExtractionProfile
from voxcodex.domain.source import SourceArtifact
from voxcodex.storage.blobs import BlobRef, LocalBlobStore


def make_source(path: Path) -> SourceArtifact:
    data = path.read_bytes()
    return SourceArtifact(
        id="source:synthetic-pdf",
        media_type="application/pdf",
        original_filename=path.name,
        byte_size=len(data),
        checksum=sha256_bytes(data),
        acquisition_kind="synthetic_test",
        original_uri=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def test_pdf_evidence_preserves_text_presentation_geometry_assets_and_glyphs(tmp_path: Path):
    path = build_inspectable_pdf(tmp_path / "inspectable.pdf")
    source = make_source(path)
    store = LocalBlobStore(tmp_path / "blobs")
    adapter = PdfAdapter(blob_store=store)
    profile = ExtractionProfile(
        id="extraction-profile:pdf:glyphs",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": True},
    )

    snapshot = adapter.extract(source, path, profile)

    assert len(snapshot.partition_refs) == 1
    partition, units = adapter.load_partition(snapshot.partition_refs[0])
    assert partition.partition_key == "page:0"
    assert partition.partition_digest == snapshot.partition_refs[0].digest

    classes = {unit.evidence_class for unit in units}
    assert {"physical_page", "line", "text_span", "asset", "glyph_run"} <= classes

    spans = [unit for unit in units if unit.evidence_class == "text_span"]
    assert any(unit.surface and "Bold title" in unit.surface for unit in spans)
    bold = next(unit for unit in spans if unit.surface and "Bold title" in unit.surface)
    assert "Bold" in str(bold.presentation["font"])
    assert bold.native_geometry is not None
    assert bold.normalized_geometry is not None
    for value in bold.normalized_geometry.model_dump().values():
        assert 0.0 <= value <= 1.0

    assets = [unit for unit in units if unit.evidence_class == "asset"]
    assert assets
    asset_payload = assets[0].native_payload
    blob = BlobRef(
        sha256=asset_payload["blob_sha256"],
        byte_size=asset_payload["byte_size"],
    )
    assert store.read_bytes(blob)

    assert any(unit.surface and "2" in unit.surface for unit in units if unit.evidence_class == "glyph_run")
    serialized = "\n".join(unit.model_dump_json() for unit in units)
    assert "text.paragraph" not in serialized
    assert "text.heading" not in serialized


def test_pdf_evidence_is_deterministic_per_extraction_profile(tmp_path: Path):
    path = build_inspectable_pdf(tmp_path / "inspectable.pdf")
    source = make_source(path)
    store = LocalBlobStore(tmp_path / "blobs")
    adapter = PdfAdapter(blob_store=store)
    glyph_profile = ExtractionProfile(
        id="extraction-profile:pdf:glyphs",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": True},
    )

    first = adapter.extract(source, path, glyph_profile)
    second = adapter.extract(source, path, glyph_profile)

    assert first.snapshot_digest == second.snapshot_digest
    assert tuple(ref.digest for ref in first.partition_refs) == tuple(
        ref.digest for ref in second.partition_refs
    )

    lean_profile = ExtractionProfile(
        id="extraction-profile:pdf:lean",
        adapter="pdf",
        adapter_version=adapter.adapter_version,
        options={"glyph_runs": False},
    )
    lean = adapter.extract(source, path, lean_profile)

    assert lean.snapshot_digest != first.snapshot_digest
    assert lean.partition_refs[0].digest != first.partition_refs[0].digest
    assert adapter.load_partition(first.partition_refs[0])[0].partition_digest == first.partition_refs[0].digest
    assert adapter.load_partition(lean.partition_refs[0])[0].partition_digest == lean.partition_refs[0].digest
