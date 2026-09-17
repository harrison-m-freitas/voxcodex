from __future__ import annotations

from typing import Literal

from pydantic import Field

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.cbm.provenance import FidelityConstraint


CellRole = Literal["header", "body", "stub"]


class RoleProfile(FrozenModel):
    role: str
    allowed_node_classes: tuple[str, ...] = ()
    allowed_parent_roles: tuple[str, ...] = ()
    allowed_child_roles: tuple[str, ...] = ()
    structured_payload_kind: str | None = None
    default_fidelity_constraints: tuple[FidelityConstraint, ...] = ()
    semantic_requirements: tuple[str, ...] = ()


class TableCell(FrozenModel):
    id: str
    row: int = Field(ge=0)
    column: int = Field(ge=0)
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)
    cell_role: CellRole
    content_refs: tuple[str, ...] = ()
    source_anchor_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()


class TablePayload(FrozenModel):
    id: str
    row_count: int = Field(ge=1)
    column_count: int = Field(ge=1)
    cells: tuple[TableCell, ...] = ()


class FormulaPayload(FrozenModel):
    id: str
    source_representation_refs: tuple[str, ...] = ()
    reconstructed_representation_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()


class StructuredPayloadRegistry(FrozenModel):
    id: str
    payload_refs: tuple[str, ...] = ()
