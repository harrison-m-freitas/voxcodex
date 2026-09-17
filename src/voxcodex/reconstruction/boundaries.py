from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.reconstruction import (
    OpenStructuralState,
    ReconstructionIssue,
    StructuralContinuation,
)


BoundaryKind = Literal["page", "worker_chunk"]


class BoundaryFragment(FrozenModel):
    id: str
    structural_kind: str
    surface: str
    evidence_refs: tuple[ArtifactRef, ...]
    opens_continuation: bool = False
    closes_continuation: bool = False
    recurrence_key: str | None = None


class ReconciledBoundaryBlock(FrozenModel):
    id: str
    structural_kind: str
    surface: str
    evidence_refs: tuple[ArtifactRef, ...]
    fragment_refs: tuple[str, ...]
    occurrence_count: int = Field(default=1, ge=1)
    recurrence_key: str | None = None


class BoundaryReconciliation(FrozenModel):
    blocks: tuple[ReconciledBoundaryBlock, ...] = ()
    issues: tuple[ReconstructionIssue, ...] = ()
    open_state: OpenStructuralState = Field(default_factory=OpenStructuralState)


def reconcile_partition(
    fragments: Sequence[BoundaryFragment],
    open_state: OpenStructuralState,
    *,
    boundary_kind: BoundaryKind,
) -> BoundaryReconciliation:
    """Reconcile logical continuations without treating an operational boundary as semantic."""

    continuations = list(open_state.continuations)
    blocks: list[ReconciledBoundaryBlock] = []
    issues: list[ReconstructionIssue] = []

    for fragment in fragments:
        matching_indexes = [
            index
            for index, continuation in enumerate(continuations)
            if continuation.structural_kind == fragment.structural_kind
        ]

        if fragment.closes_continuation and not matching_indexes:
            blocks.append(_block_from_fragment(fragment))
            issues.append(_unresolved_closing_issue(fragment, boundary_kind))
            continue

        if matching_indexes:
            index = matching_indexes[0]
            continuation = continuations[index]
            merged = _extend_continuation(continuation, fragment)
            if fragment.closes_continuation:
                blocks.append(_block_from_continuation(merged))
                del continuations[index]
            else:
                continuations[index] = merged
            continue

        if fragment.opens_continuation:
            continuations.append(_continuation_from_fragment(fragment))
            continue

        blocks.append(_block_from_fragment(fragment))

    return BoundaryReconciliation(
        blocks=tuple(blocks),
        issues=tuple(issues),
        open_state=_state_from_continuations(continuations, boundary_kind),
    )


def collapse_recurrent_editorial(
    fragments: Sequence[BoundaryFragment],
) -> tuple[ReconciledBoundaryBlock, ...]:
    """Collapse recurrent editorial candidates while preserving every evidence reference."""

    grouped: OrderedDict[str, list[BoundaryFragment]] = OrderedDict()
    standalone: list[tuple[int, ReconciledBoundaryBlock]] = []

    for index, fragment in enumerate(fragments):
        if fragment.recurrence_key is None:
            standalone.append((index, _block_from_fragment(fragment)))
            continue
        grouped.setdefault(fragment.recurrence_key, []).append(fragment)

    collapsed: list[tuple[int, ReconciledBoundaryBlock]] = list(standalone)
    for recurrence_key, occurrences in grouped.items():
        first = occurrences[0]
        evidence_refs = _unique_artifact_refs(
            ref for occurrence in occurrences for ref in occurrence.evidence_refs
        )
        fragment_refs = tuple(occurrence.id for occurrence in occurrences)
        block_id = _stable_id(
            "recurrent-editorial",
            {
                "recurrence_key": recurrence_key,
                "structural_kind": first.structural_kind,
                "surface": first.surface,
                "evidence_refs": [ref.model_dump(mode="json") for ref in evidence_refs],
            },
        )
        collapsed.append(
            (
                fragments.index(first),
                ReconciledBoundaryBlock(
                    id=block_id,
                    structural_kind=first.structural_kind,
                    surface=first.surface,
                    evidence_refs=evidence_refs,
                    fragment_refs=fragment_refs,
                    occurrence_count=len(occurrences),
                    recurrence_key=recurrence_key,
                ),
            )
        )

    return tuple(block for _index, block in sorted(collapsed, key=lambda item: item[0]))


def _continuation_from_fragment(fragment: BoundaryFragment) -> StructuralContinuation:
    continuation_id = _stable_id(
        "continuation",
        {
            "structural_kind": fragment.structural_kind,
            "first_fragment_ref": fragment.id,
            "first_evidence_refs": [ref.model_dump(mode="json") for ref in fragment.evidence_refs],
        },
    )
    return StructuralContinuation(
        id=continuation_id,
        structural_kind=fragment.structural_kind,
        surface=fragment.surface,
        evidence_refs=fragment.evidence_refs,
        fragment_refs=(fragment.id,),
    )


def _extend_continuation(
    continuation: StructuralContinuation,
    fragment: BoundaryFragment,
) -> StructuralContinuation:
    return StructuralContinuation(
        id=continuation.id,
        structural_kind=continuation.structural_kind,
        surface=_join_surfaces(continuation.surface, fragment.surface),
        evidence_refs=_unique_artifact_refs((*continuation.evidence_refs, *fragment.evidence_refs)),
        fragment_refs=(*continuation.fragment_refs, fragment.id),
    )


def _block_from_continuation(continuation: StructuralContinuation) -> ReconciledBoundaryBlock:
    return ReconciledBoundaryBlock(
        id=_stable_id(
            "boundary-block",
            {
                "structural_kind": continuation.structural_kind,
                "surface": continuation.surface,
                "evidence_refs": [ref.model_dump(mode="json") for ref in continuation.evidence_refs],
                "fragment_refs": continuation.fragment_refs,
            },
        ),
        structural_kind=continuation.structural_kind,
        surface=continuation.surface,
        evidence_refs=continuation.evidence_refs,
        fragment_refs=continuation.fragment_refs,
    )


def _block_from_fragment(fragment: BoundaryFragment) -> ReconciledBoundaryBlock:
    return ReconciledBoundaryBlock(
        id=_stable_id(
            "boundary-block",
            {
                "structural_kind": fragment.structural_kind,
                "surface": fragment.surface,
                "evidence_refs": [ref.model_dump(mode="json") for ref in fragment.evidence_refs],
                "fragment_refs": [fragment.id],
            },
        ),
        structural_kind=fragment.structural_kind,
        surface=fragment.surface,
        evidence_refs=fragment.evidence_refs,
        fragment_refs=(fragment.id,),
        recurrence_key=fragment.recurrence_key,
    )


def _state_from_continuations(
    continuations: Sequence[StructuralContinuation],
    boundary_kind: BoundaryKind,
) -> OpenStructuralState:
    continuation_tuple = tuple(continuations)
    refs = tuple(continuation.id for continuation in continuation_tuple)
    return OpenStructuralState(
        open_units=refs,
        pending_continuations=refs,
        unresolved_boundaries=tuple(f"{boundary_kind}:{ref}" for ref in refs),
        continuations=continuation_tuple,
    )


def _unresolved_closing_issue(
    fragment: BoundaryFragment,
    boundary_kind: BoundaryKind,
) -> ReconstructionIssue:
    issue_id = _stable_id(
        "reconstruction-issue",
        {
            "type": "unresolved_boundary",
            "fragment_ref": fragment.id,
            "boundary_kind": boundary_kind,
        },
    )
    return ReconstructionIssue(
        id=issue_id,
        issue_type="unresolved_boundary",
        severity="warning",
        affected_refs=(fragment.id,),
        message=(
            "A fragment declared as a continuation closer arrived without matching open structural state; "
            "the evidence was preserved as a standalone block."
        ),
        suggested_action="review_boundary",
    )


def _join_surfaces(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if left[-1].isspace() or right[0].isspace():
        return left + right
    return f"{left} {right}"


def _unique_artifact_refs(refs) -> tuple[ArtifactRef, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.id, ref.digest, ref.kind)
        if key in seen:
            continue
        seen.add(key)
        result.append(ref)
    return tuple(result)


def _stable_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(payload))}"
