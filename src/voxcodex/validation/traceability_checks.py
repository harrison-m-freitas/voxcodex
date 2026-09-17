from __future__ import annotations

from voxcodex.domain.cbm.content import DocumentNode
from voxcodex.domain.cbm.validation import ValidationCheck


def check_source_accountability(
    nodes: tuple[DocumentNode, ...],
    source_anchor_refs: tuple[str, ...],
) -> ValidationCheck:
    available = set(source_anchor_refs)
    missing = tuple(
        sorted(
            node.id
            for node in nodes
            if not node.source_anchor_refs or any(ref not in available for ref in node.source_anchor_refs)
        )
    )
    if missing:
        return ValidationCheck(
            code="traceability.source_accountability",
            severity="error",
            status="FAIL",
            object_refs=missing,
            message="one or more canonical nodes lack resolvable source anchors",
        )
    return ValidationCheck(
        code="traceability.source_accountability",
        severity="info",
        status="PASS",
        message="canonical nodes have resolvable source anchors",
    )


def check_provenance(nodes: tuple[DocumentNode, ...], provenance_refs: tuple[str, ...]) -> ValidationCheck:
    available = set(provenance_refs)
    missing = tuple(sorted(node.id for node in nodes if node.provenance_ref not in available))
    if missing:
        return ValidationCheck(
            code="traceability.provenance",
            severity="error",
            status="FAIL",
            object_refs=missing,
            message="one or more canonical nodes lack resolvable provenance",
        )
    return ValidationCheck(
        code="traceability.provenance",
        severity="info",
        status="PASS",
        message="canonical node provenance is resolvable",
    )
