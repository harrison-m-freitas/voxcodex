from __future__ import annotations

from voxcodex.domain.cbm.content import FidelityConstraint


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
