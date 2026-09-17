from __future__ import annotations

from voxcodex.domain.reconstruction import ReconstructionProfile
from voxcodex.reconstruction.classifiers import BlockFeatures, classify_block


def _profile() -> ReconstructionProfile:
    return ReconstructionProfile(
        id="reconstruction-profile:classifiers",
        version="0.1.0",
        classification_resolve_threshold=0.80,
        heading_min_relative_font_size=1.20,
        running_header_min_recurrence=3,
        speaker_cue_max_chars=32,
    )


def test_bold_alone_does_not_resolve_heading():
    result = classify_block(
        BlockFeatures(
            text="Uma linha qualquer",
            relative_font_size=1.0,
            is_bold=True,
            line_count=1,
        ),
        _profile(),
    )

    assert result.resolved_role != "text.heading"
    heading = next((item for item in result.hypotheses if item.role == "text.heading"), None)
    assert heading is None or heading.score < _profile().classification_resolve_threshold


def test_large_bold_spaced_short_line_can_resolve_heading():
    result = classify_block(
        BlockFeatures(
            text="Arquiteturas Distribuídas",
            relative_font_size=1.45,
            is_bold=True,
            spacing_before=0.05,
            spacing_after=0.03,
            line_count=1,
        ),
        _profile(),
    )

    assert result.resolved_role == "text.heading"
    hypothesis = next(item for item in result.hypotheses if item.role == "text.heading")
    assert {"relative_font_size", "weight", "spacing", "short_line"} <= set(hypothesis.evidence_basis)


def test_repeated_same_position_text_becomes_running_header_candidate():
    result = classify_block(
        BlockFeatures(
            text="SEÇÃO EXPERIMENTAL 17",
            relative_font_size=0.90,
            normalized_y=0.03,
            recurrence_count=4,
            line_count=1,
        ),
        _profile(),
    )

    assert result.resolved_role == "editorial.running_header"
    hypothesis = next(item for item in result.hypotheses if item.role == "editorial.running_header")
    assert {"recurrence", "page_position"} <= set(hypothesis.evidence_basis)


def test_uppercase_short_line_plus_verse_shape_can_hypothesize_speaker_cue_without_genre():
    result = classify_block(
        BlockFeatures(
            text="ZORBLAX",
            relative_font_size=1.0,
            is_uppercase=True,
            line_count=1,
            following_verse_like_lines=5,
        ),
        _profile(),
    )

    assert result.resolved_role == "drama.speaker_cue"
    hypothesis = next(item for item in result.hypotheses if item.role == "drama.speaker_cue")
    assert {"uppercase_shape", "short_line", "neighboring_verse_shape"} <= set(hypothesis.evidence_basis)


def test_unseen_uppercase_name_uses_features_not_corpus_literals():
    first = classify_block(
        BlockFeatures(
            text="QXMVORA",
            is_uppercase=True,
            line_count=1,
            following_verse_like_lines=3,
        ),
        _profile(),
    )
    second = classify_block(
        BlockFeatures(
            text="NARVEX",
            is_uppercase=True,
            line_count=1,
            following_verse_like_lines=3,
        ),
        _profile(),
    )

    assert first.resolved_role == second.resolved_role == "drama.speaker_cue"
    assert first.hypotheses[0].evidence_basis == second.hypotheses[0].evidence_basis
