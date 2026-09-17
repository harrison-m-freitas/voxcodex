from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.reconstruction import (
    OpenStructuralState,
    ReconstructionIssue,
    ReconstructionSnapshot,
    ReconstructionUnit,
    StageResult,
)


def test_reconstruction_unit_parent_and_order_are_normative_authority():
    unit = ReconstructionUnit(
        id="reconstruction-unit:1",
        reconstruction_snapshot_ref="reconstruction-snapshot:1",
        parent_ref="reconstruction-unit:root",
        order_key="000001",
        reconstruction_class="block_candidate",
        evidence_refs=(ArtifactRef(id="evidence:1", digest="a" * 64, kind="evidence_unit"),),
        properties={"candidate_kind": "paragraph"},
        provenance_ref="derivation:1",
    )

    assert unit.parent_ref == "reconstruction-unit:root"
    assert unit.order_key == "000001"
    assert "child_refs" not in ReconstructionUnit.model_fields

    with pytest.raises(ValidationError):
        unit.order_key = "000002"


def test_snapshot_stage_result_and_operational_state_are_frozen():
    snapshot = ReconstructionSnapshot(
        id="reconstruction-snapshot:1",
        source_evidence_refs=(
            ArtifactRef(id="evidence-snapshot:1", digest="b" * 64, kind="evidence_snapshot"),
        ),
        reconstruction_activity_ref="activity:reconstruction:1",
        reconstruction_profile_ref="reconstruction-profile:test",
        root_unit_refs=("reconstruction-unit:root",),
        reconstruction_validation_ref=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
        snapshot_digest="c" * 64,
    )
    state = OpenStructuralState(
        open_units=("reconstruction-unit:open",),
        pending_continuations=("continuation:1",),
        unresolved_boundaries=("boundary:1",),
    )
    issue = ReconstructionIssue(
        id="reconstruction-issue:1",
        issue_type="ambiguous_reading_order",
        severity="warning",
        affected_refs=("reconstruction-unit:1",),
        message="Two reading orders remain plausible.",
        suggested_action="review_region",
    )
    result = StageResult(units=(), issues=(issue,), open_state=state)

    with pytest.raises(ValidationError):
        snapshot.snapshot_digest = "d" * 64
    with pytest.raises(ValidationError):
        result.units = ()
    with pytest.raises(ValidationError):
        state.open_units = ()


def test_reconstruction_class_rejects_unknown_values():
    with pytest.raises(ValidationError):
        ReconstructionUnit(
            id="reconstruction-unit:bad",
            reconstruction_snapshot_ref="reconstruction-snapshot:1",
            parent_ref=None,
            order_key="000001",
            reconstruction_class="paragraph",
            evidence_refs=(),
            provenance_ref="derivation:bad",
        )
