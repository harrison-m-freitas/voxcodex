from __future__ import annotations

from datetime import UTC, datetime

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.content import DocumentNode
from voxcodex.domain.cbm.document import CanonicalRevision
from voxcodex.domain.cbm.structured import TablePayload
from voxcodex.domain.cbm.validation import ValidationPolicy, ValidationReport
from voxcodex.domain.common import FrozenModel
from voxcodex.validation.coverage_checks import (
    check_significant_suspected_loss,
    check_unresolved_non_significant,
)
from voxcodex.validation.fidelity_checks import check_inherited_weakening
from voxcodex.validation.policies import EvidenceAccountability
from voxcodex.validation.schema_checks import check_role_node_classes
from voxcodex.validation.structural_checks import (
    check_dangling_refs,
    check_table_topology,
    check_tree_cycles,
)
from voxcodex.validation.traceability_checks import (
    check_provenance,
    check_source_accountability,
)


class RevisionValidationBundle(FrozenModel):
    revision: CanonicalRevision
    nodes: tuple[DocumentNode, ...] = ()
    tables: tuple[TablePayload, ...] = ()
    source_anchor_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    evidence_accountability: tuple[EvidenceAccountability, ...] = ()
    fidelity_weakening_attempts: tuple[str, ...] = ()


def validate_revision(
    bundle: RevisionValidationBundle,
    policy: ValidationPolicy,
) -> ValidationReport:
    checks = (
        check_dangling_refs(bundle.nodes),
        check_tree_cycles(bundle.nodes),
        check_role_node_classes(bundle.nodes),
        check_table_topology(bundle.tables),
        check_source_accountability(bundle.nodes, bundle.source_anchor_refs),
        check_provenance(bundle.nodes, bundle.provenance_refs),
        check_inherited_weakening(bundle.fidelity_weakening_attempts),
        check_significant_suspected_loss(bundle.evidence_accountability),
        check_unresolved_non_significant(bundle.evidence_accountability),
    )
    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        result = "FAIL"
    elif "WARN" in statuses:
        result = "WARN"
    else:
        result = "PASS"

    seed = {
        "revision_ref": bundle.revision.id,
        "policy_ref": policy.id,
        "checks": [check.model_dump(mode="json") for check in checks],
        "result": result,
    }
    report_id = f"validation-report:{sha256_bytes(canonical_json_bytes(seed))}"
    return ValidationReport(
        id=report_id,
        revision_ref=bundle.revision.id,
        validation_policy_ref=policy.id,
        validator_suite_version="m2.4-v0.1",
        checks=checks,
        result=result,
        created_at=datetime(1970, 1, 1, tzinfo=UTC),
    )
