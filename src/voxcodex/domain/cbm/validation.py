from __future__ import annotations

from datetime import datetime
from typing import Literal

from voxcodex.domain.common import FrozenModel


ValidationStatus = Literal["PASS", "WARN", "FAIL"]
ValidationSeverity = Literal["info", "warning", "error", "critical"]


class ValidationCheck(FrozenModel):
    code: str
    severity: ValidationSeverity
    status: ValidationStatus
    object_refs: tuple[str, ...] = ()
    message: str


class ValidationReport(FrozenModel):
    id: str
    revision_ref: str
    validation_policy_ref: str
    validator_suite_version: str
    checks: tuple[ValidationCheck, ...] = ()
    result: ValidationStatus
    created_at: datetime


class ValidationPolicy(FrozenModel):
    id: str
    profile: str
    blocking_severities: tuple[ValidationSeverity, ...] = ()
    required_checks: tuple[str, ...] = ()
