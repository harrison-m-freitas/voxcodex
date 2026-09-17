from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.corpus.candidate import ImplementationCandidateManifest, freeze_candidate
from voxcodex.corpus.holdout_execution import (
    HoldoutExecutionSpec,
    HoldoutPreflightError,
)
from voxcodex.corpus.m2_pipeline import HoldoutCaseRun
from voxcodex.digests import sha256_bytes


runner = CliRunner()


def _fixture_repo(tmp_path: Path) -> dict[str, Path | str]:
    root = tmp_path / "repo"
    root.mkdir()
    selection = root / "selection.json"
    selection.write_text(
        json.dumps(
            {
                "schema": "synthetic.selection.v1",
                "status": "FROZEN_UNREVEALED",
                "holdouts": [
                    {
                        "holdout_id": "SYN-H1",
                        "corpus_case_id": "CC-SYN",
                        "support_tier": "Tier 1",
                        "format": "Markdown",
                        "source_artifact": {
                            "relative_path": "corpus/compatibility/CC-SYN/source/secret.md",
                            "sha256": "8" * 64,
                            "byte_size": 10,
                        },
                        "selection": {
                            "selected_scope": {
                                "physical_pdf_pages_1_based": [1]
                            }
                        },
                    }
                ],
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    freeze = root / "holdout-freeze.json"
    freeze.write_text(
        json.dumps(
            {
                "schema": "synthetic.freeze.v1",
                "status": "FROZEN_UNREVEALED",
                "holdout_selection_manifest_sha256": sha256_bytes(selection.read_bytes()),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    candidate = root / "candidate.json"
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
        holdout_freeze_manifest_digest=sha256_bytes(freeze.read_bytes()),
        regression_report_digest="2" * 64,
        capability_claims=("Tier 1 PDF and Markdown",),
        known_classifications=(),
        regression_status="PASS",
        selective_reprocessing_status="PASS",
        holdouts_withheld=("CC-SYN",),
    )
    candidate_ref = freeze_candidate(manifest, output_path=candidate)
    reveal = root / "reveal.json"
    reveal.write_text(
        json.dumps(
            {
                "candidate_digest": candidate_ref.digest,
                "holdout_manifest_digest": sha256_bytes(freeze.read_bytes()),
                "revealed_at": "2026-09-17T00:00:00+00:00",
                "actor": "synthetic",
                "context": "integration-test",
                "reveal_version": "M2_HOLDOUTS_V1",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    registry = root / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "total_cases": 1,
                "total_acquired": 1,
                "blind_holdouts": {"reserved_case_ids": ["CC-SYN"]},
                "cases": [{"corpus_case_id": "CC-SYN"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = root / "regression-report.json"
    report.write_text("{}\n", encoding="utf-8")
    return {
        "root": root,
        "selection": selection,
        "freeze": freeze,
        "candidate": candidate,
        "candidate_digest": candidate_ref.digest,
        "reveal": reveal,
        "registry": registry,
        "report": report,
        "output": root / "blind-report.json",
    }


def _args(repo: dict[str, Path | str], *, reveal: Path | None = None) -> list[str]:
    return [
        "corpus",
        "run-holdouts",
        "--repo-root",
        str(repo["root"]),
        "--candidate",
        str(repo["candidate"]),
        "--regression-report",
        str(repo["report"]),
        "--selection-manifest",
        str(repo["selection"]),
        "--holdout-manifest",
        str(repo["freeze"]),
        "--reveal-record",
        str(reveal if reveal is not None else repo["reveal"]),
        "--registry",
        str(repo["registry"]),
        "--output",
        str(repo["output"]),
    ]


def _spec() -> HoldoutExecutionSpec:
    return HoldoutExecutionSpec(
        holdout_id="SYN-H1",
        corpus_case_id="CC-SYN",
        support_tier="Tier 1",
        format="Markdown",
        source_relative_path="corpus/compatibility/CC-SYN/source/secret.md",
        source_sha256="8" * 64,
        source_byte_size=10,
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
        selected_page_indexes=(0,),
    )


def test_run_holdouts_fails_preflight_before_processor_or_source_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fixture_repo(tmp_path)
    called = {"processor": False}

    def blocked(**kwargs):
        raise HoldoutPreflightError("reveal record is missing; source access blocked")

    class MustNotConstruct:
        def __init__(self, *args, **kwargs):
            called["processor"] = True
            raise AssertionError("processor must not be constructed before preflight")

    monkeypatch.setattr("voxcodex.cli.verify_holdout_preflight", blocked)
    monkeypatch.setattr("voxcodex.cli.M2PipelineProcessor", MustNotConstruct)

    result = runner.invoke(
        app,
        _args(repo, reveal=Path(repo["root"]) / "missing-reveal.json"),
    )

    assert result.exit_code != 0
    assert "reveal record is missing" in result.output
    assert called["processor"] is False
    assert not Path(repo["output"]).exists()


def test_run_holdouts_writes_auditable_report_for_synthetic_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fixture_repo(tmp_path)
    spec = _spec()

    monkeypatch.setattr(
        "voxcodex.cli.verify_holdout_preflight",
        lambda **kwargs: spec,
    )

    class FakeProcessor:
        def __init__(self, work_root: Path):
            self.work_root = work_root

        def process(self, received_spec, source_path):
            assert received_spec == spec
            assert source_path == Path(repo["root"]) / spec.source_relative_path
            return HoldoutCaseRun(
                holdout_id=spec.holdout_id,
                corpus_case_id=spec.corpus_case_id,
                selected_scope={"page_indexes": [0]},
                source_digest_verified=True,
                evidence_snapshot_ref="snapshot:evidence:synthetic",
                evidence_snapshot_digest="3" * 64,
                reconstruction_snapshot_ref="snapshot:reconstruction:synthetic",
                reconstruction_snapshot_digest="4" * 64,
                canonical_revision_ref="revision:synthetic",
                frozen_revision_digest="5" * 64,
                validation_report_ref="validation:synthetic",
                validation_result="PASS",
                result_class="PASS",
                diagnostic="synthetic pass",
            )

    monkeypatch.setattr("voxcodex.cli.M2PipelineProcessor", FakeProcessor)

    result = runner.invoke(app, _args(repo))

    assert result.exit_code == 0, result.output
    payload = json.loads(Path(repo["output"]).read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "m2-implementation-candidate-v2"
    assert payload["candidate_digest"] == repo["candidate_digest"]
    assert payload["reveal_version"] == "M2_HOLDOUTS_V1"
    assert payload["cases"][0]["result_class"] == "PASS"
    assert "output=" in result.output


def test_run_holdouts_refuses_to_overwrite_existing_blind_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fixture_repo(tmp_path)
    Path(repo["output"]).write_text("{}\n", encoding="utf-8")
    spec = _spec()
    monkeypatch.setattr(
        "voxcodex.cli.verify_holdout_preflight",
        lambda **kwargs: spec,
    )

    class FakeProcessor:
        def __init__(self, work_root: Path):
            pass

        def process(self, received_spec, source_path):
            return HoldoutCaseRun(
                holdout_id=spec.holdout_id,
                corpus_case_id=spec.corpus_case_id,
                selected_scope={"page_indexes": [0]},
                source_digest_verified=True,
                result_class="PASS",
                diagnostic="synthetic pass",
            )

    monkeypatch.setattr("voxcodex.cli.M2PipelineProcessor", FakeProcessor)

    result = runner.invoke(app, _args(repo))

    assert result.exit_code != 0
    assert "already exists" in result.output
    assert Path(repo["output"]).read_text(encoding="utf-8") == "{}\n"
