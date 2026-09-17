from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.processing import UsageRecord
from voxcodex.execution.planner import PlannedActivity
from voxcodex.ids import new_event_id
from voxcodex.storage.metadata import MetadataStore


class PricingPolicy(FrozenModel):
    id: str
    currency: str
    unit_prices: dict[str, Decimal] = Field(default_factory=dict)


class UsageEstimate(FrozenModel):
    input_bytes: int = Field(default=0, ge=0)
    page_units: int = Field(default=0, ge=0)
    file_units: int = Field(default=0, ge=0)
    cpu_duration_seconds: float | None = Field(default=None, ge=0.0)
    output_bytes: int | None = Field(default=None, ge=0)
    external_model_units: float = Field(default=0.0, ge=0.0)
    external_api_units: float = Field(default=0.0, ge=0.0)
    estimated_cost: Decimal | None = None
    pricing_ref: str | None = None


class ActualUsageMetrics(FrozenModel):
    input_bytes: int = Field(default=0, ge=0)
    page_units: int = Field(default=0, ge=0)
    file_units: int = Field(default=0, ge=0)
    cpu_duration_seconds: float = Field(default=0.0, ge=0.0)
    output_bytes: int = Field(default=0, ge=0)
    external_model_units: float = Field(default=0.0, ge=0.0)
    external_api_units: float = Field(default=0.0, ge=0.0)


class UsageEstimator:
    def __init__(self, *, pricing: PricingPolicy | None = None) -> None:
        self.pricing = pricing

    def estimate(self, planned_activity: PlannedActivity) -> UsageEstimate:
        usage = planned_activity.stage.estimated_usage
        dimensions = {
            "input_bytes": int(usage.get("input_bytes", 0)),
            "page_units": int(usage.get("page_units", 0)),
            "file_units": int(usage.get("file_units", 0)),
            "external_model_units": float(usage.get("external_model_units", 0)),
            "external_api_units": float(usage.get("external_api_units", 0)),
        }
        cost, pricing_ref = self._cost(dimensions)
        return UsageEstimate(
            **dimensions,
            cpu_duration_seconds=(
                float(usage["cpu_duration_seconds"])
                if "cpu_duration_seconds" in usage
                else None
            ),
            output_bytes=(int(usage["output_bytes"]) if "output_bytes" in usage else None),
            estimated_cost=cost,
            pricing_ref=pricing_ref,
        )

    def record_actual(
        self,
        activity_ref: str,
        metrics: ActualUsageMetrics,
        *,
        metadata_store: MetadataStore | None = None,
    ) -> UsageRecord:
        priced_dimensions = {
            "input_bytes": metrics.input_bytes,
            "page_units": metrics.page_units,
            "file_units": metrics.file_units,
            "cpu_duration_seconds": metrics.cpu_duration_seconds,
            "output_bytes": metrics.output_bytes,
            "external_model_units": metrics.external_model_units,
            "external_api_units": metrics.external_api_units,
        }
        cost, pricing_ref = self._cost(priced_dimensions)
        record = UsageRecord(
            id=f"usage:{new_event_id()}",
            activity_ref=activity_ref,
            compute={
                "input_bytes": metrics.input_bytes,
                "page_units": metrics.page_units,
                "file_units": metrics.file_units,
                "cpu_duration_seconds": metrics.cpu_duration_seconds,
                "output_bytes": metrics.output_bytes,
            },
            model_usage={"external_model_units": metrics.external_model_units},
            external_api_usage={"external_api_units": metrics.external_api_units},
            storage_delta_bytes=metrics.output_bytes,
            actual_cost=cost,
            pricing_ref=pricing_ref,
        )
        if metadata_store is not None:
            metadata_store.register_usage(record)
        return record

    def _cost(self, dimensions: dict[str, int | float]) -> tuple[Decimal | None, str | None]:
        if self.pricing is None:
            return None, None

        nonzero = {
            key: value
            for key, value in dimensions.items()
            if Decimal(str(value)) != 0
        }
        if any(key not in self.pricing.unit_prices for key in nonzero):
            return None, None

        total = Decimal("0")
        for key, value in dimensions.items():
            price = self.pricing.unit_prices.get(key)
            if price is None:
                continue
            total += Decimal(str(value)) * price
        return total, self.pricing.id
