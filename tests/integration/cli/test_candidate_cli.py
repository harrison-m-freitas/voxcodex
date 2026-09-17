from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from voxcodex.cli import app


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
