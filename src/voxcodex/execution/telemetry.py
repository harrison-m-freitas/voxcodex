from __future__ import annotations

from pydantic import Field

from voxcodex.domain.common import FrozenModel


class ExecutionTelemetry(FrozenModel):
    activity_ref: str | None = None
    duration_seconds: float = Field(ge=0.0)
    queue_wait_seconds: float | None = Field(default=None, ge=0.0)
    retry_count: int = Field(default=0, ge=0)
    cpu_seconds: float | None = Field(default=None, ge=0.0)
    peak_memory_bytes: int | None = Field(default=None, ge=0)
    observed_resource_metrics: dict[str, float | int] = Field(default_factory=dict)
    error_diagnostics: tuple[str, ...] = ()
