from __future__ import annotations

from typing import Literal

from voxcodex.domain.common import FrozenModel


class SchemaEvolutionObservation(FrozenModel):
    case_id: str
    source_ref: str
    result_class: Literal["MODEL_GAP", "MODEL_FAILURE"]
    phenomenon: str
    affected_model_area: str
    evidence_refs: tuple[str, ...] = ()
    candidate_resolutions: tuple[str, ...] = ()
