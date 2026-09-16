from pathlib import Path

import pytest
from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.corpus.holdouts import HoldoutGuard, QuarantinedCaseError
from voxcodex.corpus.registry import CorpusRegistry


def test_holdout_guard_blocks_frozen_cases():
    guard = HoldoutGuard({"CC-05", "CC-07", "CC-14", "CC-18"}, revealed=False)
    with pytest.raises(QuarantinedCaseError):
        guard.assert_allowed("CC-14", "extract")
    guard.assert_allowed("CC-03", "extract")


def test_registry_loads_frozen_counts_without_source_access():
    registry = CorpusRegistry.load(Path("corpus/COMPATIBILITY-CORPUS-V1.json"))
    assert registry.total_cases == 30
    assert registry.total_acquired == 30
    assert registry.quarantined_case_ids == {"CC-05", "CC-07", "CC-14", "CC-18"}


def test_cli_corpus_status_reports_counts():
    result = CliRunner().invoke(
        app,
        ["corpus", "status", "--registry", "corpus/COMPATIBILITY-CORPUS-V1.json"],
    )
    assert result.exit_code == 0
    assert "total=30" in result.stdout
    assert "acquired=30" in result.stdout
    assert "quarantined=4" in result.stdout
