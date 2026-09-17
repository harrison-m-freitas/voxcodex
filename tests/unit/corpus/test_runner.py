from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from voxcodex.corpus.holdouts import HoldoutGuard, QuarantinedCaseError
from voxcodex.corpus.registry import CorpusRegistry
from voxcodex.corpus.runner import CorpusRunner, CorpusRunResult, ProcessorOutcome


def _write_case(root: Path, case_id: str, *, support_tier: str, acquired_format: str) -> None:
    case_root = root / "compatibility" / case_id
    source_root = case_root / "source"
    source_root.mkdir(parents=True, exist_ok=True)
    source_name = f"{case_id}.bin"
    (source_root / source_name).write_bytes(b"synthetic corpus source")
    (case_root / "metadata.json").write_text(
        json.dumps(
            {
                "corpus_case_id": case_id,
                "support_tier": support_tier,
                "acquired_manifestation_format": acquired_format,
                "source_artifacts": [{"relative_path": source_name}],
            }
        ),
        encoding="utf-8",
    )


def _registry(tmp_path: Path, cases: list[dict], holdouts: tuple[str, ...] = ()) -> CorpusRegistry:
    root = tmp_path / "corpus"
    root.mkdir()
    path = root / "COMPATIBILITY-CORPUS-V1.json"
    path.write_text(
        json.dumps(
            {
                "total_cases": len(cases),
                "total_acquired": len(cases),
                "cases": cases,
                "blind_holdouts": {"reserved_case_ids": list(holdouts)},
            }
        ),
        encoding="utf-8",
    )
    return CorpusRegistry.load(path)


def test_tier1_pdf_and_markdown_enter_processor_but_unsupported_formats_are_deferred(tmp_path: Path) -> None:
    cases = [
        {"corpus_case_id": "CC-PDF", "support_tier": "Tier 1", "acquired_manifestation_format": "PDF"},
        {"corpus_case_id": "CC-MD", "support_tier": "Tier 1", "acquired_manifestation_format": "Markdown source bundle (ZIP)"},
        {"corpus_case_id": "CC-HTML", "support_tier": "Experimental", "acquired_manifestation_format": "HTML saved-page bundle"},
        {"corpus_case_id": "CC-EPUB", "support_tier": "Experimental", "acquired_manifestation_format": "EPUB3"},
        {"corpus_case_id": "CC-DOCX", "support_tier": "Experimental", "acquired_manifestation_format": "DOCX"},
    ]
    registry = _registry(tmp_path, cases)
    _write_case(registry.path.parent, "CC-PDF", support_tier="Tier 1", acquired_format="PDF")
    _write_case(registry.path.parent, "CC-MD", support_tier="Tier 1", acquired_format="Markdown source bundle (ZIP)")
    processed: list[str] = []

    def processor(case, source_path: Path) -> ProcessorOutcome:
        processed.append(case.case_id)
        assert source_path.is_file()
        return ProcessorOutcome(result_class="PASS", diagnostic="processor accepted source", evidence_refs=(f"source:{case.case_id}",))

    runner = CorpusRunner(registry=registry, guard=HoldoutGuard(set()), processor=processor)

    pdf = runner.run_case("CC-PDF")
    markdown = runner.run_case("CC-MD")
    html = runner.run_case("CC-HTML")
    epub = runner.run_case("CC-EPUB")
    docx = runner.run_case("CC-DOCX")

    assert processed == ["CC-PDF", "CC-MD"]
    assert pdf.result_class == "PASS"
    assert markdown.result_class == "PASS"
    assert {html.result_class, epub.result_class, docx.result_class} == {"DEFERRED_BY_SUPPORT_TIER"}
    assert all(result.source_resolved is False for result in (html, epub, docx))


def test_quarantined_case_is_blocked_before_source_resolution(tmp_path: Path) -> None:
    cases = [{"corpus_case_id": "CC-H", "support_tier": "Tier 1", "acquired_manifestation_format": "PDF"}]
    registry = _registry(tmp_path, cases, holdouts=("CC-H",))
    called = False

    def processor(case, source_path: Path) -> ProcessorOutcome:
        nonlocal called
        called = True
        return ProcessorOutcome(result_class="PASS", diagnostic="should not run")

    runner = CorpusRunner(registry=registry, guard=HoldoutGuard({"CC-H"}), processor=processor)

    with pytest.raises(QuarantinedCaseError):
        runner.run_case("CC-H")

    assert called is False
    assert not (registry.path.parent / "compatibility" / "CC-H" / "metadata.json").exists()


def test_model_gap_emits_immutable_schema_evolution_observation(tmp_path: Path) -> None:
    cases = [{"corpus_case_id": "CC-GAP", "support_tier": "Tier 1", "acquired_manifestation_format": "PDF"}]
    registry = _registry(tmp_path, cases)
    _write_case(registry.path.parent, "CC-GAP", support_tier="Tier 1", acquired_format="PDF")

    def processor(case, source_path: Path) -> ProcessorOutcome:
        return ProcessorOutcome(
            result_class="MODEL_GAP",
            diagnostic="new source-significant structure",
            evidence_refs=("evidence:gap",),
            phenomenon="nested marginal apparatus",
            affected_model_area="CBM relations",
            candidate_resolutions=("role extension", "new relation profile"),
        )

    result = CorpusRunner(
        registry=registry,
        guard=HoldoutGuard(set()),
        processor=processor,
    ).run_case("CC-GAP")

    assert result.result_class == "MODEL_GAP"
    assert result.evolution_observation is not None
    assert result.evolution_observation.case_id == "CC-GAP"
    assert result.evolution_observation.evidence_refs == ("evidence:gap",)
    with pytest.raises(ValidationError):
        result.evolution_observation.case_id = "mutated"  # type: ignore[misc]


def test_result_class_is_closed_not_free_text() -> None:
    with pytest.raises(ValidationError):
        CorpusRunResult(
            case_id="CC-X",
            support_tier="Tier 1",
            manifestation_format="PDF",
            result_class="MAYBE",  # type: ignore[arg-type]
            source_resolved=False,
            diagnostic="invalid",
        )
