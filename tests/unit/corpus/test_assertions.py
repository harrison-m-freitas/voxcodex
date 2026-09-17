from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from voxcodex.corpus.assertions import (
    AssertionRunner,
    AssertionSpec,
    FROZEN_ASSERTION_BINDINGS,
    UnsupportedAssertionOperator,
    load_frozen_assertions,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "corpus" / "manifests" / "M2-REGRESSION-ASSERTIONS-V1.json"
FROZEN_MANIFEST_SHA256 = "60cadbb29497e07c7c9a622337fd4c19df0afd7822948b43c442d3312e8ede9c"


def _spec(operator: str, **params) -> AssertionSpec:
    return AssertionSpec(
        assertion_id=f"SYNTH-{operator}",
        case_id="SYNTH",
        layer="CBM",
        description=f"synthetic {operator} contract",
        blocking=True,
        operator=operator,
        params=params,
    )


def _outputs() -> dict:
    return {
        "nodes": {
            "scene": {"kind": "scene", "parent": None},
            "cue": {"kind": "speaker_cue", "parent": "scene"},
            "speech": {"kind": "speech", "parent": "scene", "surface": "HIPÓLITO"},
        },
        "topologies": {
            "table:w2": {
                "rows": 3,
                "columns": 2,
                "cells": ["r1c1", "r1c2", "r2c1", "r2c2", "r3c1", "r3c2"],
            }
        },
        "relations": [
            {"kind": "spoken_by", "source": "speech", "target": "cue"},
        ],
        "provenance": {
            "node:paragraph": ["reconstruction:1"],
            "reconstruction:1": ["evidence:1"],
            "evidence:1": ["source:1"],
            "source:1": [],
        },
        "validation": {"status": "passed", "blocking_failures": 0},
    }


def test_frozen_assertion_manifest_is_unchanged_and_compiles_all_42_entries() -> None:
    raw = MANIFEST_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FROZEN_MANIFEST_SHA256

    manifest = json.loads(raw)
    specs = load_frozen_assertions(MANIFEST_PATH)

    frozen_ids = {
        assertion["assertion_id"]
        for case in manifest["cases"]
        for assertion in case["assertions"]
    }

    assert manifest["status"] == "FROZEN"
    assert manifest["assertion_count"] == 42
    assert len(specs) == 42
    assert {spec.assertion_id for spec in specs} == frozen_ids
    assert set(FROZEN_ASSERTION_BINDINGS) == frozen_ids
    assert all(spec.description for spec in specs)
    assert all(spec.case_id for spec in specs)


def test_unknown_assertion_operator_is_never_silently_ignored() -> None:
    spec = AssertionSpec(
        assertion_id="SYNTH-A01",
        case_id="SYNTH",
        layer="CBM",
        description="synthetic unknown operator contract",
        blocking=True,
        operator="not_a_real_operator",
        params={},
    )

    with pytest.raises(UnsupportedAssertionOperator, match="not_a_real_operator"):
        AssertionRunner().run(case="SYNTH", outputs={}, assertions=(spec,))


@pytest.mark.parametrize(
    ("spec", "expected_ref"),
    [
        (_spec("structural", path="nodes.speech.kind", equals="speech"), "nodes.speech.kind"),
        (_spec("surface_equals", path="nodes.speech.surface", expected="HIPÓLITO"), "nodes.speech.surface"),
        (
            _spec(
                "topology",
                path="topologies.table:w2",
                rows=3,
                columns=2,
                min_cells=6,
            ),
            "topologies.table:w2",
        ),
        (
            _spec(
                "relation_exists",
                path="relations",
                kind="spoken_by",
                source="speech",
                target="cue",
            ),
            "speech->cue",
        ),
        (
            _spec(
                "provenance_reachable",
                path="provenance",
                start="node:paragraph",
                target="source:1",
            ),
            "node:paragraph->source:1",
        ),
        (_spec("validation_result", path="validation.status", expected="passed"), "validation.status"),
    ],
)
def test_supported_assertion_operators_return_auditable_pass(spec: AssertionSpec, expected_ref: str) -> None:
    [result] = AssertionRunner().run(case="SYNTH", outputs=_outputs(), assertions=(spec,))

    assert result.status == "PASS"
    assert result.case_id == "SYNTH"
    assert result.assertion_id == spec.assertion_id
    assert expected_ref in result.affected_refs
    assert result.diagnostic


def test_negative_operator_passes_only_when_nested_condition_is_absent() -> None:
    spec = _spec(
        "negative",
        operator_spec={
            "operator": "relation_exists",
            "params": {
                "path": "relations",
                "kind": "fabricated_entry",
                "source": "scene",
                "target": "character",
            },
        },
    )

    [result] = AssertionRunner().run(case="SYNTH", outputs=_outputs(), assertions=(spec,))

    assert result.status == "PASS"
    assert result.diagnostic


def test_failed_assertion_is_explicit_not_silent() -> None:
    spec = _spec("surface_equals", path="nodes.speech.surface", expected="ARÍCIA")

    [result] = AssertionRunner().run(case="SYNTH", outputs=_outputs(), assertions=(spec,))

    assert result.status == "FAIL"
    assert result.diagnostic
