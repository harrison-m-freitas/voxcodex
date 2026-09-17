from __future__ import annotations

from datetime import UTC, datetime

import pytest

from voxcodex.domain.cbm.document import CanonicalRevision
from voxcodex.domain.cbm.validation import ValidationReport
from voxcodex.materialization.builder import freeze_revision, with_supplemental_validation


def _revision(*, activity: str, created_at: datetime) -> CanonicalRevision:
    return CanonicalRevision(
        id="revision:test",
        canonical_document_ref="document:test",
        revision_number=1,
        schema_version="0.1",
        root_node_ref="node:root",
        node_registry_ref="registry:nodes:abc",
        content_registry_ref="registry:content:def",
        entity_registry_ref="registry:entities:ghi",
        semantic_registry_ref="registry:semantic:jkl",
        structured_payload_registry_ref="registry:structured:mno",
        source_mapping_manifest_ref="manifest:source:pqr",
        fidelity_manifest_ref="manifest:fidelity:stu",
        provenance_manifest_ref="manifest:provenance:vwx",
        lifecycle_state="validated",
        created_by_activity_ref=activity,
        created_at=created_at,
    )


def _report(report_id: str, result: str) -> ValidationReport:
    return ValidationReport(
        id=report_id,
        revision_ref="revision:test",
        validation_policy_ref="validation-policy:m2-poc-strict:v1",
        validator_suite_version="m2.4-v0.1",
        checks=(),
        result=result,
        created_at=datetime(2026, 9, 17, tzinfo=UTC),
    )


def test_blocking_report_prevents_freeze():
    with pytest.raises(ValueError, match="validation report does not authorize freeze"):
        freeze_revision(
            _revision(activity="activity:one", created_at=datetime(2026, 9, 17, tzinfo=UTC)),
            _report("validation:fail", "FAIL"),
        )


def test_passing_report_and_manifests_freeze_revision():
    frozen = freeze_revision(
        _revision(activity="activity:one", created_at=datetime(2026, 9, 17, tzinfo=UTC)),
        _report("validation:pass", "PASS"),
    )

    assert frozen.revision.lifecycle_state == "frozen"
    assert frozen.revision.validation_report_ref == "validation:pass"
    assert frozen.revision.content_digest == frozen.semantic_digest
    assert len(frozen.semantic_digest) == 64


def test_authorizing_validation_report_cannot_be_replaced_by_supplemental_revalidation():
    frozen = freeze_revision(
        _revision(activity="activity:one", created_at=datetime(2026, 9, 17, tzinfo=UTC)),
        _report("validation:pass", "PASS"),
    )

    supplemented = with_supplemental_validation(
        frozen,
        _report("validation:supplemental", "WARN"),
    )

    assert supplemented.revision.validation_report_ref == "validation:pass"
    assert supplemented.authorizing_validation_report_ref == "validation:pass"
    assert supplemented.supplemental_validation_report_refs == ("validation:supplemental",)


def test_semantic_digest_is_idempotent_across_activity_ids_and_timestamps():
    first = freeze_revision(
        _revision(activity="activity:one", created_at=datetime(2026, 9, 17, 10, tzinfo=UTC)),
        _report("validation:pass-a", "PASS"),
    )
    second = freeze_revision(
        _revision(activity="activity:two", created_at=datetime(2026, 9, 18, 12, tzinfo=UTC)),
        _report("validation:pass-b", "PASS"),
    )

    assert first.semantic_digest == second.semantic_digest
