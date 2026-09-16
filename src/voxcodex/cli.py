from __future__ import annotations

import os
from pathlib import Path

import typer

from voxcodex.application.evidence import (
    DirectCorpusSourceError,
    EvidenceApplication,
    UnknownArtifactError,
)
from voxcodex.corpus.holdouts import QuarantinedCaseError
from voxcodex.corpus.registry import CorpusRegistry

app = typer.Typer(name="voxcodex", no_args_is_help=True)
corpus_app = typer.Typer(name="corpus", no_args_is_help=True)
evidence_app = typer.Typer(name="evidence", no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")
app.add_typer(evidence_app, name="evidence")


def _application() -> EvidenceApplication:
    home = Path(os.environ.get("VOXCODEX_HOME", ".voxcodex"))
    return EvidenceApplication(home)


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
