from __future__ import annotations

import json
from collections import deque
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
        case_id = str(getattr(case, "case_id", case))
        for assertion in assertions:
            passed, affected_refs, diagnostic = self._evaluate(
                assertion.operator,
                assertion.params,
                outputs,
            )
            results.append(
                AssertionResult(
                    case_id=case_id,
                    assertion_id=assertion.assertion_id,
                    status="PASS" if passed else "FAIL",
                    affected_refs=affected_refs,
                    diagnostic=diagnostic,
                )
            )
        return results

    def _evaluate(
        self,
        operator: str,
        params: Mapping[str, Any],
        outputs: Mapping[str, Any],
    ) -> tuple[bool, tuple[str, ...], str]:
        if operator not in self._SUPPORTED_OPERATORS:
            raise UnsupportedAssertionOperator(f"unsupported assertion operator: {operator}")

        fact_key = params.get("fact")
        if fact_key is not None:
            passed = bool(outputs.get("assertion_facts", {}).get(fact_key, False))
            return (
                passed,
                (str(fact_key),),
                f"fact {fact_key!r} {'satisfied' if passed else 'not satisfied'}",
            )

        if operator == "negative":
            nested = params.get("operator_spec")
            if not isinstance(nested, Mapping):
                return False, (), "negative assertion requires operator_spec"
            nested_operator = str(nested.get("operator", ""))
            nested_params = nested.get("params", {})
            if not isinstance(nested_params, Mapping):
                return False, (), "negative assertion operator_spec.params must be a mapping"
            nested_passed, refs, nested_diagnostic = self._evaluate(
                nested_operator,
                nested_params,
                outputs,
            )
            passed = not nested_passed
            return passed, refs, f"negative {'satisfied' if passed else 'failed'}: {nested_diagnostic}"

        if operator in {"structural", "surface_equals", "validation_result"}:
            path = str(params.get("path", ""))
            expected_key = "equals" if operator == "structural" else "expected"
            expected = params.get(expected_key)
            found, value = _resolve_path(outputs, path)
            passed = found and value == expected
            return (
                passed,
                (path,) if path else (),
                f"{path} expected {expected!r}; got {value!r}" if found else f"path not found: {path}",
            )

        if operator == "topology":
            path = str(params.get("path", ""))
            found, value = _resolve_path(outputs, path)
            if not found or not isinstance(value, Mapping):
                return False, (path,) if path else (), f"topology not found at {path}"
            checks = []
            if "rows" in params:
                checks.append(value.get("rows") == params["rows"])
            if "columns" in params:
                checks.append(value.get("columns") == params["columns"])
            if "min_cells" in params:
                cells = value.get("cells", ())
                checks.append(isinstance(cells, Sequence) and len(cells) >= int(params["min_cells"]))
            passed = bool(checks) and all(checks)
            return passed, (path,), f"topology at {path} {'satisfied' if passed else 'did not satisfy'} constraints"

        if operator == "relation_exists":
            path = str(params.get("path", "relations"))
            found, relations = _resolve_path(outputs, path)
            source = str(params.get("source", ""))
            target = str(params.get("target", ""))
            kind = params.get("kind")
            ref = f"{source}->{target}"
            if not found or not isinstance(relations, Sequence):
                return False, (ref,), f"relation collection not found at {path}"
            passed = any(
                isinstance(relation, Mapping)
                and relation.get("kind") == kind
                and relation.get("source") == source
                and relation.get("target") == target
                for relation in relations
            )
            return passed, (ref,), f"relation {kind!r} {ref} {'exists' if passed else 'missing'}"

        if operator == "provenance_reachable":
            path = str(params.get("path", "provenance"))
            found, graph = _resolve_path(outputs, path)
            start = str(params.get("start", ""))
            target = str(params.get("target", ""))
            ref = f"{start}->{target}"
            if not found or not isinstance(graph, Mapping):
                return False, (ref,), f"provenance graph not found at {path}"
            passed = _reachable(graph, start, target)
            return passed, (ref,), f"provenance {ref} {'reachable' if passed else 'not reachable'}"

        raise UnsupportedAssertionOperator(f"unsupported assertion operator: {operator}")


def _resolve_path(root: Any, path: str) -> tuple[bool, Any]:
    if not path:
        return False, None
    value = root
    for part in path.split("."):
        if isinstance(value, Mapping) and part in value:
            value = value[part]
            continue
        if hasattr(value, part):
            value = getattr(value, part)
            continue
        return False, None
    return True, value


def _reachable(graph: Mapping[str, Any], start: str, target: str) -> bool:
    if start == target:
        return True
    queue: deque[str] = deque([start])
    seen = {start}
    while queue:
        current = queue.popleft()
        neighbours = graph.get(current, ())
        if isinstance(neighbours, str) or not isinstance(neighbours, Sequence):
            neighbours = ()
        for neighbour in neighbours:
            neighbour = str(neighbour)
            if neighbour == target:
                return True
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return False


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
