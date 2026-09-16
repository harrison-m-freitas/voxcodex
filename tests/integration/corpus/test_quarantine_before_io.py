from pathlib import Path

import pytest

from voxcodex.corpus.holdouts import HoldoutGuard, QuarantinedCaseError
from voxcodex.corpus.registry import CorpusRegistry


def test_quarantined_source_resolution_fails_before_path_open(monkeypatch):
    registry = CorpusRegistry.load(Path("corpus/COMPATIBILITY-CORPUS-V1.json"))
    guard = HoldoutGuard(registry.quarantined_case_ids, revealed=False)
    opened = []

    def forbidden_open(self, *args, **kwargs):
        opened.append(self)
        raise AssertionError("Path.open must not run for a quarantined case")

    monkeypatch.setattr(Path, "open", forbidden_open)

    with pytest.raises(QuarantinedCaseError):
        registry.resolve_primary_source_path("CC-05", guard, operation="extract")

    assert opened == []
