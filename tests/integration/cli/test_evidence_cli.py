from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from voxcodex.cli import app


runner = CliRunner()


def _value(output: str, key: str) -> str:
    for line in output.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    raise AssertionError(f"missing {key}=... in output:\n{output}")


def test_ingest_build_and_show_markdown_evidence(tmp_path: Path, monkeypatch):
    home = tmp_path / "workspace"
    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    source_path = tmp_path / "chapter.md"
    source_path.write_text("# Titulo\n\nTexto fiel.\n", encoding="utf-8")

    ingested = runner.invoke(app, ["ingest", str(source_path)])
    assert ingested.exit_code == 0, ingested.output
    source_id = _value(ingested.output, "source_id")
    assert source_id.startswith("source:")

    built = runner.invoke(
        app,
        ["evidence", "build", source_id, "--adapter", "markdown"],
    )
    assert built.exit_code == 0, built.output
    snapshot_id = _value(built.output, "snapshot_id")
    assert snapshot_id.startswith("snapshot:markdown:")
    assert len(_value(built.output, "snapshot_digest")) == 64
    assert _value(built.output, "partitions") == "1"

    shown = runner.invoke(app, ["evidence", "show", snapshot_id])
    assert shown.exit_code == 0, shown.output
    assert f"snapshot_id={snapshot_id}" in shown.output
    assert f"source_id={source_id}" in shown.output
    assert "adapter=markdown" in shown.output
    assert "partitions=1" in shown.output


def test_ingest_is_idempotent_for_same_source_bytes(tmp_path: Path, monkeypatch):
    home = tmp_path / "workspace"
    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    source_path = tmp_path / "same.md"
    source_path.write_text("texto\n", encoding="utf-8")

    first = runner.invoke(app, ["ingest", str(source_path)])
    second = runner.invoke(app, ["ingest", str(source_path)])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert _value(first.output, "source_id") == _value(second.output, "source_id")


def test_pdf_build_scope_selects_requested_page(tmp_path: Path, monkeypatch):
    import pymupdf

    home = tmp_path / "workspace"
    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    source_path = tmp_path / "two-pages.pdf"
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "page zero")
    document.new_page().insert_text((72, 72), "page one")
    document.save(source_path)
    document.close()

    ingested = runner.invoke(app, ["ingest", str(source_path)])
    assert ingested.exit_code == 0, ingested.output
    source_id = _value(ingested.output, "source_id")

    built = runner.invoke(
        app,
        [
            "evidence",
            "build",
            source_id,
            "--adapter",
            "pdf",
            "--scope",
            "1",
        ],
    )
    assert built.exit_code == 0, built.output
    assert _value(built.output, "partitions") == "1"
