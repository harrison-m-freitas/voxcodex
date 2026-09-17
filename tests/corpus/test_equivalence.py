from __future__ import annotations

import json
from pathlib import Path

from voxcodex.corpus.equivalence import (
    canonical_structure_signature,
    compare_canonical_structures,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "corpus" / "COMPATIBILITY-CORPUS-V1.json"


def _document(*, ids: tuple[str, str], paragraph_surface: str) -> dict:
    root_id, paragraph_id = ids
    return {
        "revision_id": f"revision:{root_id}",
        "activity_ref": f"activity:{root_id}",
        "source_locators": [{"page": 1, "bbox": [0.1, 0.2, 0.8, 0.9]}],
        "nodes": [
            {
                "id": root_id,
                "parent_ref": None,
                "node_class": "division",
                "role": "chapter",
                "surface": "Chapter I",
                "source_anchor_refs": [f"anchor:{root_id}"],
            },
            {
                "id": paragraph_id,
                "parent_ref": root_id,
                "node_class": "block",
                "role": "paragraph",
                "surface": paragraph_surface,
                "source_anchor_refs": [f"anchor:{paragraph_id}"],
            },
        ],
        "topologies": [
            {
                "id": f"table:{root_id}",
                "kind": "table",
                "rows": 2,
                "columns": 2,
                "cells": ["a", "b", "c", "d"],
                "source_ref": f"source:{root_id}",
            }
        ],
    }


def test_canonical_signature_ignores_operational_ids_and_source_locators() -> None:
    left = _document(ids=("left-root", "left-p"), paragraph_surface="Hello   world")
    right = _document(ids=("right-root", "right-p"), paragraph_surface="Hello world")

    assert canonical_structure_signature(left) == canonical_structure_signature(right)


def test_canonical_signature_detects_source_supported_surface_difference() -> None:
    left = _document(ids=("left-root", "left-p"), paragraph_surface="Hello world")
    right = _document(ids=("right-root", "right-p"), paragraph_surface="Hello there")

    assert canonical_structure_signature(left) != canonical_structure_signature(right)


def test_supported_pair_compares_canonical_structure_not_serialization_bytes() -> None:
    left = _document(ids=("left-root", "left-p"), paragraph_surface="Hello   world")
    right = _document(ids=("right-root", "right-p"), paragraph_surface="Hello world")

    result = compare_canonical_structures(
        left,
        right,
        left_supported=True,
        right_supported=True,
    )

    assert result.status == "EQUIVALENT"
    assert result.left_signature == result.right_signature
    assert result.diagnostic


def test_unsupported_pair_is_explicitly_deferred_without_comparison() -> None:
    result = compare_canonical_structures(
        {},
        {},
        left_supported=True,
        right_supported=False,
    )

    assert result.status == "DEFERRED_BY_SUPPORT_TIER"
    assert result.left_signature is None
    assert result.right_signature is None


def test_available_non_holdout_cross_format_pairs_are_deferred_when_a_member_is_unsupported() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    cases = {case["corpus_case_id"]: case for case in registry["cases"]}
    holdouts = set(registry["blind_holdouts"]["reserved_case_ids"])
    pairs = (("CC-16", "CC-17"), ("CC-19", "CC-20"), ("CC-23", "CC-24"))

    def supported(case: dict) -> bool:
        tier1 = case["support_tier"].casefold() == "tier 1"
        fmt = case["acquired_manifestation_format"].casefold()
        return tier1 and ("pdf" in fmt or "markdown" in fmt)

    for left_id, right_id in pairs:
        assert left_id not in holdouts
        assert right_id not in holdouts
        result = compare_canonical_structures(
            {},
            {},
            left_supported=supported(cases[left_id]),
            right_supported=supported(cases[right_id]),
        )
        assert result.status == "DEFERRED_BY_SUPPORT_TIER"
