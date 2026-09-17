from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from voxcodex.domain.common import FrozenModel


class ReproducibilityClass(StrEnum):
    DETERMINISTIC = "deterministic"
    SEEDED = "seeded"
    NON_DETERMINISTIC = "non_deterministic"
    EXTERNALLY_VARIABLE = "externally_variable"


class FailureClass(StrEnum):
    TRANSIENT = "transient"
    PERMANENT_INPUT = "permanent_input"
    PROCESSOR_BUG = "processor_bug"
    POLICY_BLOCK = "policy_block"
    RESOURCE_LIMIT = "resource_limit"
    EXTERNAL_DEPENDENCY = "external_dependency"


class ExecutionFailure(FrozenModel):
    failure_class: FailureClass
    code: str
    message: str
    retry_after_seconds: float | None = Field(default=None, ge=0.0)


class RetryDecision(FrozenModel):
    should_retry: bool
    next_attempt: int | None = Field(default=None, ge=1)
    delay_seconds: float = Field(default=0.0, ge=0.0)
    reason: str


class RetryPolicy(FrozenModel):
    max_attempts: int = Field(default=3, ge=1)
    retryable_classes: tuple[FailureClass, ...] = (
        FailureClass.TRANSIENT,
        FailureClass.RESOURCE_LIMIT,
        FailureClass.EXTERNAL_DEPENDENCY,
    )

    def decide(self, failure: ExecutionFailure, attempt: int) -> RetryDecision:
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        if failure.failure_class not in self.retryable_classes:
            return RetryDecision(
                should_retry=False,
                reason=f"{failure.failure_class.value} failures are not blind-retryable",
            )
        if attempt >= self.max_attempts:
            return RetryDecision(
                should_retry=False,
                reason="retry budget exhausted",
            )
        return RetryDecision(
            should_retry=True,
            next_attempt=attempt + 1,
            delay_seconds=failure.retry_after_seconds or 0.0,
            reason="failure class is retryable under policy",
        )
