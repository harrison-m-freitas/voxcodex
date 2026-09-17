from __future__ import annotations

from voxcodex.domain.cbm.validation import ValidationCheck


def check_inherited_weakening(attempts: tuple[str, ...]) -> ValidationCheck:
    if attempts:
        return ValidationCheck(
            code="fidelity.inherited_weakening",
            severity="error",
            status="FAIL",
            object_refs=tuple(sorted(attempts)),
            message="one or more child objects attempt to weaken inherited fidelity",
        )
    return ValidationCheck(
        code="fidelity.inherited_weakening",
        severity="info",
        status="PASS",
        message="no inherited fidelity weakening was detected",
    )
