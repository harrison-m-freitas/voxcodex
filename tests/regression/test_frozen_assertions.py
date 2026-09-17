from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from voxcodex.corpus.assertions import AssertionRunner, load_frozen_assertions


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "corpus" / "manifests" / "M2-REGRESSION-ASSERTIONS-V1.json"

# These are the pre-holdout known-regression observations corresponding to the
# frozen semantic expectations. They deliberately contain semantic assertion
# outcomes, not serialized CBM snapshots or operational object IDs.
KNOWN_REGRESSION_FACTS: dict[str, frozenset[str]] = {
    "F1": frozenset({"F1-A01", "F1-A02", "F1-A03", "F1-A04", "F1-A05"}),
    "F2": frozenset({"F2-A01", "F2-A02", "F2-A03", "F2-A04"}),
    "W1": frozenset({"W1-A01", "W1-A02", "W1-A03", "W1-A04", "W1-A05"}),
    "W2": frozenset({"W2-A01", "W2-A02", "W2-A03", "W2-A04"}),
    "C1": frozenset({"C1-A01", "C1-A02", "C1-A03", "C1-A04", "C1-A05"}),
    "C2": frozenset({"C2-A01", "C2-A02", "C2-A03", "C2-A04", "C2-A05"}),
    "C3": frozenset({"C3-A01", "C3-A02", "C3-A03", "C3-A04", "C3-A05"}),
    "F-RND": frozenset({"FR-A01", "FR-A02", "FR-A03", "FR-A04"}),
    "W-RND": frozenset({"WR-A01", "WR-A02", "WR-A03", "WR-A04", "WR-A05"}),
}


def test_all_42_frozen_assertions_execute_against_known_regression_observations() -> None:
    specs = load_frozen_assertions(MANIFEST_PATH)
    by_case = defaultdict(list)
    for spec in specs:
        by_case[spec.case_id].append(spec)

    assert set(by_case) == set(KNOWN_REGRESSION_FACTS)
    assert sum(len(facts) for facts in KNOWN_REGRESSION_FACTS.values()) == 42

    runner = AssertionRunner()
    results = []
    for case_id, case_specs in by_case.items():
        facts = KNOWN_REGRESSION_FACTS[case_id]
        assert {spec.assertion_id for spec in case_specs} == set(facts)
        outputs = {"assertion_facts": {assertion_id: True for assertion_id in facts}}
        results.extend(runner.run(case_id, outputs, tuple(case_specs)))

    assert len(results) == 42
    assert all(result.status == "PASS" for result in results)
    assert all(result.affected_refs for result in results)
    assert all(result.diagnostic for result in results)
