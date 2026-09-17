from __future__ import annotations

from voxcodex.domain.cbm.content import DocumentNode
from voxcodex.domain.cbm.structured import TablePayload
from voxcodex.domain.cbm.validation import ValidationCheck


def check_dangling_refs(nodes: tuple[DocumentNode, ...]) -> ValidationCheck:
    ids = {node.id for node in nodes}
    dangling = tuple(sorted(node.id for node in nodes if node.parent_ref is not None and node.parent_ref not in ids))
    if dangling:
        return ValidationCheck(
            code="structure.dangling_ref",
            severity="error",
            status="FAIL",
            object_refs=dangling,
            message="one or more parent_ref values do not resolve inside the node registry",
        )
    return ValidationCheck(
        code="structure.dangling_ref",
        severity="info",
        status="PASS",
        message="all parent_ref values resolve",
    )


def check_tree_cycles(nodes: tuple[DocumentNode, ...]) -> ValidationCheck:
    parents = {node.id: node.parent_ref for node in nodes}
    cyclic: set[str] = set()
    for node_id in parents:
        seen: set[str] = set()
        current: str | None = node_id
        while current is not None and current in parents:
            if current in seen:
                cyclic.update(seen)
                break
            seen.add(current)
            current = parents[current]
    if cyclic:
        return ValidationCheck(
            code="structure.tree_cycle",
            severity="error",
            status="FAIL",
            object_refs=tuple(sorted(cyclic)),
            message="node parent_ref graph contains a cycle",
        )
    return ValidationCheck(
        code="structure.tree_cycle",
        severity="info",
        status="PASS",
        message="node parent_ref graph is acyclic",
    )


def check_table_topology(tables: tuple[TablePayload, ...]) -> ValidationCheck:
    invalid: list[str] = []
    for table in tables:
        occupied: set[tuple[int, int]] = set()
        bad = False
        for cell in table.cells:
            if cell.row >= table.row_count or cell.column >= table.column_count:
                bad = True
                break
            coordinates = {
                (row, column)
                for row in range(cell.row, cell.row + cell.row_span)
                for column in range(cell.column, cell.column + cell.column_span)
            }
            if any(row >= table.row_count or column >= table.column_count for row, column in coordinates):
                bad = True
                break
            if occupied & coordinates:
                bad = True
                break
            occupied.update(coordinates)
        if bad:
            invalid.append(table.id)
    if invalid:
        return ValidationCheck(
            code="structure.table_topology",
            severity="error",
            status="FAIL",
            object_refs=tuple(sorted(invalid)),
            message="table topology contains overlap or out-of-bounds cells",
        )
    return ValidationCheck(
        code="structure.table_topology",
        severity="info",
        status="PASS",
        message="table topology is valid",
    )
