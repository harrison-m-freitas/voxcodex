from __future__ import annotations

from sqlalchemy import create_engine, func, select
from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.storage.schema import processing_activities


runner = CliRunner()


def test_plan_cli_reports_reuse_process_and_estimated_usage_without_executing(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    source_path = tmp_path / "book.md"
    source_path.write_text("# Chapter\n\nParagraph.\n", encoding="utf-8")

    ingest = runner.invoke(app, ["ingest", str(source_path)])
    assert ingest.exit_code == 0, ingest.output
    source_id = next(
        line.split("=", 1)[1]
        for line in ingest.output.splitlines()
        if line.startswith("source_id=")
    )

    result = runner.invoke(
        app,
        [
            "plan",
            source_id,
            "--target",
            "cbm",
            "--work-ref",
            "work:cli-test",
            "--edition-ref",
            "edition:cli-test",
            "--assertion-provenance-ref",
            "assertion:cli-test",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "reuse=0" in result.output
    assert "process=3" in result.output
    assert "estimated_usage=" in result.output

    engine = create_engine(f"sqlite:///{home / 'metadata.db'}")
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(processing_activities)) == 0


def test_run_cli_refuses_unbound_processor_work_instead_of_fabricating_execution(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    source_path = tmp_path / "book.md"
    source_path.write_text("Paragraph.\n", encoding="utf-8")
    ingest = runner.invoke(app, ["ingest", str(source_path)])
    source_id = next(
        line.split("=", 1)[1]
        for line in ingest.output.splitlines()
        if line.startswith("source_id=")
    )

    result = runner.invoke(
        app,
        [
            "run",
            source_id,
            "--target",
            "cbm",
            "--work-ref",
            "work:cli-test",
            "--edition-ref",
            "edition:cli-test",
            "--assertion-provenance-ref",
            "assertion:cli-test",
        ],
    )

    assert result.exit_code != 0
    assert "requires processor work" in result.output

    engine = create_engine(f"sqlite:///{home / 'metadata.db'}")
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(processing_activities)) == 0
