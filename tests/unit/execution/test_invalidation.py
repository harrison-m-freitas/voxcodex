from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.execution.invalidation import compute_affected
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


def _artifact(name: str) -> ArtifactRef:
    return ArtifactRef(id=name, digest=(name[-1] * 64), kind="test")


def _activity(name: str) -> ProcessingActivity:
    now = datetime(2026, 9, 17, tzinfo=UTC)
    return ProcessingActivity(
        id=f"activity:{name}",
        type="test",
        processor=ProcessorIdentity(kind="python", name="test", version="1"),
        started_at=now,
        completed_at=now,
        status="succeeded",
    )


def _edge(store: MetadataStore, name: str, source: ArtifactRef, target: ArtifactRef) -> None:
    activity = _activity(name)
    store.register_activity(activity)
    store.register_derivation(
        Derivation(
            id=f"derivation:{name}",
            activity_ref=activity.id,
            input_refs=(source,),
            output_refs=(target,),
            derivation_kind="reconstructed",
        )
    )


def test_changing_b_affects_c_but_not_sibling_d_and_keeps_history_queryable():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)

    a, b, c, d = (_artifact(name) for name in ("artifact:a", "artifact:b", "artifact:c", "artifact:d"))
    for artifact in (a, b, c, d):
        store.register_artifact(artifact)

    _edge(store, "ab", a, b)
    _edge(store, "bc", b, c)
    _edge(store, "ad", a, d)

    affected = compute_affected(
        store,
        changed_refs=(b,),
        target_refs=(c, d),
    )

    assert c in affected.affected_refs
    assert d not in affected.affected_refs
    assert b in affected.changed_refs

    # Staleness is contextual metadata; historical artifacts are not mutated/deleted.
    assert store.get_artifact(b.id) == b
    assert store.get_artifact(c.id) == c
    assert store.get_artifact(d.id) == d
