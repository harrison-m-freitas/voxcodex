from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from voxcodex.application.evidence import (
    DirectCorpusSourceError,
    EvidenceApplication,
    UnknownArtifactError,
)
from voxcodex.application.trace import TraceApplication, UnknownTraceArtifactError
from voxcodex.corpus.candidate import (
    CandidateReadinessError,
    build_repository_candidate,
    freeze_candidate,
)
from voxcodex.corpus.holdouts import QuarantinedCaseError
from voxcodex.corpus.registry import CorpusRegistry
from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.processing import ProcessorIdentity
from voxcodex.execution.planner import ExecutionConfig, PipelineStage, plan_to_cbm
from voxcodex.execution.runner import execute_plan
from voxcodex.materialization.builder import CanonicalTargetContext

app = typer.Typer(name="voxcodex", no_args_is_help=True)
corpus_app = typer.Typer(name="corpus", no_args_is_help=True)
evidence_app = typer.Typer(name="evidence", no_args_is_help=True)
candidate_app = typer.Typer(name="candidate", no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")
app.add_typer(evidence_app, name="evidence")
app.add_typer(candidate_app, name="candidate")


def _home() -> Path:
    return Path(os.environ.get("VOXCODEX_HOME", ".voxcodex"))


def _application() -> EvidenceApplication:
    return EvidenceApplication(_home())


def _execution_config() -> ExecutionConfig:
    def stage(
        name: str,
        *,
        processor_name: str,
        schema_versions: tuple[str, ...],
        uses_target_context: bool = False,
    ) -> PipelineStage:
        semantic_config_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "stage": name,
                    "profile": "m2-default:0.1",
                    "schema_versions": schema_versions,
                }
            )
        )
        return PipelineStage(
            name=name,
            activity_type=name,
            processor=ProcessorIdentity(
                kind="python",
                name=processor_name,
                version="0.1.0",
            ),
            semantic_config_digest=semantic_config_digest,
            profile_versions=("m2-default:0.1",),
            schema_versions=schema_versions,
            uses_target_context=uses_target_context,
            estimated_usage={"work_units": 1},
        )

    return ExecutionConfig(
        stages=(
            stage(
                "evidence",
                processor_name="source_evidence",
                schema_versions=("evidence:0.1",),
            ),
            stage(
                "reconstruction",
                processor_name="reconstruction",
                schema_versions=("evidence:0.1", "reconstruction:0.1"),
            ),
            stage(
                "materialization",
                processor_name="cbm_materialization",
                schema_versions=("reconstruction:0.1", "cbm:0.1"),
                uses_target_context=True,
            ),
        )
    )


def _build_execution_plan(
    source_id: str,
    *,
    target: str,
    work_ref: str,
    edition_ref: str,
    assertion_provenance_ref: str,
):
    if target != "cbm":
        raise typer.BadParameter("--target currently supports only cbm")
    application = _application()
    source_ref = application.metadata.get_artifact(source_id)
    if source_ref is None or source_ref.kind != "source_artifact":
        raise typer.BadParameter(f"unknown source artifact: {source_id}")
    target_context = CanonicalTargetContext(
        work_ref=work_ref,
        edition_ref=edition_ref,
        source_artifact_refs=(source_id,),
        assertion_provenance_ref=assertion_provenance_ref,
    )
    plan = plan_to_cbm(
        source_ref,
        target_context,
        _execution_config(),
        metadata_store=application.metadata,
    )
    return application, plan


@app.command("ingest")
def ingest(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
) -> None:
    try:
        source = _application().ingest_path(path)
    except DirectCorpusSourceError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"source_id={source.id}")
    typer.echo(f"checksum={source.checksum}")
    typer.echo(f"media_type={source.media_type}")


@app.command("trace")
def trace(object_id: str = typer.Argument(...)) -> None:
    try:
        records = TraceApplication(_home()).trace(object_id)
    except UnknownTraceArtifactError as exc:
        raise typer.BadParameter(f"unknown artifact: {object_id}") from exc
    for record in records:
        typer.echo(json.dumps(record, sort_keys=True, separators=(",", ":")))


@app.command("plan")
def plan_command(
    source_id: str = typer.Argument(...),
    target: str = typer.Option("cbm", "--target"),
    work_ref: str = typer.Option(..., "--work-ref"),
    edition_ref: str = typer.Option(..., "--edition-ref"),
    assertion_provenance_ref: str = typer.Option(..., "--assertion-provenance-ref"),
) -> None:
    _, plan = _build_execution_plan(
        source_id,
        target=target,
        work_ref=work_ref,
        edition_ref=edition_ref,
        assertion_provenance_ref=assertion_provenance_ref,
    )
    typer.echo(f"target={plan.target}")
    typer.echo(f"reuse={plan.reuse_count}")
    typer.echo(f"process={plan.process_count}")
    typer.echo(
        "estimated_usage="
        + json.dumps(plan.estimated_usage, sort_keys=True, separators=(",", ":"))
    )


@app.command("run")
def run_command(
    source_id: str = typer.Argument(...),
    target: str = typer.Option("cbm", "--target"),
    work_ref: str = typer.Option(..., "--work-ref"),
    edition_ref: str = typer.Option(..., "--edition-ref"),
    assertion_provenance_ref: str = typer.Option(..., "--assertion-provenance-ref"),
) -> None:
    application, plan = _build_execution_plan(
        source_id,
        target=target,
        work_ref=work_ref,
        edition_ref=edition_ref,
        assertion_provenance_ref=assertion_provenance_ref,
    )
    try:
        result = execute_plan(plan, metadata_store=application.metadata)
    except RuntimeError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"reused={result.reused_activity_count}")
    typer.echo(f"executed={result.executed_activity_count}")
    for ref in result.final_output_refs:
        typer.echo(f"output_ref={ref.id}")


@corpus_app.command("status")
def corpus_status(
    registry: Path = typer.Option(..., "--registry", exists=True, dir_okay=False, readable=True),
) -> None:
    loaded = CorpusRegistry.load(registry)
    typer.echo(
        f"total={loaded.total_cases} "
        f"acquired={loaded.total_acquired} "
        f"quarantined={len(loaded.quarantined_case_ids)}"
    )


@corpus_app.command("ingest")
def corpus_ingest(
    case_id: str = typer.Argument(...),
    registry: Path = typer.Option(..., "--registry", exists=True, dir_okay=False, readable=True),
) -> None:
    try:
        source = _application().ingest_corpus_case(registry, case_id)
    except (QuarantinedCaseError, KeyError, FileNotFoundError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"case_id={case_id}")
    typer.echo(f"source_id={source.id}")
    typer.echo(f"checksum={source.checksum}")


@evidence_app.command("build")
def evidence_build(
    source_id: str = typer.Argument(...),
    adapter: str = typer.Option(..., "--adapter"),
    scope: str = typer.Option("all", "--scope"),
    glyph_runs: bool = typer.Option(False, "--glyph-runs"),
) -> None:
    if adapter not in {"pdf", "markdown"}:
        raise typer.BadParameter("--adapter must be pdf or markdown")
    try:
        snapshot = _application().build_evidence(
            source_id,
            adapter,  # type: ignore[arg-type]
            scope=scope,
            glyph_runs=glyph_runs,
        )
    except (UnknownArtifactError, ValueError, IndexError, TypeError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"snapshot_id={snapshot.id}")
    typer.echo(f"snapshot_digest={snapshot.snapshot_digest}")
    typer.echo(f"partitions={len(snapshot.partition_refs)}")


@evidence_app.command("show")
def evidence_show(snapshot_id: str = typer.Argument(...)) -> None:
    try:
        snapshot = _application().show_snapshot(snapshot_id)
    except (UnknownArtifactError, TypeError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    adapter = snapshot.id.split(":", 2)[1] if snapshot.id.startswith("snapshot:") else "unknown"
    typer.echo(f"snapshot_id={snapshot.id}")
    typer.echo(f"source_id={snapshot.source_artifact_ref}")
    typer.echo(f"adapter={adapter}")
    typer.echo(f"snapshot_digest={snapshot.snapshot_digest}")
    typer.echo(f"partitions={len(snapshot.partition_refs)}")


@candidate_app.command("freeze")
def candidate_freeze(
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
    ),
    regression_report: Path = typer.Option(
        ...,
        "--regression-report",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    git_commit_sha: str = typer.Option(..., "--git-commit-sha"),
    output: Path = typer.Option(..., "--output"),
) -> None:
    try:
        manifest = build_repository_candidate(
            repo_root=repo_root,
            git_commit_sha=git_commit_sha,
            regression_report_path=regression_report,
        )
        artifact = freeze_candidate(manifest, output_path=output)
    except (CandidateReadinessError, FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"candidate_id={artifact.id}")
    typer.echo(f"candidate_digest={artifact.digest}")
    typer.echo(f"output={output}")
