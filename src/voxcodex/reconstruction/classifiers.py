from __future__ import annotations

import re

from pydantic import Field

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.reconstruction import ReconstructionProfile


class BlockFeatures(FrozenModel):
    text: str
    relative_font_size: float = Field(default=1.0, gt=0.0)
    is_bold: bool = False
    is_monospace: bool = False
    is_uppercase: bool = False
    normalized_y: float | None = Field(default=None, ge=0.0, le=1.0)
    spacing_before: float = Field(default=0.0, ge=0.0, le=1.0)
    spacing_after: float = Field(default=0.0, ge=0.0, le=1.0)
    recurrence_count: int = Field(default=1, ge=1)
    line_count: int = Field(default=1, ge=1)
    following_verse_like_lines: int = Field(default=0, ge=0)
    is_small_font: bool = False


class RoleHypothesis(FrozenModel):
    role: str
    score: float = Field(ge=0.0, le=1.0)
    evidence_basis: tuple[str, ...]


class ClassificationResult(FrozenModel):
    hypotheses: tuple[RoleHypothesis, ...]
    resolved_role: str | None = None


def classify_block(
    features: BlockFeatures,
    profile: ReconstructionProfile,
) -> ClassificationResult:
    hypotheses: list[RoleHypothesis] = []
    text = features.text.strip()

    heading_basis: list[str] = []
    heading_score = 0.0
    if features.relative_font_size >= profile.heading_min_relative_font_size:
        heading_score += 0.35
        heading_basis.append("relative_font_size")
    if features.is_bold:
        heading_score += 0.20
        heading_basis.append("weight")
    if features.spacing_before >= 0.03 or features.spacing_after >= 0.02:
        heading_score += 0.20
        heading_basis.append("spacing")
    if features.line_count == 1 and 0 < len(text) <= 80:
        heading_score += 0.15
        heading_basis.append("short_line")
    if heading_basis:
        hypotheses.append(
            RoleHypothesis(
                role="text.heading",
                score=min(heading_score, 1.0),
                evidence_basis=tuple(heading_basis),
            )
        )

    if (
        features.recurrence_count >= profile.running_header_min_recurrence
        and features.normalized_y is not None
        and features.normalized_y <= 0.12
    ):
        hypotheses.append(
            RoleHypothesis(
                role="editorial.running_header",
                score=0.95,
                evidence_basis=("recurrence", "page_position"),
            )
        )

    if (
        text.isdigit()
        and len(text) <= 6
        and features.normalized_y is not None
        and (features.normalized_y <= 0.10 or features.normalized_y >= 0.90)
    ):
        hypotheses.append(
            RoleHypothesis(
                role="editorial.folio",
                score=0.85,
                evidence_basis=("numeric_shape", "page_position"),
            )
        )

    speaker_basis: list[str] = []
    speaker_score = 0.0
    uppercase_shape = features.is_uppercase or (bool(text) and text == text.upper() and any(ch.isalpha() for ch in text))
    if uppercase_shape:
        speaker_score += 0.30
        speaker_basis.append("uppercase_shape")
    if features.line_count == 1 and 0 < len(text) <= profile.speaker_cue_max_chars:
        speaker_score += 0.25
        speaker_basis.append("short_line")
    if features.following_verse_like_lines >= 2:
        speaker_score += 0.35
        speaker_basis.append("neighboring_verse_shape")
    if speaker_basis:
        hypotheses.append(
            RoleHypothesis(
                role="drama.speaker_cue",
                score=min(speaker_score, 1.0),
                evidence_basis=tuple(speaker_basis),
            )
        )

    if features.is_monospace:
        score = 0.65 + (0.25 if features.line_count >= 2 else 0.0)
        basis = ("monospace", "multiline") if features.line_count >= 2 else ("monospace",)
        hypotheses.append(
            RoleHypothesis(
                role="technical.monospace_block",
                score=min(score, 1.0),
                evidence_basis=basis,
            )
        )

    if (
        features.is_small_font
        and features.normalized_y is not None
        and features.normalized_y >= 0.65
        and re.match(r"^\s*(?:\d+|[*†‡])(?:[.)]|\s)", text)
    ):
        hypotheses.append(
            RoleHypothesis(
                role="editorial.footnote",
                score=0.90,
                evidence_basis=("small_font", "lower_page_position", "note_marker_shape"),
            )
        )

    if re.match(r"^\s*(?:figure|fig\.?|figura|table|tabela)\s+\d+", text, flags=re.IGNORECASE):
        hypotheses.append(
            RoleHypothesis(
                role="editorial.caption",
                score=0.82,
                evidence_basis=("caption_label_shape", "short_text"),
            )
        )

    if len(text) >= 80 and not features.is_monospace:
        hypotheses.append(
            RoleHypothesis(
                role="text.prose_block",
                score=0.82,
                evidence_basis=("long_text", "non_monospace"),
            )
        )

    hypotheses.sort(key=lambda hypothesis: (-hypothesis.score, hypothesis.role))
    resolved_role = (
        hypotheses[0].role
        if hypotheses and hypotheses[0].score >= profile.classification_resolve_threshold
        else None
    )
    return ClassificationResult(
        hypotheses=tuple(hypotheses),
        resolved_role=resolved_role,
    )
