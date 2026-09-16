from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ArtifactRef(FrozenModel):
    id: str
    digest: str
    kind: str


class Confidence(FrozenModel):
    value: float
    scale: str
    basis: str
    producer_ref: str
    calibration_ref: str | None = None
