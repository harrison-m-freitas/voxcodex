from __future__ import annotations

from typing import Literal

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.validation import ValidationPolicy
from voxcodex.domain.common import FrozenModel


AccountabilityClass = Literal[
    "canonicalized",
    "intentionally_noncanonical",
    "unresolved",
    "suspected_loss",
]
EvidenceSignificance = Literal["significant", "non_significant", "unknown"]


class EvidenceAccountability(FrozenModel):
    evidence_ref: str
    significance: EvidenceSignificance
    classification: AccountabilityClass
    canonical_ref: str | None = None


class EvidenceSignificancePolicy(FrozenModel):
    id: str
    version: str
    significant_classes: tuple[str, ...]

    @property
    def artifact_digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))


def m2_evidence_significance() -> EvidenceSignificancePolicy:
    return EvidenceSignificancePolicy(
        id="evidence-significance-policy:m2-poc-strict:v1",
        version="1",
        significant_classes=("text", "literal", "marker", "symbol", "asset", "structured"),
    )


def m2_poc_strict() -> ValidationPolicy:
    return ValidationPolicy(
        id="validation-policy:m2-poc-strict:v1",
        profile="m2_poc_strict",
        blocking_severities=("error", "critical"),
        required_checks=(
            "structure.dangling_ref",
            "structure.tree_cycle",
            "schema.role_node_class",
            "structure.table_topology",
            "traceability.source_accountability",
            "traceability.provenance",
            "fidelity.inherited_weakening",
            "coverage.significant_suspected_loss",
            "coverage.unresolved_non_significant",
        ),
    )
