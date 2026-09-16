from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from voxcodex.domain.common import ArtifactRef, FrozenModel


class ProcessorIdentity(FrozenModel):
    kind: str
    name: str
    version: str


class ModelIdentity(FrozenModel):
    provider: str
    name: str
    version: str | None = None


class ProcessingActivity(FrozenModel):
    id: str
    type: str
    processor: ProcessorIdentity
    model: ModelIdentity | None = None
    prompt_ref: str | None = None
    configuration_ref: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    usage_ref: str | None = None


class Derivation(FrozenModel):
    id: str
    activity_ref: str
    input_refs: tuple[ArtifactRef, ...]
    output_refs: tuple[ArtifactRef, ...]
    derivation_kind: str
    confidence_ref: str | None = None


class UsageRecord(FrozenModel):
    id: str
    activity_ref: str
    compute: dict[str, Any] = {}
    model_usage: dict[str, Any] = {}
    external_api_usage: dict[str, Any] = {}
    storage_delta_bytes: int = 0
    estimated_cost: Decimal | None = None
    actual_cost: Decimal | None = None
    pricing_ref: str | None = None
