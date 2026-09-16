from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from voxcodex.domain.common import ArtifactRef, Confidence
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity, UsageRecord
from voxcodex.domain.source import SourceArtifact, SourceProfile


def round_trip(model):
    return type(model).model_validate_json(model.model_dump_json())


def test_common_and_source_contracts_round_trip_and_are_frozen():
    ref = ArtifactRef(id="artifact:abc", digest="a" * 64, kind="source_artifact")
    confidence = Confidence(
        value=1.0,
        scale="deterministic",
        basis="direct_structure",
        producer_ref="processor:source-inspector",
    )
    source = SourceArtifact(
        id="source:abc",
        media_type="application/pdf",
        original_filename="book.pdf",
        byte_size=123,
        checksum="a" * 64,
        acquisition_kind="uploaded",
        original_uri=None,
        created_at=datetime(2026, 9, 14, tzinfo=UTC),
    )
    profile = SourceProfile(
        id="profile:abc",
        source_artifact_ref=source.id,
        format_family="pdf",
        declared_media_type="application/pdf",
        detected_media_type="application/pdf",
        language_hints=("pt-BR",),
        characteristics={"page_count": 10},
        recommended_routes=("digital_pdf_text",),
        provenance_ref="derivation:profile",
    )

    assert round_trip(ref) == ref
    assert round_trip(confidence) == confidence
    assert round_trip(source) == source
    assert round_trip(profile) == profile
    with pytest.raises(ValidationError):
        source.id = "source:mutated"


def test_processing_contracts_round_trip():
    processor = ProcessorIdentity(kind="python", name="source-inspector", version="0.1.0")
    activity = ProcessingActivity(
        id="activity:1",
        type="source_inspection",
        processor=processor,
        configuration_ref="config:source-inspection-v1",
        started_at=datetime(2026, 9, 14, tzinfo=UTC),
        completed_at=datetime(2026, 9, 14, tzinfo=UTC),
        status="succeeded",
        usage_ref="usage:1",
    )
    derivation = Derivation(
        id="derivation:1",
        activity_ref=activity.id,
        input_refs=(ArtifactRef(id="source:1", digest="1" * 64, kind="source_artifact"),),
        output_refs=(ArtifactRef(id="profile:1", digest="2" * 64, kind="source_profile"),),
        derivation_kind="extracted",
        confidence_ref=None,
    )
    usage = UsageRecord(
        id="usage:1",
        activity_ref=activity.id,
        compute={"cpu_seconds": 0.25},
        model_usage={},
        external_api_usage={},
        storage_delta_bytes=0,
        estimated_cost=None,
        actual_cost=None,
        pricing_ref=None,
    )

    assert round_trip(processor) == processor
    assert round_trip(activity) == activity
    assert round_trip(derivation) == derivation
    assert round_trip(usage) == usage
