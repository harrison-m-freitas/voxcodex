from __future__ import annotations

from pathlib import Path

import pytest

from voxcodex.corpus.holdouts import HoldoutGuard
from voxcodex.corpus.registry import CorpusRegistry
from voxcodex.corpus.runner import CorpusRunner, ProcessorOutcome


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "corpus" / "COMPATIBILITY-CORPUS-V1.json"


def test_all_26_non_holdout_cases_receive_explicit_support_classification() -> None:
    registry = CorpusRegistry.load(REGISTRY_PATH)
    guard = HoldoutGuard(registry.quarantined_case_ids)
    touched: list[str] = []

    def support_dispatch_probe(case, source_path: Path) -> ProcessorOutcome:
        touched.append(case.case_id)
        return ProcessorOutcome(
            result_class="PASS",
            diagnostic="Tier 1 PDF/Markdown case dispatched to the supported processing surface",
            evidence_refs=(f"corpus:{case.case_id}:registered-source",),
        )

    runner = CorpusRunner(registry=registry, guard=guard, processor=support_dispatch_probe)
    non_holdout_ids = sorted(registry.case_ids - registry.quarantined_case_ids)
    results = [runner.run_case(case_id) for case_id in non_holdout_ids]

    assert len(non_holdout_ids) == 26
    assert len(results) == 26
    assert not registry.quarantined_case_ids.intersection(result.case_id for result in results)
    assert all(result.result_class for result in results)

    tier1_results = [result for result in results if result.support_tier == "Tier 1"]
    assert tier1_results
    assert all(result.result_class == "PASS" for result in tier1_results)

    deferred = [result for result in results if result.result_class == "DEFERRED_BY_SUPPORT_TIER"]
    assert deferred
    assert all(result.source_resolved is False for result in deferred)

    assert set(touched) == {
        result.case_id
        for result in results
        if result.result_class != "DEFERRED_BY_SUPPORT_TIER"
    }


def test_non_holdout_supported_source_artifacts_exist_when_local_corpus_is_mounted() -> None:
    registry = CorpusRegistry.load(REGISTRY_PATH)
    guard = HoldoutGuard(registry.quarantined_case_ids)
    missing: list[str] = []
    checked: list[str] = []

    def availability_probe(case, source_path: Path) -> ProcessorOutcome:
        checked.append(case.case_id)
        if not source_path.is_file():
            missing.append(f"{case.case_id}:{source_path}")
        return ProcessorOutcome(
            result_class="PASS",
            diagnostic="physical source availability probe",
        )

    runner = CorpusRunner(registry=registry, guard=guard, processor=availability_probe)
    for case_id in sorted(registry.case_ids - registry.quarantined_case_ids):
        runner.run_case(case_id)

    assert checked
    if missing:
        pytest.skip(
            "local compatibility SourceArtifacts are not mounted in CI: "
            + ", ".join(missing)
        )

    assert not missing
