from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import AbstractSet

from voxcodex.corpus.candidate import (
    ImplementationCandidateManifest,
    candidate_digest,
)
from voxcodex.digests import sha256_bytes


REVEAL_ACKNOWLEDGEMENT = "REVEAL_M2_HOLDOUTS_V1"
REVEAL_VERSION = "M2_HOLDOUTS_V1"
REVEAL_RECORD_NAME = "M2-HOLDOUT-REVEAL-V1.json"


class QuarantinedCaseError(PermissionError):
    """Raised when unrevealed holdout source content is requested."""


class HoldoutRevealError(ValueError):
    """Raised when the one-way holdout reveal preconditions are not satisfied."""


class HoldoutAlreadyRevealedError(HoldoutRevealError):
    """Raised when the v1 reveal state already exists for this history."""


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


@dataclass(frozen=True, slots=True)
class RevealRecord:
    candidate_digest: str
    holdout_manifest_digest: str
    revealed_at: str
    actor: str
    context: str
    reveal_version: str = REVEAL_VERSION


def _load_frozen_candidate(path: Path) -> tuple[ImplementationCandidateManifest, str]:
    if not path.is_file():
        raise HoldoutRevealError(f"candidate manifest is not frozen or missing: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HoldoutRevealError(f"candidate manifest is unreadable: {path}") from exc
    if not isinstance(data, dict):
        raise HoldoutRevealError("candidate manifest must be a JSON object")

    frozen_digest = data.pop("candidate_digest", None)
    if not isinstance(frozen_digest, str) or not frozen_digest:
        raise HoldoutRevealError("candidate manifest is not frozen: candidate_digest is missing")

    try:
        manifest = ImplementationCandidateManifest.model_validate(data)
    except ValueError as exc:
        raise HoldoutRevealError("candidate manifest does not satisfy the frozen contract") from exc

    recomputed = candidate_digest(manifest)
    if recomputed != frozen_digest:
        raise HoldoutRevealError(
            "candidate digest mismatch: frozen candidate content has changed"
        )
    return manifest, frozen_digest


def _actor_context() -> tuple[str, str]:
    actor = (
        os.environ.get("GITHUB_ACTOR")
        or os.environ.get("USER")
        or os.environ.get("USERNAME")
        or "unknown"
    )
    github_run_id = os.environ.get("GITHUB_RUN_ID")
    if github_run_id:
        return actor, f"github-actions:{github_run_id}"
    return actor, os.environ.get("VOXCODEX_REVEAL_CONTEXT", "local")


def reveal_holdouts(
    candidate_manifest_ref: Path,
    holdout_manifest_ref: Path,
    explicit_ack: str,
) -> RevealRecord:
    candidate_path = Path(candidate_manifest_ref)
    holdout_path = Path(holdout_manifest_ref)
    reveal_path = candidate_path.parent / REVEAL_RECORD_NAME

    if reveal_path.exists():
        raise HoldoutAlreadyRevealedError(
            f"M2 holdouts v1 already revealed for this implementation history: {reveal_path}"
        )

    if explicit_ack != REVEAL_ACKNOWLEDGEMENT:
        raise HoldoutRevealError(
            f"exact acknowledgement required: {REVEAL_ACKNOWLEDGEMENT}"
        )

    candidate, frozen_candidate_digest = _load_frozen_candidate(candidate_path)

    if not holdout_path.is_file():
        raise HoldoutRevealError(f"holdout manifest is missing: {holdout_path}")
    holdout_bytes = holdout_path.read_bytes()
    holdout_digest = sha256_bytes(holdout_bytes)
    if holdout_digest != candidate.holdout_freeze_manifest_digest:
        raise HoldoutRevealError(
            "holdout manifest digest mismatch with frozen implementation candidate"
        )

    try:
        holdout_manifest = json.loads(holdout_bytes)
    except json.JSONDecodeError as exc:
        raise HoldoutRevealError("holdout manifest is not valid JSON") from exc
    if not isinstance(holdout_manifest, dict):
        raise HoldoutRevealError("holdout manifest must be a JSON object")
    if holdout_manifest.get("status") != "FROZEN_UNREVEALED":
        raise HoldoutRevealError(
            "holdout manifest must be FROZEN_UNREVEALED before first reveal"
        )

    actor, context = _actor_context()
    record = RevealRecord(
        candidate_digest=frozen_candidate_digest,
        holdout_manifest_digest=holdout_digest,
        revealed_at=datetime.now(UTC).isoformat(),
        actor=actor,
        context=context,
    )
    serialized = json.dumps(asdict(record), sort_keys=True, indent=2) + "\n"
    try:
        with reveal_path.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
    except FileExistsError as exc:
        raise HoldoutAlreadyRevealedError(
            f"M2 holdouts v1 already revealed for this implementation history: {reveal_path}"
        ) from exc
    return record
