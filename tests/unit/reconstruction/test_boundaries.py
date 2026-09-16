from __future__ import annotations

import pytest

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.reconstruction import OpenStructuralState
from voxcodex.reconstruction.boundaries import (
    BoundaryFragment,
    collapse_recurrent_editorial,
    reconcile_partition,
)


def _ref(name: str) -> ArtifactRef:
    return ArtifactRef(id=f"evidence:{name}", digest=(name[0] * 64), kind="evidence_unit")


@pytest.mark.parametrize("boundary_kind", ["page", "worker_chunk"])
def test_open_paragraph_reconciles_identically_across_operational_boundary(boundary_kind: str):
    first = BoundaryFragment(
        id="fragment:first",
        structural_kind="paragraph",
        surface="A reconstrução atravessa",
        evidence_refs=(_ref("alpha"),),
        opens_continuation=True,
    )
    second = BoundaryFragment(
        id="fragment:second",
        structural_kind="paragraph",
        surface="o limite operacional.",
        evidence_refs=(_ref("beta"),),
        closes_continuation=True,
    )

    first_result = reconcile_partition(
        (first,),
        OpenStructuralState(),
        boundary_kind=boundary_kind,
    )
    assert first_result.blocks == ()
    assert len(first_result.open_state.continuations) == 1

    final_result = reconcile_partition(
        (second,),
        first_result.open_state,
        boundary_kind=boundary_kind,
    )

    assert len(final_result.blocks) == 1
    block = final_result.blocks[0]
    assert block.structural_kind == "paragraph"
    assert block.surface == "A reconstrução atravessa o limite operacional."
    assert tuple(ref.id for ref in block.evidence_refs) == ("evidence:alpha", "evidence:beta")
    assert final_result.open_state.continuations == ()


@pytest.mark.parametrize("structural_kind", ["speech", "note"])
def test_nonparagraph_open_structures_preserve_kind_and_evidence(structural_kind: str):
    first = BoundaryFragment(
        id=f"fragment:{structural_kind}:first",
        structural_kind=structural_kind,
        surface="Primeira parte",
        evidence_refs=(_ref("gamma"),),
        opens_continuation=True,
    )
    second = BoundaryFragment(
        id=f"fragment:{structural_kind}:second",
        structural_kind=structural_kind,
        surface="segunda parte",
        evidence_refs=(_ref("delta"),),
        closes_continuation=True,
    )

    pending = reconcile_partition((first,), OpenStructuralState(), boundary_kind="page")
    final = reconcile_partition((second,), pending.open_state, boundary_kind="page")

    assert final.blocks[0].structural_kind == structural_kind
    assert final.blocks[0].surface == "Primeira parte segunda parte"
    assert tuple(ref.id for ref in final.blocks[0].evidence_refs) == (
        "evidence:gamma",
        "evidence:delta",
    )


def test_unmatched_closing_fragment_emits_issue_instead_of_dropping_evidence():
    closing = BoundaryFragment(
        id="fragment:orphan",
        structural_kind="paragraph",
        surface="continuação sem estado anterior",
        evidence_refs=(_ref("epsilon"),),
        closes_continuation=True,
    )

    result = reconcile_partition((closing,), OpenStructuralState(), boundary_kind="page")

    assert len(result.blocks) == 1
    assert result.blocks[0].surface == closing.surface
    assert len(result.issues) == 1
    assert result.issues[0].issue_type == "unresolved_boundary"
    assert result.issues[0].affected_refs == (closing.id,)


def test_recurrent_editorial_material_is_one_logical_candidate_with_all_evidence():
    headers = (
        BoundaryFragment(
            id="header:1",
            structural_kind="running_header",
            surface="CAPÍTULO EXPERIMENTAL",
            evidence_refs=(_ref("zeta"),),
            recurrence_key="header:chapter-experimental",
        ),
        BoundaryFragment(
            id="header:2",
            structural_kind="running_header",
            surface="CAPÍTULO EXPERIMENTAL",
            evidence_refs=(_ref("eta"),),
            recurrence_key="header:chapter-experimental",
        ),
        BoundaryFragment(
            id="header:3",
            structural_kind="running_header",
            surface="CAPÍTULO EXPERIMENTAL",
            evidence_refs=(_ref("theta"),),
            recurrence_key="header:chapter-experimental",
        ),
    )

    collapsed = collapse_recurrent_editorial(headers)

    assert len(collapsed) == 1
    assert collapsed[0].structural_kind == "running_header"
    assert collapsed[0].surface == "CAPÍTULO EXPERIMENTAL"
    assert collapsed[0].occurrence_count == 3
    assert tuple(ref.id for ref in collapsed[0].evidence_refs) == (
        "evidence:zeta",
        "evidence:eta",
        "evidence:theta",
    )
