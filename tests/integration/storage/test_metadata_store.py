from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


def activity(activity_id: str) -> ProcessingActivity:
    now = datetime(2026, 9, 14, tzinfo=UTC)
    return ProcessingActivity(
        id=activity_id,
        type="test_transform",
        processor=ProcessorIdentity(kind="python", name="test", version="0.1.0"),
        configuration_ref="config:test",
        started_at=now,
        completed_at=now,
        status="succeeded",
    )


def test_dependency_dag_returns_transitive_downstream(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    metadata.create_all(engine)
    store = MetadataStore(engine)

    a = ArtifactRef(id="artifact:A", digest="a" * 64, kind="test")
    b = ArtifactRef(id="artifact:B", digest="b" * 64, kind="test")
    c = ArtifactRef(id="artifact:C", digest="c" * 64, kind="test")
    for artifact in (a, b, c):
        store.register_artifact(artifact)

    ab_activity = activity("activity:AB")
    bc_activity = activity("activity:BC")
    store.register_activity(ab_activity)
    store.register_activity(bc_activity)
    store.register_derivation(
        Derivation(
            id="derivation:AB",
            activity_ref=ab_activity.id,
            input_refs=(a,),
            output_refs=(b,),
            derivation_kind="reconstructed",
        )
    )
    store.register_derivation(
        Derivation(
            id="derivation:BC",
            activity_ref=bc_activity.id,
            input_refs=(b,),
            output_refs=(c,),
            derivation_kind="reconstructed",
        )
    )

    assert store.get_downstream(a) == {b, c}


def test_failed_derivation_transaction_leaves_no_partial_rows(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    metadata.create_all(engine)
    store = MetadataStore(engine)

    a = ArtifactRef(id="artifact:A", digest="a" * 64, kind="test")
    missing = ArtifactRef(id="artifact:missing", digest="d" * 64, kind="test")
    store.register_artifact(a)
    transform = activity("activity:broken")
    store.register_activity(transform)
    derivation = Derivation(
        id="derivation:broken",
        activity_ref=transform.id,
        input_refs=(a,),
        output_refs=(missing,),
        derivation_kind="reconstructed",
    )

    with pytest.raises(IntegrityError):
        store.register_derivation(derivation)

    # If the failed transaction left the derivation row behind, retrying after
    # the missing artifact is registered would fail its primary-key constraint.
    store.register_artifact(missing)
    store.register_derivation(derivation)
    assert store.get_downstream(a) == {missing}
