from __future__ import annotations

from pathlib import Path

import pytest

from voxcodex.corpus.candidate import (
    CandidateReadinessError,
    ImplementationCandidateManifest,
    KnownClassification,
    _assert_ready,
    implementation_tree_digest,
)


def _base_v2(**overrides) -> ImplementationCandidateManifest:
    data = {
        "candidate_id": "m2-implementation-candidate-v2",
        "git_commit_sha": "a" * 40,
        "uv_lock_sha256": "b" * 64,
        "python_version": "3.14.7",
        "uv_version": "0.12.13",
        "processor_versions": {"pipeline": "1"},
        "semantic_config_digests": {"pipeline": "c" * 64},
        "validation_policy_digest": "d" * 64,
        "regression_assertion_manifest_digest": "e" * 64,
        "corpus_freeze_manifest_digest": "f" * 64,
        "holdout_freeze_manifest_digest": "1" * 64,
        "regression_report_digest": "2" * 64,
        "capability_claims": ("Tier 1 PDF and Markdown",),
        "known_classifications": (
            KnownClassification(
                case_id="SYN-01",
                support_tier="Tier 1",
                result_class="PASS",
                quarantined=False,
                diagnostic="synthetic",
            ),
        ),
        "regression_status": "PASS",
        "selective_reprocessing_status": "PASS",
        "holdouts_withheld": ("CC-05", "CC-07", "CC-14", "CC-18"),
    }
    data.update(overrides)
    return ImplementationCandidateManifest(**data)


def test_implementation_tree_digest_changes_when_semantic_source_changes(
    tmp_path: Path,
) -> None:
    (tmp_path / "src/voxcodex").mkdir(parents=True)
    (tmp_path / "src/voxcodex/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("lock-v1\n", encoding="utf-8")

    first = implementation_tree_digest(tmp_path)
    (tmp_path / "src/voxcodex/a.py").write_text("VALUE = 2\n", encoding="utf-8")
    second = implementation_tree_digest(tmp_path)

    assert first != second


def test_implementation_tree_digest_ignores_nonsemantic_docs(tmp_path: Path) -> None:
    (tmp_path / "src/voxcodex").mkdir(parents=True)
    (tmp_path / "src/voxcodex/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("lock-v1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()

    first = implementation_tree_digest(tmp_path)
    (tmp_path / "docs/note.md").write_text("documentation only\n", encoding="utf-8")
    second = implementation_tree_digest(tmp_path)

    assert first == second


def test_candidate_v2_requires_implementation_tree_digest() -> None:
    manifest = _base_v2()

    with pytest.raises(CandidateReadinessError, match="implementation_tree_digest"):
        _assert_ready(manifest)


def test_candidate_v2_accepts_implementation_tree_digest() -> None:
    manifest = _base_v2(implementation_tree_digest="3" * 64)

    _assert_ready(manifest)
