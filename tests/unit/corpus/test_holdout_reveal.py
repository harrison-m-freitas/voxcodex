from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxcodex.corpus import holdouts
from voxcodex.corpus.candidate import (
    ImplementationCandidateManifest,
    KnownClassification,
    freeze_candidate,
)
from voxcodex.digests import sha256_bytes


def _write_holdout_manifest(path: Path, *, marker: str = "synthetic") -> str:
    payload = {
        "schema": "voxcodex.synthetic_holdout_manifest.v1",
        "status": "FROZEN_UNREVEALED",
        "marker": marker,
        "reserved_source_artifacts": [
            {"holdout_id": "SYN-H1", "path": "never-resolve/source.pdf"}
        ],
    }
    raw = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(raw)
    return sha256_bytes(raw)


def _write_candidate(path: Path, *, holdout_digest: str) -> str:
    manifest = ImplementationCandidateManifest(
        candidate_id="synthetic-candidate-v1",
        git_commit_sha="a" * 40,
        uv_lock_sha256="b" * 64,
        python_version="3.14.7",
        uv_version="0.12.13",
        processor_versions={"synthetic": "1"},
        semantic_config_digests={"synthetic": "c" * 64},
        validation_policy_digest="d" * 64,
        regression_assertion_manifest_digest="e" * 64,
        corpus_freeze_manifest_digest="f" * 64,
        holdout_freeze_manifest_digest=holdout_digest,
        regression_report_digest="1" * 64,
        capability_claims=("synthetic Tier 1 claim",),
        known_classifications=(
            KnownClassification(
                case_id="SYN-01",
                support_tier="Tier 1",
                result_class="PASS",
                quarantined=False,
                diagnostic="synthetic",
            ),
        ),
        regression_status="PASS",
        selective_reprocessing_status="PASS",
        holdouts_withheld=("SYN-H1",),
    )
    artifact = freeze_candidate(manifest, output_path=path)
    return artifact.digest


def test_reveal_requires_frozen_candidate(tmp_path: Path) -> None:
    holdout_path = tmp_path / "holdouts.json"
    _write_holdout_manifest(holdout_path)

    with pytest.raises(Exception, match="candidate"):
        holdouts.reveal_holdouts(
            tmp_path / "missing-candidate.json",
            holdout_path,
            "REVEAL_M2_HOLDOUTS_V1",
        )


def test_reveal_rejects_mismatched_holdout_manifest_before_source_resolution(
    tmp_path: Path,
) -> None:
    holdout_path = tmp_path / "holdouts.json"
    original_digest = _write_holdout_manifest(holdout_path, marker="original")
    candidate_path = tmp_path / "candidate.json"
    _write_candidate(candidate_path, holdout_digest=original_digest)

    _write_holdout_manifest(holdout_path, marker="changed")

    with pytest.raises(Exception, match="digest"):
        holdouts.reveal_holdouts(
            candidate_path,
            holdout_path,
            "REVEAL_M2_HOLDOUTS_V1",
        )

    assert not (tmp_path / "M2-HOLDOUT-REVEAL-V1.json").exists()
    assert not (tmp_path / "never-resolve" / "source.pdf").exists()


def test_reveal_requires_exact_acknowledgement(tmp_path: Path) -> None:
    holdout_path = tmp_path / "holdouts.json"
    holdout_digest = _write_holdout_manifest(holdout_path)
    candidate_path = tmp_path / "candidate.json"
    _write_candidate(candidate_path, holdout_digest=holdout_digest)

    with pytest.raises(Exception, match="acknowledgement"):
        holdouts.reveal_holdouts(candidate_path, holdout_path, "reveal")

    assert not (tmp_path / "M2-HOLDOUT-REVEAL-V1.json").exists()


def test_reveal_persists_auditable_record_without_mutating_holdout_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_ACTOR", "synthetic-actor")
    monkeypatch.setenv("GITHUB_RUN_ID", "synthetic-run")

    holdout_path = tmp_path / "holdouts.json"
    holdout_digest = _write_holdout_manifest(holdout_path)
    original_holdout_bytes = holdout_path.read_bytes()
    candidate_path = tmp_path / "candidate.json"
    candidate_digest = _write_candidate(candidate_path, holdout_digest=holdout_digest)

    record = holdouts.reveal_holdouts(
        candidate_path,
        holdout_path,
        "REVEAL_M2_HOLDOUTS_V1",
    )

    assert record.candidate_digest == candidate_digest
    assert record.holdout_manifest_digest == holdout_digest
    assert record.actor == "synthetic-actor"
    assert record.context == "github-actions:synthetic-run"
    assert record.reveal_version == "M2_HOLDOUTS_V1"
    assert holdout_path.read_bytes() == original_holdout_bytes

    state_path = tmp_path / "M2-HOLDOUT-REVEAL-V1.json"
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["candidate_digest"] == candidate_digest
    assert persisted["holdout_manifest_digest"] == holdout_digest
    assert persisted["reveal_version"] == "M2_HOLDOUTS_V1"


def test_reveal_is_one_way_for_same_implementation_history(tmp_path: Path) -> None:
    holdout_path = tmp_path / "holdouts.json"
    holdout_digest = _write_holdout_manifest(holdout_path)
    candidate_path = tmp_path / "candidate.json"
    _write_candidate(candidate_path, holdout_digest=holdout_digest)

    holdouts.reveal_holdouts(
        candidate_path,
        holdout_path,
        "REVEAL_M2_HOLDOUTS_V1",
    )

    with pytest.raises(Exception, match="already revealed"):
        holdouts.reveal_holdouts(
            candidate_path,
            holdout_path,
            "REVEAL_M2_HOLDOUTS_V1",
        )
