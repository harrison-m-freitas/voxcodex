from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.digests import canonical_json_bytes, sha256_bytes


runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_candidate_freeze_cli_binds_repository_state_without_revealing_holdouts(tmp_path: Path) -> None:
    report = tmp_path / "regression-report.json"
    report.write_text(
        json.dumps(
            {
                "status": "PASS_WITH_LOCAL_CORPUS_WAIVER",
                "selective_reprocessing_status": "PASS",
                "local_corpus_waiver": "registered SourceArtifacts are not mounted in public CI",
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "M2-IMPLEMENTATION-CANDIDATE-V1.json"

    result = runner.invoke(
        app,
        [
            "candidate",
            "freeze",
            "--repo-root",
            str(REPO_ROOT),
            "--regression-report",
            str(report),
            "--git-commit-sha",
            "a" * 40,
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["git_commit_sha"] == "a" * 40
    assert payload["validation_policy_digest"]
    assert payload["uv_lock_sha256"]
    assert payload["regression_assertion_manifest_digest"]
    assert payload["corpus_freeze_manifest_digest"]
    assert payload["holdout_freeze_manifest_digest"]
    assert payload["regression_report_digest"]
    assert payload["holdouts_withheld"] == ["CC-05", "CC-07", "CC-14", "CC-18"]
    assert "candidate_digest=" in result.output



def test_candidate_verify_cli_accepts_frozen_repository_candidate() -> None:
    result = runner.invoke(
        app,
        [
            "candidate",
            "verify",
            "--repo-root",
            str(REPO_ROOT),
            "--regression-report",
            str(REPO_ROOT / "planning" / "M2-PREFREEZE-REGRESSION-REPORT.json"),
            "--candidate",
            str(REPO_ROOT / "M2-IMPLEMENTATION-CANDIDATE-V1.json"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "candidate_id=m2-implementation-candidate-v1" in result.output
    assert "candidate_digest=666271411488ab2563263efda93a8aa5d182396098eac92e8a356aa69dbfacf9" in result.output
    assert "git_commit_sha=2b20be89d01aa1add802d3fff91d9e3d4fb43719" in result.output


def test_candidate_verify_cli_rejects_self_consistent_manifest_with_repository_drift(
    tmp_path: Path,
) -> None:
    source = REPO_ROOT / "M2-IMPLEMENTATION-CANDIDATE-V1.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["regression_report_digest"] = "0" * 64
    unsigned = dict(payload)
    unsigned.pop("candidate_digest")
    payload["candidate_digest"] = sha256_bytes(canonical_json_bytes(unsigned))
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "candidate",
            "verify",
            "--repo-root",
            str(REPO_ROOT),
            "--regression-report",
            str(REPO_ROOT / "planning" / "M2-PREFREEZE-REGRESSION-REPORT.json"),
            "--candidate",
            str(candidate),
        ],
    )

    assert result.exit_code != 0
    assert "repository no longer matches frozen candidate" in result.output



def test_candidate_freeze_cli_can_create_v2_with_semantic_tree_binding(tmp_path: Path) -> None:
    report = tmp_path / "regression-report.json"
    report.write_text(
        json.dumps(
            {
                "status": "PASS_WITH_LOCAL_CORPUS_WAIVER",
                "selective_reprocessing_status": "PASS",
                "local_corpus_waiver": "registered SourceArtifacts are not mounted in public CI",
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "M2-IMPLEMENTATION-CANDIDATE-V2.json"

    result = runner.invoke(
        app,
        [
            "candidate",
            "freeze",
            "--repo-root",
            str(REPO_ROOT),
            "--regression-report",
            str(report),
            "--git-commit-sha",
            "b" * 40,
            "--candidate-id",
            "m2-implementation-candidate-v2",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "m2-implementation-candidate-v2"
    assert payload["implementation_tree_digest"]
