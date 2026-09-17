from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Literal

from voxcodex.corpus.evolution import SchemaEvolutionObservation
from voxcodex.corpus.holdouts import HoldoutGuard
from voxcodex.corpus.registry import CorpusRegistry
from voxcodex.domain.common import FrozenModel


ResultClass = Literal[
    "PASS",
    "PASS_WITH_EXTENSION",
    "PROCESSING_FAILURE",
    "MODEL_GAP",
    "MODEL_FAILURE",
    "DEFERRED_BY_SUPPORT_TIER",
]


class CorpusCase(FrozenModel):
    case_id: str
    support_tier: str
    manifestation_format: str


class ProcessorOutcome(FrozenModel):
    result_class: ResultClass
    diagnostic: str
    evidence_refs: tuple[str, ...] = ()
    phenomenon: str | None = None
    affected_model_area: str | None = None
    candidate_resolutions: tuple[str, ...] = ()


class CorpusRunResult(FrozenModel):
    case_id: str
    support_tier: str
    manifestation_format: str
    result_class: ResultClass
    source_resolved: bool
    diagnostic: str
    evidence_refs: tuple[str, ...] = ()
    evolution_observation: SchemaEvolutionObservation | None = None


Processor = Callable[[CorpusCase, Path], ProcessorOutcome]


class CorpusRunner:
    def __init__(
        self,
        *,
        registry: CorpusRegistry,
        guard: HoldoutGuard,
        processor: Processor,
    ) -> None:
        self.registry = registry
        self.guard = guard
        self.processor = processor
        data = json.loads(registry.path.read_text(encoding="utf-8"))
        self._cases = {
            str(entry["corpus_case_id"]): CorpusCase(
                case_id=str(entry["corpus_case_id"]),
                support_tier=str(entry.get("support_tier", "Experimental")),
                manifestation_format=str(entry.get("acquired_manifestation_format", "unknown")),
            )
            for entry in data.get("cases", [])
        }

    def run_case(self, case_id: str) -> CorpusRunResult:
        # The quarantine guard runs before metadata/source resolution and before
        # capability dispatch so a blind holdout can never be inspected merely
        # to decide whether it is supported.
        self.guard.assert_allowed(case_id, "corpus_run")
        case = self._cases.get(case_id)
        if case is None:
            raise KeyError(f"unknown corpus case: {case_id}")

        if not self._is_supported(case):
            return CorpusRunResult(
                case_id=case.case_id,
                support_tier=case.support_tier,
                manifestation_format=case.manifestation_format,
                result_class="DEFERRED_BY_SUPPORT_TIER",
                source_resolved=False,
                diagnostic=(
                    f"{case.support_tier} / {case.manifestation_format} is outside the "
                    "current Tier 1 PDF/Markdown execution claim"
                ),
            )

        source_path = self.registry.resolve_primary_source_path(
            case.case_id,
            self.guard,
            operation="corpus_run_source_resolution",
        )
        outcome = self.processor(case, source_path)
        observation = self._evolution_observation(case, source_path, outcome)
        return CorpusRunResult(
            case_id=case.case_id,
            support_tier=case.support_tier,
            manifestation_format=case.manifestation_format,
            result_class=outcome.result_class,
            source_resolved=True,
            diagnostic=outcome.diagnostic,
            evidence_refs=outcome.evidence_refs,
            evolution_observation=observation,
        )

    @staticmethod
    def _is_supported(case: CorpusCase) -> bool:
        if case.support_tier.casefold() != "tier 1":
            return False
        manifestation = case.manifestation_format.casefold()
        return "pdf" in manifestation or "markdown" in manifestation

    @staticmethod
    def _evolution_observation(
        case: CorpusCase,
        source_path: Path,
        outcome: ProcessorOutcome,
    ) -> SchemaEvolutionObservation | None:
        if outcome.result_class not in {"MODEL_GAP", "MODEL_FAILURE"}:
            return None
        if not outcome.phenomenon or not outcome.affected_model_area:
            raise ValueError(
                f"{outcome.result_class} requires phenomenon and affected_model_area"
            )
        return SchemaEvolutionObservation(
            case_id=case.case_id,
            source_ref=str(source_path),
            result_class=outcome.result_class,
            phenomenon=outcome.phenomenon,
            affected_model_area=outcome.affected_model_area,
            evidence_refs=outcome.evidence_refs,
            candidate_resolutions=outcome.candidate_resolutions,
        )
