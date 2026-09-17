from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.corpus.candidate import ImplementationCandidateManifest, freeze_candidate
from voxcodex.digests import sha256_bytes


runner = CliRunner()


def _synthetic_candidate(tmp_path: Path) -> tuple[Path, Path]:
    holdout = tmp_path / "holdouts.json"
    raw = (
        json.dumps(
            {
                "schema": "voxcodex.synthetic_holdout_manifest.v1",
                "status": "FROZEN_UNREVEALED",
                "reserved_source_artifacts": [
                    {"holdout_id": "SYN-H1", "path": "never-resolve/source.pdf"}
                ],
            },
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        + b"\n"
    )
    holdout.write_bytes(raw)

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
        holdout_freeze_manifest_digest=sha256_bytes(raw),
        regression_report_digest="1" * 64,
        capability_claims=("synthetic Tier 1 claim",),
        known_classifications=(),
        regression_status="PASS",
        selective_reprocessing_status="PASS",
        holdouts_withheld=("SYN-H1",),
    )
    candidate = tmp_path / "candidate.json"
    freeze_candidate(manifest, output_path=candidate)
    return candidate, holdout


def test_holdouts_reveal_cli_uses_exact_ack_and_persists_record(tmp_path: Path) -> None:
    candidate, holdout = _synthetic_candidate(tmp_path)

    result = runner.invoke(
        app,
        [
            "holdouts",
            "reveal",
            "--candidate",
            str(candidate),
            "--holdout-manifest",
            str(holdout),
            "--ack",
            "REVEAL_M2_HOLDOUTS_V1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "reveal_version=M2_HOLDOUTS_V1" in result.output
    assert "candidate_digest=" in result.output
    assert (tmp_path / "M2-HOLDOUT-REVEAL-V1.json").is_file()


def test_holdouts_reveal_cli_rejects_non_exact_ack_without_state_change(
    tmp_path: Path,
) -> None:
    candidate, holdout = _synthetic_candidate(tmp_path)

    result = runner.invoke(
        app,
        [
            "holdouts",
            "reveal",
            "--candidate",
            str(candidate),
            "--holdout-manifest",
            str(holdout),
            "--ack",
            "yes",
        ],
    )

    assert result.exit_code != 0
    assert "exact acknowledgement required" in result.output
    assert not (tmp_path / "M2-HOLDOUT-REVEAL-V1.json").exists()
