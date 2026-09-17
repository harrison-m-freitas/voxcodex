from __future__ import annotations

from voxcodex.domain.cbm.content import DocumentNode
from voxcodex.domain.cbm.validation import ValidationCheck
from voxcodex.materialization.mappings import RoleProfileRegistry


def check_role_node_classes(nodes: tuple[DocumentNode, ...]) -> ValidationCheck:
    registry = RoleProfileRegistry.v01_defaults()
    invalid: list[str] = []
    for node in nodes:
        mapping = registry.resolve(node.role)
        if mapping is None or mapping.node_class != node.node_class:
            invalid.append(node.id)
    if invalid:
        return ValidationCheck(
            code="schema.role_node_class",
            severity="error",
            status="FAIL",
            object_refs=tuple(sorted(invalid)),
            message="one or more node roles are unregistered or incompatible with node_class",
        )
    return ValidationCheck(
        code="schema.role_node_class",
        severity="info",
        status="PASS",
        object_refs=(),
        message="all node role/node_class pairs are registered",
    )
