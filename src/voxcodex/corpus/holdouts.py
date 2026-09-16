from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet


class QuarantinedCaseError(PermissionError):
    """Raised when unrevealed holdout source content is requested."""


@dataclass(frozen=True, slots=True)
class HoldoutGuard:
    quarantined_case_ids: frozenset[str]
    revealed: bool = False

    def __init__(self, quarantined_case_ids: AbstractSet[str], revealed: bool = False) -> None:
        object.__setattr__(self, "quarantined_case_ids", frozenset(quarantined_case_ids))
        object.__setattr__(self, "revealed", revealed)

    def assert_allowed(self, case_id: str, operation: str) -> None:
        if not self.revealed and case_id in self.quarantined_case_ids:
            raise QuarantinedCaseError(
                f"{case_id} is an unrevealed M2 blind holdout; operation {operation!r} is blocked"
            )
