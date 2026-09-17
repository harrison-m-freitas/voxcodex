from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pymupdf
import pytest

from voxcodex.corpus.holdout_execution import HoldoutExecutionSpec
from voxcodex.corpus import m2_pipeline
from voxcodex.corpus.m2_pipeline import M2PipelineProcessor
from voxcodex.digests import sha256_bytes
from voxcodex.domain.cbm.validation import ValidationReport
from voxcodex.materialization.mappings import RoleMapping, RoleProfileRegistry
from voxcodex.validation.policies import m2_poc_strict


def _pdf(path: Path) -> Path:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Heading", fontsize=18)
    page.insert_text((72, 110), "Body paragraph with enough source text.", fontsize=10)
    document.save(path)
    document.close()
    return path


def _markdown(path: Path) -> Path:
    path.write_text("# Heading\n\nBody paragraph.\n", encoding="utf-8")
    return path


def _zip(path: Path) -> Path:
    with ZipFile(path, "w") as archive:
        archive.writestr("book/src/a.md", "# A\n")
        archive.writestr("book/src/b.md", "# B\n\nSelected body.\n")
    return path


def _spec(
    source: Path,
    *,
    format: str,
    pages: tuple[int, ...] = (),
    member: str | None = None,
    member_digest: str | None = None,
    member_size: int | None = None,
) -> HoldoutExecutionSpec:
    raw = source.read_bytes()
    return HoldoutExecutionSpec(
        holdout_id="SYN-H1",
        corpus_case_id="CC-SYN",
        support_tier="Tier 1",
        format=format,
        source_relative_path=str(source),
        source_sha256=sha256_bytes(raw),
        source_byte_size=len(raw),
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
        selected_page_indexes=pages,
        zip_member_path=member,
        zip_member_sha256=member_digest,
        zip_member_byte_size=member_size,
    )


def _zip_spec(source: Path) -> HoldoutExecutionSpec:
    with ZipFile(source) as archive:
        member = "book/src/b.md"
        data = archive.read(member)
    return _spec(
        source,
        format="Markdown source bundle (ZIP)",
        member=member,
        member_digest=sha256_bytes(data),
        member_size=len(data),
    )


def test_synthetic_pdf_runs_full_pipeline_and_freezes_revision(tmp_path: Path) -> None:
    source = _pdf(tmp_path / "sample.pdf")

    result = M2PipelineProcessor(tmp_path / "work").process(
        _spec(source, format="PDF", pages=(0,)),
        source,
    )

    assert result.result_class == "PASS", result.diagnostic
    assert result.source_digest_verified is True
    assert result.evidence_snapshot_ref
    assert result.evidence_snapshot_digest
    assert result.reconstruction_snapshot_ref
    assert result.reconstruction_snapshot_digest
    assert result.canonical_revision_ref
    assert result.validation_result == "PASS"
    assert result.validation_report_ref
    assert result.frozen_revision_digest
    assert result.evidence_accountability
    assert not any(
        item.significance == "significant" and item.classification == "suspected_loss"
        for item in result.evidence_accountability
    )


def test_synthetic_markdown_uses_same_orchestration_surface(tmp_path: Path) -> None:
    source = _markdown(tmp_path / "sample.md")

    result = M2PipelineProcessor(tmp_path / "work").process(
        _spec(source, format="Markdown"),
        source,
    )

    assert result.result_class == "PASS", result.diagnostic
    assert result.validation_result == "PASS"
    assert result.canonical_revision_ref
    assert result.frozen_revision_digest


def test_zip_member_is_exact_and_member_digest_is_verified(tmp_path: Path) -> None:
    source = _zip(tmp_path / "book.zip")
    spec = _zip_spec(source)

    result = M2PipelineProcessor(tmp_path / "work").process(spec, source)

    assert result.result_class == "PASS", result.diagnostic
    assert result.selected_scope["zip_member_path"] == "book/src/b.md"


def test_container_digest_mismatch_is_processing_failure(tmp_path: Path) -> None:
    source = _markdown(tmp_path / "sample.md")
    spec = _spec(source, format="Markdown").model_copy(
        update={"source_sha256": "0" * 64}
    )

    result = M2PipelineProcessor(tmp_path / "work").process(spec, source)

    assert result.result_class == "PROCESSING_FAILURE"
    assert result.source_digest_verified is False
    assert "source digest" in result.diagnostic


def test_zip_member_digest_mismatch_is_processing_failure(tmp_path: Path) -> None:
    source = _zip(tmp_path / "book.zip")
    spec = _zip_spec(source).model_copy(
        update={"zip_member_sha256": "0" * 64}
    )

    result = M2PipelineProcessor(tmp_path / "work").process(spec, source)

    assert result.result_class == "PROCESSING_FAILURE"
    assert "member digest" in result.diagnostic


def test_materialization_gap_is_model_gap_with_schema_evolution_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _markdown(tmp_path / "sample.md")
    restricted = RoleProfileRegistry(
        version="synthetic-gap",
        mappings=(
            RoleMapping(
                reconstruction_role="document.root",
                node_class="root",
                cbm_role="document.root",
            ),
            RoleMapping(
                reconstruction_role="text.paragraph",
                node_class="block",
                cbm_role="text.paragraph",
            ),
        ),
    )
    monkeypatch.setattr(
        m2_pipeline.RoleProfileRegistry,
        "v01_defaults",
        classmethod(lambda cls: restricted),
    )

    result = M2PipelineProcessor(tmp_path / "work").process(
        _spec(source, format="Markdown"),
        source,
    )

    assert result.result_class == "MODEL_GAP"
    assert result.evolution_observation is not None
    assert result.evolution_observation.result_class == "MODEL_GAP"
    assert result.validation_result is None


def test_validation_failure_is_model_failure_and_never_freezes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _markdown(tmp_path / "sample.md")

    def fail_validation(bundle, policy):
        return ValidationReport(
            id="validation-report:synthetic-fail",
            revision_ref=bundle.revision.id,
            validation_policy_ref=m2_poc_strict().id,
            validator_suite_version="synthetic",
            checks=(),
            result="FAIL",
            created_at=bundle.revision.created_at,
        )

    monkeypatch.setattr(m2_pipeline, "validate_revision", fail_validation)

    result = M2PipelineProcessor(tmp_path / "work").process(
        _spec(source, format="Markdown"),
        source,
    )

    assert result.result_class == "MODEL_FAILURE"
    assert result.validation_result == "FAIL"
    assert result.frozen_revision_digest is None


def test_identical_input_and_config_have_identical_semantic_output_digests(
    tmp_path: Path,
) -> None:
    source = _markdown(tmp_path / "sample.md")
    spec = _spec(source, format="Markdown")

    first = M2PipelineProcessor(tmp_path / "work-1").process(spec, source)
    second = M2PipelineProcessor(tmp_path / "work-2").process(spec, source)

    assert first.result_class == second.result_class == "PASS"
    assert first.evidence_snapshot_digest == second.evidence_snapshot_digest
    assert first.reconstruction_snapshot_digest == second.reconstruction_snapshot_digest
    assert first.frozen_revision_digest == second.frozen_revision_digest
