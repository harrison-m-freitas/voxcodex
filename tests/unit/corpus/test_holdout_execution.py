from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxcodex.corpus import holdout_execution
from voxcodex.corpus.candidate import (
    ImplementationCandidateManifest,
    freeze_candidate,
)
from voxcodex.digests import sha256_bytes


def _selection_manifest(
    tmp_path: Path,
    *,
    pages: tuple[int, ...] | None = None,
    zip_member: str | None = None,
) -> Path:
    selected_scope: dict[str, object]
    fmt: str
    source_path: str
    if pages is not None:
        selected_scope = {"physical_pdf_pages_1_based": list(pages)}
        fmt = "PDF"
        source_path = "corpus/compatibility/CC-SYN/source/secret.pdf"
    else:
        selected_scope = {
            "zip_member_path": zip_member or "book/src/a.md",
            "member_sha256": "9" * 64,
            "member_byte_size": 123,
        }
        fmt = "Markdown source bundle (ZIP)"
        source_path = "corpus/compatibility/CC-SYN/source/book.zip"

    payload = {
        "schema": "voxcodex.m2_blind_holdout_selection.v1",
        "version": "1.0-frozen",
        "status": "FROZEN_UNREVEALED",
        "holdouts": [
            {
                "holdout_id": "SYN-H1",
                "corpus_case_id": "CC-SYN",
                "support_tier": "Tier 1",
                "format": fmt,
                "source_artifact": {
                    "relative_path": source_path,
                    "sha256": "8" * 64,
                    "byte_size": 456,
                },
                "selection": {"selected_scope": selected_scope},
            }
        ],
    }
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _freeze_manifest(tmp_path: Path, selection_path: Path) -> Path:
    payload = {
        "schema": "voxcodex.m2_holdout_freeze_manifest.v1",
        "status": "FROZEN_UNREVEALED",
        "holdout_selection_manifest_sha256": sha256_bytes(selection_path.read_bytes()),
        "reserved_source_artifacts": [],
    }
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _candidate(tmp_path: Path, freeze_path: Path) -> tuple[Path, str]:
    manifest = ImplementationCandidateManifest(
        candidate_id="m2-implementation-candidate-v2",
        git_commit_sha="a" * 40,
        implementation_tree_digest="b" * 64,
        uv_lock_sha256="c" * 64,
        python_version="3.14.7",
        uv_version="0.12.13",
        processor_versions={"pipeline": "1"},
        semantic_config_digests={"pipeline": "d" * 64},
        validation_policy_digest="e" * 64,
        regression_assertion_manifest_digest="f" * 64,
        corpus_freeze_manifest_digest="1" * 64,
        holdout_freeze_manifest_digest=sha256_bytes(freeze_path.read_bytes()),
        regression_report_digest="2" * 64,
        capability_claims=("Tier 1 PDF and Markdown",),
        known_classifications=(),
        regression_status="PASS",
        selective_reprocessing_status="PASS",
        holdouts_withheld=("CC-SYN",),
    )
    path = tmp_path / "candidate.json"
    artifact = freeze_candidate(manifest, output_path=path)
    return path, artifact.digest


def _reveal(
    tmp_path: Path,
    *,
    candidate_digest: str,
    holdout_digest: str,
    reveal_version: str = "M2_HOLDOUTS_V1",
) -> Path:
    payload = {
        "candidate_digest": candidate_digest,
        "holdout_manifest_digest": holdout_digest,
        "revealed_at": "2026-09-17T00:00:00+00:00",
        "actor": "synthetic",
        "context": "unit-test",
        "reveal_version": reveal_version,
    }
    path = tmp_path / "reveal.json"
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _report(tmp_path: Path) -> Path:
    path = tmp_path / "report.json"
    path.write_text("{}\n", encoding="utf-8")
    return path


def test_pdf_scope_converts_frozen_one_based_pages_to_zero_based_indexes(
    tmp_path: Path,
) -> None:
    specs = holdout_execution.load_holdout_execution_specs(
        _selection_manifest(tmp_path, pages=(57, 58)),
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
    )

    assert specs[0].selected_page_indexes == (56, 57)
    assert specs[0].zip_member_path is None


def test_markdown_zip_scope_keeps_exact_frozen_member_path(tmp_path: Path) -> None:
    specs = holdout_execution.load_holdout_execution_specs(
        _selection_manifest(tmp_path, zip_member="book-main/src/ch15-01-box.md"),
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
    )

    assert specs[0].zip_member_path == "book-main/src/ch15-01-box.md"
    assert specs[0].zip_member_sha256 == "9" * 64
    assert specs[0].zip_member_byte_size == 123


def test_preflight_rejects_missing_reveal_before_source_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_manifest(tmp_path, pages=(1, 2))
    freeze = _freeze_manifest(tmp_path, selection)
    candidate, _candidate_digest = _candidate(tmp_path, freeze)
    report = _report(tmp_path)

    monkeypatch.setattr(
        holdout_execution,
        "verify_repository_candidate",
        lambda **_: None,
    )

    with pytest.raises(holdout_execution.HoldoutPreflightError, match="reveal"):
        holdout_execution.verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=candidate,
            regression_report_path=report,
            selection_manifest_path=selection,
            holdout_freeze_manifest_path=freeze,
            reveal_record_path=tmp_path / "missing-reveal.json",
            corpus_case_id="CC-SYN",
        )

    assert not (tmp_path / "corpus/compatibility/CC-SYN/source/secret.pdf").exists()


def test_preflight_rejects_reveal_bound_to_other_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_manifest(tmp_path, pages=(1,))
    freeze = _freeze_manifest(tmp_path, selection)
    candidate, _candidate_digest = _candidate(tmp_path, freeze)
    reveal = _reveal(
        tmp_path,
        candidate_digest="0" * 64,
        holdout_digest=sha256_bytes(freeze.read_bytes()),
    )
    monkeypatch.setattr(holdout_execution, "verify_repository_candidate", lambda **_: None)

    with pytest.raises(holdout_execution.HoldoutPreflightError, match="candidate"):
        holdout_execution.verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=candidate,
            regression_report_path=_report(tmp_path),
            selection_manifest_path=selection,
            holdout_freeze_manifest_path=freeze,
            reveal_record_path=reveal,
            corpus_case_id="CC-SYN",
        )


def test_preflight_rejects_changed_holdout_freeze_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_manifest(tmp_path, pages=(1,))
    freeze = _freeze_manifest(tmp_path, selection)
    candidate, candidate_digest = _candidate(tmp_path, freeze)
    original_holdout_digest = sha256_bytes(freeze.read_bytes())
    reveal = _reveal(
        tmp_path,
        candidate_digest=candidate_digest,
        holdout_digest=original_holdout_digest,
    )
    freeze.write_text(
        json.dumps(
            {
                "schema": "voxcodex.m2_holdout_freeze_manifest.v1",
                "status": "FROZEN_UNREVEALED",
                "holdout_selection_manifest_sha256": "0" * 64,
                "reserved_source_artifacts": [],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(holdout_execution, "verify_repository_candidate", lambda **_: None)

    with pytest.raises(holdout_execution.HoldoutPreflightError, match="holdout.*digest"):
        holdout_execution.verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=candidate,
            regression_report_path=_report(tmp_path),
            selection_manifest_path=selection,
            holdout_freeze_manifest_path=freeze,
            reveal_record_path=reveal,
            corpus_case_id="CC-SYN",
        )


def test_preflight_rejects_selection_manifest_not_bound_by_freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_manifest(tmp_path, pages=(1,))
    freeze = _freeze_manifest(tmp_path, selection)
    candidate, candidate_digest = _candidate(tmp_path, freeze)
    reveal = _reveal(
        tmp_path,
        candidate_digest=candidate_digest,
        holdout_digest=sha256_bytes(freeze.read_bytes()),
    )
    selection.write_text(
        selection.read_text(encoding="utf-8").replace('"PDF"', '"PDF changed"'),
        encoding="utf-8",
    )
    monkeypatch.setattr(holdout_execution, "verify_repository_candidate", lambda **_: None)

    with pytest.raises(holdout_execution.HoldoutPreflightError, match="selection.*digest"):
        holdout_execution.verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=candidate,
            regression_report_path=_report(tmp_path),
            selection_manifest_path=selection,
            holdout_freeze_manifest_path=freeze,
            reveal_record_path=reveal,
            corpus_case_id="CC-SYN",
        )


def test_preflight_rejects_unknown_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_manifest(tmp_path, pages=(1,))
    freeze = _freeze_manifest(tmp_path, selection)
    candidate, candidate_digest = _candidate(tmp_path, freeze)
    reveal = _reveal(
        tmp_path,
        candidate_digest=candidate_digest,
        holdout_digest=sha256_bytes(freeze.read_bytes()),
    )
    monkeypatch.setattr(holdout_execution, "verify_repository_candidate", lambda **_: None)

    with pytest.raises(holdout_execution.HoldoutPreflightError, match="unknown.*holdout"):
        holdout_execution.verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=candidate,
            regression_report_path=_report(tmp_path),
            selection_manifest_path=selection,
            holdout_freeze_manifest_path=freeze,
            reveal_record_path=reveal,
            corpus_case_id="CC-NOT-THERE",
        )
