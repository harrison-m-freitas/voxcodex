from __future__ import annotations

from voxcodex.domain.cbm.validation import ValidationCheck
from voxcodex.validation.policies import EvidenceAccountability


def check_significant_suspected_loss(items: tuple[EvidenceAccountability, ...]) -> ValidationCheck:
    refs = tuple(
        sorted(
            item.evidence_ref
            for item in items
            if item.significance == "significant" and item.classification == "suspected_loss"
        )
    )
    if refs:
        return ValidationCheck(
            code="coverage.significant_suspected_loss",
            severity="critical",
            status="FAIL",
            object_refs=refs,
            message="significant evidence is classified as suspected_loss",
        )
    return ValidationCheck(
        code="coverage.significant_suspected_loss",
        severity="info",
        status="PASS",
        message="no significant evidence is classified as suspected_loss",
    )


def check_unresolved_non_significant(items: tuple[EvidenceAccountability, ...]) -> ValidationCheck:
    refs = tuple(
        sorted(
            item.evidence_ref
            for item in items
            if item.significance == "non_significant" and item.classification == "unresolved"
        )
    )
    if refs:
        return ValidationCheck(
            code="coverage.unresolved_non_significant",
            severity="warning",
            status="WARN",
            object_refs=refs,
            message="non-significant evidence remains unresolved",
        )
    return ValidationCheck(
        code="coverage.unresolved_non_significant",
        severity="info",
        status="PASS",
        message="no non-significant evidence remains unresolved",
    )
