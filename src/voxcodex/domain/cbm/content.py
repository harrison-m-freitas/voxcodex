from __future__ import annotations

from typing import Literal

from voxcodex.domain.common import FrozenModel
from voxcodex.domain.cbm.provenance import FidelityConstraint


FragmentClass = Literal["text", "literal", "marker", "symbol"]


class Surface(FrozenModel):
    text: str
    language: str


class ContentFragment(FrozenModel):
    id: str
    owner_node_ref: str
    order_key: str
    fragment_class: FragmentClass
    role: str
    surface: Surface
    source_anchor_refs: tuple[str, ...] = ()
    fidelity_constraints: tuple[FidelityConstraint, ...] = ()
    provenance_ref: str


class ContentRegistry(FrozenModel):
    id: str
    content_refs: tuple[str, ...] = ()
