from __future__ import annotations

from typing import Literal

from pydantic import Field

from voxcodex.domain.common import FrozenModel


NodeClass = Literal["root", "division", "block", "structured_block", "declaration", "asset"]
FragmentClass = Literal["text", "literal", "marker", "symbol"]
FidelityDimension = Literal["lexical", "character", "structure", "symbolic", "ordering"]
FidelityRequirement = Literal["preserve_exactly"]


class Surface(FrozenModel):
    text: str
    language: str = "und"


class FidelityConstraint(FrozenModel):
    dimension: FidelityDimension
    requirement: FidelityRequirement = "preserve_exactly"


class DocumentNode(FrozenModel):
    id: str
    parent_ref: str | None = None
    order_key: str
    node_class: NodeClass
    role: str = Field(pattern=r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$")
    content_refs: tuple[str, ...] = ()
    child_refs: tuple[str, ...] = ()
    structured_payload_ref: str | None = None
    source_anchor_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()
    provenance_ref: str


class ContentFragment(FrozenModel):
    id: str
    owner_node_ref: str
    order_key: str
    fragment_class: FragmentClass
    role: str = Field(pattern=r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$")
    surface: Surface
    source_anchor_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()
    provenance_ref: str


class NodeRegistry(FrozenModel):
    id: str
    node_refs: tuple[str, ...] = ()


class ContentRegistry(FrozenModel):
    id: str
    content_refs: tuple[str, ...] = ()
