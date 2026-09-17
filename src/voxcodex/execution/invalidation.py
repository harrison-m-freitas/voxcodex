from __future__ import annotations

from collections.abc import Sequence

from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.storage.metadata import MetadataStore


class AffectedGraph(FrozenModel):
    changed_refs: tuple[ArtifactRef, ...]
    affected_refs: tuple[ArtifactRef, ...]
    target_refs: tuple[ArtifactRef, ...]


def compute_affected(
    store: MetadataStore,
    *,
    changed_refs: Sequence[ArtifactRef],
    target_refs: Sequence[ArtifactRef] = (),
) -> AffectedGraph:
    """Compute contextual staleness without mutating historical artifacts.

    Only descendants of changed refs are candidates. When targets are supplied,
    candidates are further restricted to artifacts that are either targets or
    lie on an upstream path to a target. This prevents sibling branches from
    becoming stale merely because they share an earlier ancestor.
    """

    changed = _unique_sorted(changed_refs)
    targets = _unique_sorted(target_refs)

    downstream: dict[str, ArtifactRef] = {}
    for ref in changed:
        for artifact in store.get_downstream(ref):
            downstream[artifact.id] = artifact

    if targets:
        relevant_ids: set[str] = {ref.id for ref in targets}
        for target in targets:
            relevant_ids.update(ref.id for ref in store.get_upstream(target))
        affected = tuple(
            artifact
            for artifact in sorted(downstream.values(), key=lambda item: item.id)
            if artifact.id in relevant_ids
        )
    else:
        affected = tuple(sorted(downstream.values(), key=lambda item: item.id))

    return AffectedGraph(
        changed_refs=changed,
        affected_refs=affected,
        target_refs=targets,
    )


def _unique_sorted(refs: Sequence[ArtifactRef]) -> tuple[ArtifactRef, ...]:
    by_id = {ref.id: ref for ref in refs}
    return tuple(by_id[key] for key in sorted(by_id))
