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
