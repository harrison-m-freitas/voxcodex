from __future__ import annotations

from pathlib import Path
from typing import Protocol

from voxcodex.domain.source import SourceArtifact, SourceProfile


class SourceAdapter(Protocol):
    def inspect(self, source: SourceArtifact, bytes_path: Path) -> SourceProfile: ...
