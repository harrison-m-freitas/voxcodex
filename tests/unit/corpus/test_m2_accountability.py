from __future__ import annotations

from voxcodex.corpus.m2_pipeline import _evidence_accountability
from voxcodex.domain.evidence import EvidenceUnit


def _syntax(
    evidence_id: str,
    *,
    start: int,
    end: int,
    token_type: str,
    surface: str,
) -> EvidenceUnit:
    return EvidenceUnit(
        id=evidence_id,
        snapshot_ref="snapshot:test",
        evidence_class="syntax_unit",
        source_locator={"char_start": start, "char_end": end},
        surface=surface,
        native_payload={"token_type": token_type},
        provenance_ref="derivation:test",
    )


def test_whitespace_only_text_span_is_non_significant_when_unmaterialized() -> None:
    whitespace = EvidenceUnit(
        id="evidence:whitespace",
        snapshot_ref="snapshot:test",
        evidence_class="text_span",
        source_locator={"page_index": 0, "span_index": 0},
        surface="  ",
        provenance_ref="derivation:test",
    )

    result = _evidence_accountability((whitespace,), {})

    assert len(result) == 1
    assert result[0].significance == "non_significant"
    assert result[0].classification == "intentionally_noncanonical"
    assert result[0].canonical_ref is None


def test_nested_markdown_syntax_inside_canonical_block_is_redundant_not_loss() -> None:
    paragraph = _syntax(
        "evidence:paragraph",
        start=0,
        end=20,
        token_type="paragraph_open",
        surface="alpha *beta* gamma\n",
    )
    emphasis = _syntax(
        "evidence:emphasis",
        start=6,
        end=12,
        token_type="emphasis",
        surface="*beta*",
    )

    result = _evidence_accountability(
        (paragraph, emphasis),
        {paragraph.id: "node:paragraph"},
    )
    by_ref = {item.evidence_ref: item for item in result}

    assert by_ref[paragraph.id].significance == "significant"
    assert by_ref[paragraph.id].classification == "canonicalized"
    assert by_ref[emphasis.id].significance == "non_significant"
    assert by_ref[emphasis.id].classification == "intentionally_noncanonical"
    assert by_ref[emphasis.id].canonical_ref is None


def test_markdown_syntax_outside_canonical_ranges_still_blocks_as_suspected_loss() -> None:
    paragraph = _syntax(
        "evidence:paragraph",
        start=0,
        end=10,
        token_type="paragraph_open",
        surface="alpha\n",
    )
    orphan = _syntax(
        "evidence:orphan",
        start=20,
        end=25,
        token_type="unknown_block",
        surface="omega",
    )

    result = _evidence_accountability(
        (paragraph, orphan),
        {paragraph.id: "node:paragraph"},
    )
    by_ref = {item.evidence_ref: item for item in result}

    assert by_ref[orphan.id].significance == "significant"
    assert by_ref[orphan.id].classification == "suspected_loss"
