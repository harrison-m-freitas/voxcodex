from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import (
    EvidencePartition,
    EvidenceSnapshot,
    EvidenceUnit,
    ExtractionProfile,
    NativeGeometry,
    NormalizedGeometry,
)


VALID_EVIDENCE_CLASSES = (
    "physical_page",
    "region",
    "line",
    "text_span",
    "glyph_run",
    "asset",
    "syntax_unit",
)


def make_unit(evidence_class: str) -> EvidenceUnit:
    return EvidenceUnit(
        id=f"evidence:{evidence_class}",
        snapshot_ref="snapshot:1",
        parent_ref=None,
        evidence_class=evidence_class,
        source_locator={"page_index": 0},
        surface="observed text",
        presentation={"font_size": 12.0},
        native_geometry=NativeGeometry(
            coordinate_space="pdf_points",
            bbox=(10.0, 20.0, 110.0, 60.0),
        ),
        normalized_geometry=NormalizedGeometry(
            x0=0.1,
            y0=0.2,
            x1=0.8,
            y1=0.6,
        ),
        native_payload={"extractor": "synthetic"},
        confidence_ref=None,
        provenance_ref="derivation:evidence:1",
    )


def test_evidence_unit_accepts_only_physical_or_syntactic_classes():
    for evidence_class in VALID_EVIDENCE_CLASSES:
        assert make_unit(evidence_class).evidence_class == evidence_class

    with pytest.raises(ValidationError):
        make_unit("paragraph")


def test_evidence_unit_has_no_canonical_role_field():
    payload = make_unit("text_span").model_dump()
    assert "role" not in payload

    with pytest.raises(ValidationError):
        EvidenceUnit(**(payload | {"role": "text.heading"}))


def test_snapshot_references_immutable_partition_artifacts():
    partition = EvidencePartition(
        id="partition:page:0",
        source_artifact_ref="source:1",
        partition_key="page:0",
        unit_refs=("evidence:text_span",),
        partition_digest="a" * 64,
        provenance_ref="derivation:partition:1",
    )
    partition_ref = ArtifactRef(
        id=partition.id,
        digest=partition.partition_digest,
        kind="evidence_partition",
    )
    profile = ExtractionProfile(
        id="extraction-profile:pdf:v1",
        adapter="pdf",
        adapter_version="1.0.0",
        options={"glyph_runs": False},
    )
    snapshot = EvidenceSnapshot(
        id="snapshot:1",
        source_artifact_ref="source:1",
        extraction_activity_ref="activity:extract:1",
        extraction_profile_ref=profile.id,
        partition_refs=(partition_ref,),
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
        snapshot_digest="b" * 64,
    )

    assert snapshot.partition_refs == (partition_ref,)
    with pytest.raises(ValidationError):
        snapshot.id = "snapshot:mutated"
