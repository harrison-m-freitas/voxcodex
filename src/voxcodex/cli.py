from pathlib import Path

import typer

from voxcodex.corpus.registry import CorpusRegistry

app = typer.Typer(name="voxcodex", no_args_is_help=True)
corpus_app = typer.Typer(name="corpus", no_args_is_help=True)
app.add_typer(corpus_app, name="corpus")


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
