from __future__ import annotations

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.content import FidelityConstraint
from voxcodex.domain.common import FrozenModel


class FidelityRule(FrozenModel):
    role: str
    constraints: tuple[FidelityConstraint, ...]


class FidelityPolicy(FrozenModel):
    version: str
    rules: tuple[FidelityRule, ...]

    @property
    def artifact_digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    def for_role(self, role: str) -> tuple[FidelityConstraint, ...]:
        for rule in self.rules:
            if rule.role == role:
                return rule.constraints
        return ()

    @classmethod
    def v01_defaults(cls) -> "FidelityPolicy":
        exact_character_order = (
            FidelityConstraint(dimension="character", requirement="preserve_exactly"),
            FidelityConstraint(dimension="ordering", requirement="preserve_exactly"),
        )
        exact_lexical_order = (
            FidelityConstraint(dimension="lexical", requirement="preserve_exactly"),
            FidelityConstraint(dimension="ordering", requirement="preserve_exactly"),
        )
        rules = (
            FidelityRule(role="technical.code_line", constraints=exact_character_order),
            FidelityRule(role="technical.terminal_input", constraints=exact_character_order),
            FidelityRule(role="editorial.omission_marker", constraints=exact_character_order),
            FidelityRule(role="poetry.verse_line", constraints=exact_lexical_order),
            FidelityRule(
                role="structured.table",
                constraints=(FidelityConstraint(dimension="structure", requirement="preserve_exactly"),),
            ),
            FidelityRule(
                role="structured.formula",
                constraints=(FidelityConstraint(dimension="symbolic", requirement="preserve_exactly"),),
            ),
        )
        return cls(version="0.1", rules=tuple(sorted(rules, key=lambda rule: rule.role)))


def effective_fidelity(
    inherited: tuple[FidelityConstraint, ...],
    local: tuple[FidelityConstraint, ...],
    *,
    weakening_dimensions: tuple[str, ...] = (),
) -> tuple[FidelityConstraint, ...]:
    inherited_by_dimension = {constraint.dimension: constraint for constraint in inherited}
    if set(weakening_dimensions) & set(inherited_by_dimension):
        dimensions = ", ".join(sorted(set(weakening_dimensions) & set(inherited_by_dimension)))
        raise ValueError(f"cannot weaken inherited fidelity: {dimensions}")

    effective = dict(inherited_by_dimension)
    for constraint in local:
        effective[constraint.dimension] = constraint
    return tuple(effective[dimension] for dimension in sorted(effective))
