from __future__ import annotations

import pytest

from voxcodex.domain.cbm.content import FidelityConstraint
from voxcodex.materialization.anchors import AnchorEvidence, build_source_anchors
from voxcodex.materialization.fidelity import effective_fidelity


def test_cross_page_object_materializes_two_physical_source_anchors():
    evidence = (
        AnchorEvidence(
            evidence_ref="evidence:p10:last",
            source_artifact_ref="source:fedra",
            extraction_ref="activity:extract:fedra",
            source_page_index=9,
            printed_page_label="10",
            x0=0.10,
            y0=0.80,
            x1=0.90,
            y1=0.90,
        ),
        AnchorEvidence(
            evidence_ref="evidence:p11:first",
            source_artifact_ref="source:fedra",
            extraction_ref="activity:extract:fedra",
            source_page_index=10,
            printed_page_label="11",
            x0=0.10,
            y0=0.10,
            x1=0.90,
            y1=0.20,
        ),
    )

    anchors = build_source_anchors("node:speech", evidence)

    assert len(anchors) == 2
    assert tuple(anchor.locator.source_page_index for anchor in anchors) == (9, 10)
    assert tuple(anchor.printed_page_label for anchor in (a.locator for a in anchors)) == ("10", "11")
    assert all(anchor.source_artifact_ref == "source:fedra" for anchor in anchors)


def test_effective_fidelity_inherits_and_child_can_strengthen():
    inherited = (
        FidelityConstraint(dimension="lexical", requirement="preserve_exactly"),
        FidelityConstraint(dimension="ordering", requirement="preserve_exactly"),
    )
    local = (
        FidelityConstraint(dimension="character", requirement="preserve_exactly"),
    )

    effective = effective_fidelity(inherited, local)

    assert {constraint.dimension for constraint in effective} == {
        "lexical",
        "ordering",
        "character",
    }


def test_effective_fidelity_rejects_explicit_weakening_attempt():
    inherited = (
        FidelityConstraint(dimension="character", requirement="preserve_exactly"),
    )

    with pytest.raises(ValueError, match="cannot weaken inherited fidelity"):
        effective_fidelity(
            inherited,
            (),
            weakening_dimensions=("character",),
        )
