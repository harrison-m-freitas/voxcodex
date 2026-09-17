from __future__ import annotations

import pytest
from pydantic import ValidationError

from voxcodex.execution.telemetry import ExecutionTelemetry


def test_telemetry_records_operational_metrics_without_causal_edges():
    telemetry = ExecutionTelemetry(
        activity_ref="activity:1",
        duration_seconds=1.25,
        queue_wait_seconds=0.2,
        retry_count=1,
        cpu_seconds=0.8,
        peak_memory_bytes=1024,
        observed_resource_metrics={"read_bytes": 512},
        error_diagnostics=("first attempt timed out",),
    )

    assert telemetry.retry_count == 1
    assert "input_refs" not in telemetry.model_fields
    assert "output_refs" not in telemetry.model_fields
    assert "derivation_kind" not in telemetry.model_fields


def test_telemetry_is_frozen_and_rejects_negative_metrics():
    telemetry = ExecutionTelemetry(duration_seconds=0.0)
    with pytest.raises(ValidationError):
        telemetry.retry_count = 2  # type: ignore[misc]

    with pytest.raises(ValidationError):
        ExecutionTelemetry(duration_seconds=-0.1)
