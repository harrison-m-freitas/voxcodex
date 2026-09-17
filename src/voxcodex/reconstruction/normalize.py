from __future__ import annotations

import unicodedata

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.evidence import EvidenceUnit


class NormalizedEvidenceView(FrozenModel):
    evidence_ref: str
    source_surface: str | None = None
    comparison_surface: str | None = None


def build_comparison_view(unit: EvidenceUnit) -> NormalizedEvidenceView:
    source_surface = unit.surface
    comparison_surface = (
        unicodedata.normalize("NFKC", source_surface)
        if source_surface is not None
        else None
    )
    return NormalizedEvidenceView(
        evidence_ref=unit.id,
        source_surface=source_surface,
        comparison_surface=comparison_surface,
    )
