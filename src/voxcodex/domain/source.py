from __future__ import annotations

from datetime import datetime
from typing import Any

from voxcodex.domain.common import FrozenModel


class SourceArtifact(FrozenModel):
    id: str
    media_type: str
    original_filename: str
    byte_size: int
    checksum: str
    acquisition_kind: str
    original_uri: str | None = None
    created_at: datetime


class SourceProfile(FrozenModel):
    id: str
    source_artifact_ref: str
    format_family: str
    declared_media_type: str | None = None
    detected_media_type: str
    language_hints: tuple[str, ...] = ()
    characteristics: dict[str, Any] = {}
    recommended_routes: tuple[str, ...] = ()
    provenance_ref: str
