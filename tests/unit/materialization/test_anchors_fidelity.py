from __future__ import annotations

import pytest

from voxcodex.domain.cbm.content import FidelityConstraint
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import NormalizedGeometry
from voxcodex.materialization.anchors import AnchorEvidence, build_source_anchors
from voxcodex.materialization.fidelity import FidelityPolicy, effective_fidelity
from voxcodex.materialization.mappings import (
    RoleProfileRegistry,
    materialize_formula_payload,
    materialize_table_payload,
)
from voxcodex.reconstruction.structured import (
    FormulaCandidate,
    TableCandidate,
    TableCellCandidate,
)


def _eref(name: str) -> ArtifactRef:
    return ArtifactRef(id=f"evidence:{name}", digest=(name[0] * 64), kind="evidence_unit")


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


def test_role_profile_and_fidelity_policy_are_versioned_canonical_artifacts():
    roles = RoleProfileRegistry.v01_defaults()
    fidelity = FidelityPolicy.v01_defaults()

    assert roles.version == "0.1"
    assert fidelity.version == "0.1"
    assert len(roles.artifact_digest) == 64
    assert len(fidelity.artifact_digest) == 64
    assert roles.resolve("drama.speaker_cue") is not None
    assert fidelity.for_role("technical.code_line")


def test_table_candidate_maps_topology_without_owning_content():
    candidate = TableCandidate(
        id="table-candidate:test",
        row_count=1,
        column_count=2,
        cells=(
            TableCellCandidate(row_index=0, column_index=0, surface="0", evidence_refs=(_eref("a"),)),
            TableCellCandidate(row_index=0, column_index=1, surface="11", evidence_refs=(_eref("b"),)),
        ),
        evidence_refs=(_eref("a"), _eref("b")),
        visual_region=NormalizedGeometry(x0=0.1, y0=0.1, x1=0.9, y1=0.2),
    )

    payload = materialize_table_payload(
        candidate,
        content_refs_by_evidence={"evidence:a": "fragment:0", "evidence:b": "fragment:11"},
    )

    assert payload.row_count == 1
    assert payload.column_count == 2
    assert tuple(cell.content_refs for cell in payload.cells) == (("fragment:0",), ("fragment:11",))


def test_formula_candidate_keeps_source_representation_distinct_from_reconstruction():
    candidate = FormulaCandidate(
        id="formula-candidate:test",
        evidence_refs=(_eref("f"),),
        visual_region=NormalizedGeometry(x0=0.2, y0=0.2, x1=0.8, y1=0.4),
        symbolic_representation="x^2",
        detection_basis=("math_glyph_shape",),
    )

    payload = materialize_formula_payload(
        candidate,
        reconstructed_representation_ref="artifact:mathml:test",
    )

    assert payload.source_representation_refs == ("evidence:f",)
    assert payload.reconstructed_representation_refs == ("artifact:mathml:test",)
