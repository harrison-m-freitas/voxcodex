from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine

from voxcodex.domain.common import ArtifactRef
from voxcodex.execution.review import (
    ReviewCandidate,
    ReviewRiskPolicy,
    apply_review_decision,
)
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


def test_review_risk_is_not_inverse_confidence_and_prioritizes_high_impact_topology():
    policy = ReviewRiskPolicy(
        impact_weight=0.8,
        uncertainty_weight=0.2,
        issue_type_multipliers={
            "table_topology": 1.0,
            "decorative_marker": 0.5,
        },
    )
    high_confidence_high_impact = ReviewCandidate(
        id="review:table",
        object_ref="table:1",
        issue_type="table_topology",
        confidence=0.95,
        impact=1.0,
        evidence_refs=("evidence:table",),
    )
    low_confidence_low_impact = ReviewCandidate(
        id="review:marker",
        object_ref="marker:1",
        issue_type="decorative_marker",
        confidence=0.20,
        impact=0.10,
        evidence_refs=("evidence:marker",),
    )

    ranked = policy.rank((low_confidence_low_impact, high_confidence_high_impact))

    assert ranked[0].candidate_ref == high_confidence_high_impact.id
    assert ranked[0].risk_score > ranked[1].risk_score
    assert high_confidence_high_impact.confidence > low_confidence_low_impact.confidence


def test_review_correction_creates_new_immutable_output_and_lineage_without_erasing_prior():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)
    original = ArtifactRef(id="artifact:table:v1", digest="a" * 64, kind="reconstruction_table")
    corrected = ArtifactRef(id="artifact:table:v2", digest="b" * 64, kind="reconstruction_table")
    evidence = ArtifactRef(id="evidence:table", digest="e" * 64, kind="evidence_unit")
    for artifact in (original, evidence):
        store.register_artifact(artifact)

    candidate = ReviewCandidate(
        id="review:table",
        object_ref=original.id,
        issue_type="table_topology",
        confidence=0.90,
        impact=1.0,
        evidence_refs=(evidence.id,),
    )
    now = datetime(2026, 9, 17, tzinfo=UTC)

    decision = apply_review_decision(
        candidate,
        reviewer_ref="human:harrison",
        decision="correct",
        original_ref=original,
        corrected_ref=corrected,
        metadata_store=store,
        now=lambda: now,
        rationale="Cell span verified against source evidence.",
    )

    assert decision.original_ref == original
    assert decision.output_ref == corrected
    assert decision.derivation_kind == "corrected"
    assert decision.activity_ref.startswith("activity:manual-review:")
    assert store.get_artifact(original.id) == original
    assert store.get_artifact(corrected.id) == corrected
    assert store.get_producing_activity(corrected) is not None
    assert original in store.get_upstream(corrected)


def test_review_accept_without_correction_does_not_fabricate_new_content_artifact():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = MetadataStore(engine)
    original = ArtifactRef(id="artifact:paragraph:v1", digest="c" * 64, kind="reconstruction_block")
    evidence = ArtifactRef(id="evidence:paragraph", digest="d" * 64, kind="evidence_unit")
    store.register_artifact(original)
    store.register_artifact(evidence)
    candidate = ReviewCandidate(
        id="review:paragraph",
        object_ref=original.id,
        issue_type="boundary_ambiguity",
        confidence=0.65,
        impact=0.6,
        evidence_refs=(evidence.id,),
    )

    decision = apply_review_decision(
        candidate,
        reviewer_ref="human:reviewer",
        decision="accept",
        original_ref=original,
        corrected_ref=None,
        metadata_store=store,
        rationale="Existing reconstruction accepted after review.",
    )

    assert decision.output_ref == original
    assert decision.derivation_kind == "manually_asserted"
    assert store.get_artifact(original.id) == original
