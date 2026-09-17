from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from pydantic import Field, model_validator

from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.ids import new_event_id
from voxcodex.storage.metadata import MetadataStore


class ReviewCandidate(FrozenModel):
    id: str
    object_ref: str
    issue_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = ()


class ReviewRisk(FrozenModel):
    candidate_ref: str
    risk_score: float = Field(ge=0.0)
    impact_component: float = Field(ge=0.0)
    uncertainty_component: float = Field(ge=0.0)
    issue_type_multiplier: float = Field(ge=0.0)


class ReviewRiskPolicy(FrozenModel):
    impact_weight: float = Field(default=0.5, ge=0.0)
    uncertainty_weight: float = Field(default=0.5, ge=0.0)
    issue_type_multipliers: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> "ReviewRiskPolicy":
        if self.impact_weight == 0.0 and self.uncertainty_weight == 0.0:
            raise ValueError("at least one review-risk weight must be positive")
        if any(multiplier < 0.0 for multiplier in self.issue_type_multipliers.values()):
            raise ValueError("review-risk issue type multipliers cannot be negative")
        return self

    def score(self, candidate: ReviewCandidate) -> ReviewRisk:
        uncertainty = 1.0 - candidate.confidence
        impact_component = self.impact_weight * candidate.impact
        uncertainty_component = self.uncertainty_weight * uncertainty
        multiplier = self.issue_type_multipliers.get(candidate.issue_type, 1.0)
        return ReviewRisk(
            candidate_ref=candidate.id,
            risk_score=(impact_component + uncertainty_component) * multiplier,
            impact_component=impact_component,
            uncertainty_component=uncertainty_component,
            issue_type_multiplier=multiplier,
        )

    def rank(self, candidates: Iterable[ReviewCandidate]) -> tuple[ReviewRisk, ...]:
        scored = (self.score(candidate) for candidate in candidates)
        return tuple(sorted(scored, key=lambda item: (-item.risk_score, item.candidate_ref)))


class ReviewDecision(FrozenModel):
    id: str
    candidate_ref: str
    reviewer_ref: str
    decision: str
    rationale: str
    decided_at: datetime
    original_ref: ArtifactRef
    output_ref: ArtifactRef
    derivation_kind: str
    activity_ref: str


def apply_review_decision(
    candidate: ReviewCandidate,
    *,
    reviewer_ref: str,
    decision: str,
    original_ref: ArtifactRef,
    corrected_ref: ArtifactRef | None,
    metadata_store: MetadataStore,
    rationale: str,
    now: Callable[[], datetime] | None = None,
) -> ReviewDecision:
    """Apply a human review without rewriting prior immutable provenance.

    A correction creates a new output artifact produced by a manual-review
    activity. Acceptance records the human review activity and assertion but
    does not claim that the review produced the already-existing content.
    """

    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"accept", "correct"}:
        raise ValueError(f"unsupported review decision: {decision}")
    if candidate.object_ref != original_ref.id:
        raise ValueError("review candidate object_ref must match original_ref")

    stored_original = metadata_store.get_artifact(original_ref.id)
    if stored_original is None:
        raise ValueError(f"original artifact is not registered: {original_ref.id}")
    if stored_original != original_ref:
        raise ValueError(f"artifact identity collision for {original_ref.id}")

    evidence_inputs = _resolve_evidence(candidate, metadata_store)
    input_refs = _deduplicate_refs((original_ref, *evidence_inputs))
    timestamp = (now or (lambda: datetime.now(UTC)))()
    activity = ProcessingActivity(
        id=f"activity:manual-review:{new_event_id()}",
        type="manual_review",
        processor=ProcessorIdentity(kind="human", name=reviewer_ref, version="1"),
        configuration_ref=candidate.id,
        started_at=timestamp,
        completed_at=timestamp,
        status="succeeded",
    )

    if normalized_decision == "correct":
        if corrected_ref is None:
            raise ValueError("correct review decision requires corrected_ref")
        if corrected_ref.id == original_ref.id:
            raise ValueError("corrected artifact must have a new immutable identity")

        stored_corrected = metadata_store.get_artifact(corrected_ref.id)
        if stored_corrected is None:
            metadata_store.register_artifact(corrected_ref)
        elif stored_corrected != corrected_ref:
            raise ValueError(f"artifact identity collision for {corrected_ref.id}")

        derivation_kind = "corrected"
        output_ref = corrected_ref
        output_refs = (corrected_ref,)
    else:
        if corrected_ref is not None:
            raise ValueError("accept review decision cannot include corrected_ref")
        derivation_kind = "manually_asserted"
        output_ref = original_ref
        output_refs = ()

    metadata_store.register_activity(activity)
    metadata_store.register_derivation(
        Derivation(
            id=f"derivation:manual-review:{new_event_id()}",
            activity_ref=activity.id,
            input_refs=input_refs,
            output_refs=output_refs,
            derivation_kind=derivation_kind,
        )
    )

    return ReviewDecision(
        id=f"review-decision:{new_event_id()}",
        candidate_ref=candidate.id,
        reviewer_ref=reviewer_ref,
        decision=normalized_decision,
        rationale=rationale,
        decided_at=timestamp,
        original_ref=original_ref,
        output_ref=output_ref,
        derivation_kind=derivation_kind,
        activity_ref=activity.id,
    )


def _resolve_evidence(
    candidate: ReviewCandidate,
    metadata_store: MetadataStore,
) -> tuple[ArtifactRef, ...]:
    resolved: list[ArtifactRef] = []
    for evidence_ref in candidate.evidence_refs:
        artifact = metadata_store.get_artifact(evidence_ref)
        if artifact is None:
            raise ValueError(f"review evidence artifact is not registered: {evidence_ref}")
        resolved.append(artifact)
    return tuple(resolved)


def _deduplicate_refs(refs: Iterable[ArtifactRef]) -> tuple[ArtifactRef, ...]:
    unique: dict[str, ArtifactRef] = {}
    for ref in refs:
        previous = unique.get(ref.id)
        if previous is not None and previous != ref:
            raise ValueError(f"artifact identity collision for {ref.id}")
        unique.setdefault(ref.id, ref)
    return tuple(unique.values())
