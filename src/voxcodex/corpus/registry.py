from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from voxcodex.corpus.holdouts import HoldoutGuard


@dataclass(frozen=True, slots=True)
class CorpusRegistry:
    path: Path
    total_cases: int
    total_acquired: int
    quarantined_case_ids: frozenset[str]
    case_ids: frozenset[str]

    @classmethod
    def load(cls, path: Path) -> "CorpusRegistry":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        holdouts = data.get("blind_holdouts", {})
        return cls(
            path=path,
            total_cases=int(data["total_cases"]),
            total_acquired=int(data["total_acquired"]),
            quarantined_case_ids=frozenset(holdouts.get("reserved_case_ids", ())),
            case_ids=frozenset(case["corpus_case_id"] for case in cases),
        )

    def resolve_primary_source_path(
        self,
        case_id: str,
        guard: HoldoutGuard,
        *,
        operation: str,
    ) -> Path:
        guard.assert_allowed(case_id, operation)
        if case_id not in self.case_ids:
            raise KeyError(f"unknown corpus case: {case_id}")

        case_root = self.path.parent / "compatibility" / case_id
        metadata_path = case_root / "metadata.json"
        metadata: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
        source_artifacts = metadata.get("source_artifacts", [])
        if not source_artifacts:
            raise FileNotFoundError(f"no source artifact registered for {case_id}")
        relative_path = source_artifacts[0]["relative_path"]
        return case_root / "source" / relative_path
