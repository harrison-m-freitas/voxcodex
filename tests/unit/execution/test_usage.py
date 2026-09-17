from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine, func, select

from voxcodex.domain.processing import ProcessingActivity, ProcessorIdentity
from voxcodex.execution.planner import PipelineStage, PlannedActivity
from voxcodex.execution.usage import ActualUsageMetrics, PricingPolicy, UsageEstimator
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata, usage_records


def _planned_pdf_activity() -> PlannedActivity:
    stage = PipelineStage(
        name="evidence",
        activity_type="pdf_text_extraction",
        processor=ProcessorIdentity(kind="python", name="pdf.extract", version="1.0.0"),
        semantic_config_digest="a" * 64,
        profile_versions=("pdf-evidence:0.1",),
        schema_versions=("evidence:0.1",),
        estimated_usage={
            "input_bytes": 1000,
            "page_units": 3,
            "file_units": 1,
            "external_model_units": 0,
            "external_api_units": 0,
        },
    )
    return PlannedActivity(
        stage=stage,
        semantic_config_digest=stage.semantic_config_digest,
        input_refs=(),
        activity_fingerprint="f" * 64,
        requires_processing=True,
    )


def test_local_pdf_estimate_tracks_physical_units_without_inventing_currency_cost():
    estimate = UsageEstimator().estimate(_planned_pdf_activity())

    assert estimate.input_bytes == 1000
    assert estimate.page_units == 3
    assert estimate.file_units == 1
    assert estimate.external_model_units == 0
    assert estimate.external_api_units == 0
    assert estimate.estimated_cost is None
    assert estimate.pricing_ref is None


def test_fixed_pricing_produces_deterministic_estimate_only_for_priced_dimensions():
    pricing = PricingPolicy(
        id="pricing:local-test:v1",
        currency="USD",
        unit_prices={
            "input_bytes": Decimal("0.000001"),
            "page_units": Decimal("0.01"),
            "file_units": Decimal("0"),
        },
    )
    estimate = UsageEstimator(pricing=pricing).estimate(_planned_pdf_activity())

    assert estimate.estimated_cost == Decimal("0.031000")
    assert estimate.pricing_ref == pricing.id


def test_actual_usage_records_pages_duration_and_bytes_and_can_be_persisted():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)
    estimator = UsageEstimator()
    now = datetime(2026, 9, 17, tzinfo=UTC)
    store.register_activity(
        ProcessingActivity(
            id="activity:pdf:1",
            type="pdf_text_extraction",
            processor=ProcessorIdentity(kind="python", name="pdf.extract", version="1.0.0"),
            started_at=now,
            completed_at=now,
            status="succeeded",
        )
    )

    record = estimator.record_actual(
        "activity:pdf:1",
        ActualUsageMetrics(
            input_bytes=1000,
            page_units=3,
            file_units=1,
            cpu_duration_seconds=0.25,
            output_bytes=750,
            external_model_units=0,
            external_api_units=0,
        ),
        metadata_store=store,
    )

    assert record.compute["page_units"] == 3
    assert record.compute["cpu_duration_seconds"] == 0.25
    assert record.compute["input_bytes"] == 1000
    assert record.compute["output_bytes"] == 750
    assert record.model_usage["external_model_units"] == 0
    assert record.external_api_usage["external_api_units"] == 0
    assert record.actual_cost is None
    assert record.pricing_ref is None

    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(usage_records)) == 1


def test_unpriced_nonzero_dimension_prevents_partial_currency_estimate():
    pricing = PricingPolicy(
        id="pricing:incomplete:v1",
        currency="USD",
        unit_prices={"page_units": Decimal("0.01")},
    )

    estimate = UsageEstimator(pricing=pricing).estimate(_planned_pdf_activity())

    assert estimate.estimated_cost is None
    assert estimate.pricing_ref is None
