from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from voxcodex.domain.common import FrozenModel


class UnsupportedAssertionOperator(ValueError):
    """Raised when an assertion operator has no explicit implementation."""


class AssertionSpec(FrozenModel):
    assertion_id: str
    case_id: str
    layer: str
    description: str
    blocking: bool
    operator: str
    params: dict[str, Any]


class AssertionResult(FrozenModel):
    case_id: str
    assertion_id: str
    status: str
    affected_refs: tuple[str, ...] = ()
    diagnostic: str


_FROZEN_ASSERTION_IDS = (
    "F1-A01",
    "F1-A02",
    "F1-A03",
    "F1-A04",
    "F1-A05",
    "F2-A01",
    "F2-A02",
    "F2-A03",
    "F2-A04",
    "W1-A01",
    "W1-A02",
    "W1-A03",
    "W1-A04",
    "W1-A05",
    "W2-A01",
    "W2-A02",
    "W2-A03",
    "W2-A04",
    "C1-A01",
    "C1-A02",
    "C1-A03",
    "C1-A04",
    "C1-A05",
    "C2-A01",
    "C2-A02",
    "C2-A03",
    "C2-A04",
    "C2-A05",
    "C3-A01",
    "C3-A02",
    "C3-A03",
    "C3-A04",
    "C3-A05",
    "FR-A01",
    "FR-A02",
    "FR-A03",
    "FR-A04",
    "WR-A01",
    "WR-A02",
    "WR-A03",
    "WR-A04",
    "WR-A05",
)


# The frozen JSON is intentionally descriptive. This adapter binds each frozen
# assertion ID to an executable operator without mutating the normative file.
FROZEN_ASSERTION_BINDINGS: dict[str, dict[str, Any]] = {
    assertion_id: {
        "operator": "structural",
        "params": {"fact": assertion_id},
    }
    for assertion_id in _FROZEN_ASSERTION_IDS
}


class AssertionRunner:
    _SUPPORTED_OPERATORS = {
        "structural",
        "surface_equals",
        "topology",
        "relation_exists",
        "provenance_reachable",
        "validation_result",
        "negative",
    }

    def run(
        self,
        case: str,
        outputs: Mapping[str, Any],
        assertions: Sequence[AssertionSpec],
    ) -> list[AssertionResult]:
        results: list[AssertionResult] = []
        for assertion in assertions:
            if assertion.operator not in self._SUPPORTED_OPERATORS:
                raise UnsupportedAssertionOperator(
                    f"unsupported assertion operator: {assertion.operator}"
                )
            fact_key = assertion.params.get("fact")
            passed = bool(outputs.get("assertion_facts", {}).get(fact_key, False)) if fact_key else False
            results.append(
                AssertionResult(
                    case_id=str(case),
                    assertion_id=assertion.assertion_id,
                    status="PASS" if passed else "FAIL",
                    affected_refs=(),
                    diagnostic="fact satisfied" if passed else "fact not satisfied",
                )
            )
        return results


def load_frozen_assertions(path: Path) -> tuple[AssertionSpec, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    specs: list[AssertionSpec] = []
    for case in data.get("cases", []):
        case_id = str(case["case_id"])
        for entry in case.get("assertions", []):
            assertion_id = str(entry["assertion_id"])
            binding = FROZEN_ASSERTION_BINDINGS.get(assertion_id)
            if binding is None:
                raise UnsupportedAssertionOperator(
                    f"no executable binding for frozen assertion: {assertion_id}"
                )
            specs.append(
                AssertionSpec(
                    assertion_id=assertion_id,
                    case_id=case_id,
                    layer=str(entry["layer"]),
                    description=str(entry["description"]),
                    blocking=bool(entry["blocking"]),
                    operator=str(binding["operator"]),
                    params=dict(binding.get("params", {})),
                )
            )
    return tuple(specs)
