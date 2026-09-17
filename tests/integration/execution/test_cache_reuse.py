from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine, func, select

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import derivations, metadata, processing_activities


def test_cache_hit_returns_original_outputs_without_fabricating_activity_or_derivation():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)

    source = ArtifactRef(id="artifact:source", digest="a" * 64, kind="source")
    output = ArtifactRef(id="artifact:output", digest="b" * 64, kind="evidence")
    store.register_artifact(source)
    store.register_artifact(output)

    now = datetime(2026, 9, 17, tzinfo=UTC)
    activity = ProcessingActivity(
        id="activity:original",
        type="pdf_text_extraction",
        processor=ProcessorIdentity(kind="python", name="pdf.extract", version="1.0.0"),
        started_at=now,
        completed_at=now,
        status="succeeded",
    )
    fingerprint = "f" * 64
    store.register_activity(activity, activity_fingerprint=fingerprint)
    store.register_derivation(
        Derivation(
            id="derivation:original",
            activity_ref=activity.id,
            input_refs=(source,),
            output_refs=(output,),
            derivation_kind="extracted",
        )
    )

    reusable = store.find_reusable_output(fingerprint)

    assert reusable == (output,)
    assert store.get_producing_activity(output) == activity

    with engine.connect() as connection:
        activity_count = connection.scalar(select(func.count()).select_from(processing_activities))
        derivation_count = connection.scalar(select(func.count()).select_from(derivations))

    assert activity_count == 1
    assert derivation_count == 1
