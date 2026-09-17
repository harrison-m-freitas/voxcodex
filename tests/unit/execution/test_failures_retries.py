from __future__ import annotations

import pytest
from pydantic import ValidationError

from voxcodex.domain.common import ArtifactRef
from voxcodex.execution.failures import (
    ExecutionFailure,
    FailureClass,
    ReproducibilityClass,
    RetryPolicy,
)
from voxcodex.execution.runner import ExecutionOutputComponent, ExecutionOutputManifest


def test_reproducibility_classes_match_m2_contract():
    assert {item.value for item in ReproducibilityClass} == {
        "deterministic",
        "seeded",
        "non_deterministic",
        "externally_variable",
    }


def test_transient_failure_can_retry_but_permanent_classes_cannot_blind_retry():
    policy = RetryPolicy(max_attempts=3)

    transient = policy.decide(
        ExecutionFailure(failure_class=FailureClass.TRANSIENT, code="timeout", message="timeout"),
        attempt=1,
    )
    assert transient.should_retry is True
    assert transient.next_attempt == 2

    for failure_class in (
        FailureClass.PERMANENT_INPUT,
        FailureClass.PROCESSOR_BUG,
        FailureClass.POLICY_BLOCK,
    ):
        decision = policy.decide(
            ExecutionFailure(
                failure_class=failure_class,
                code="blocked",
                message="not blind-retryable",
            ),
            attempt=1,
        )
        assert decision.should_retry is False
        assert decision.next_attempt is None


def test_retry_budget_stops_transient_failure_after_max_attempts():
    policy = RetryPolicy(max_attempts=2)
    failure = ExecutionFailure(
        failure_class=FailureClass.TRANSIENT,
        code="timeout",
        message="timeout",
    )

    assert policy.decide(failure, attempt=1).should_retry is True
    assert policy.decide(failure, attempt=2).should_retry is False


def test_partial_output_manifest_reuses_only_complete_components_and_never_incomplete_aggregate():
    page_1 = ArtifactRef(id="page:1", digest="1" * 64, kind="evidence_partition")
    page_2 = ArtifactRef(id="page:2", digest="2" * 64, kind="evidence_partition")
    page_3 = ArtifactRef(id="page:3", digest="3" * 64, kind="evidence_partition")
    snapshot = ArtifactRef(id="snapshot:pdf", digest="a" * 64, kind="evidence_snapshot")

    manifest = ExecutionOutputManifest(
        components=(
            ExecutionOutputComponent(artifact_ref=page_1, complete=True),
            ExecutionOutputComponent(artifact_ref=page_2, complete=True),
            ExecutionOutputComponent(artifact_ref=page_3, complete=False),
        ),
        aggregate_output_ref=snapshot,
        aggregate_complete=False,
    )

    assert manifest.reusable_component_refs == (page_1, page_2)
    assert manifest.reusable_aggregate_ref is None


def test_output_manifest_is_immutable():
    manifest = ExecutionOutputManifest()
    with pytest.raises(ValidationError):
        manifest.aggregate_complete = True  # type: ignore[misc]
