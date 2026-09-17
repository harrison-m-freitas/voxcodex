from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

from voxcodex.domain.common import FrozenModel


class CanonicalStructureSignature(FrozenModel):
    nodes: tuple[tuple[str, str, str, int | None], ...]
    topologies: tuple[tuple[str, int | None, int | None, int], ...]


class CrossFormatComparison(FrozenModel):
    status: Literal["EQUIVALENT", "DIFFERENT", "DEFERRED_BY_SUPPORT_TIER"]
    left_signature: CanonicalStructureSignature | None = None
    right_signature: CanonicalStructureSignature | None = None
    diagnostic: str


def _surface(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def canonical_structure_signature(document: Mapping[str, Any]) -> CanonicalStructureSignature:
    raw_nodes = document.get("nodes", ())
    if isinstance(raw_nodes, (str, bytes)) or not isinstance(raw_nodes, Sequence):
        raw_nodes = ()

    id_to_index: dict[str, int] = {}
    for index, raw in enumerate(raw_nodes):
        if isinstance(raw, Mapping) and raw.get("id") is not None:
            id_to_index[str(raw["id"])] = index

    nodes: list[tuple[str, str, str, int | None]] = []
    for raw in raw_nodes:
        if not isinstance(raw, Mapping):
            continue
        parent_ref = raw.get("parent_ref")
        if parent_ref is None:
            parent_index = None
        else:
            parent_index = id_to_index.get(str(parent_ref), -1)
        nodes.append(
            (
                str(raw.get("node_class", "")),
                str(raw.get("role", "")),
                _surface(raw.get("surface")),
                parent_index,
            )
        )

    raw_topologies = document.get("topologies", ())
    if isinstance(raw_topologies, (str, bytes)) or not isinstance(raw_topologies, Sequence):
        raw_topologies = ()
    topologies: list[tuple[str, int | None, int | None, int]] = []
    for raw in raw_topologies:
        if not isinstance(raw, Mapping):
            continue
        cells = raw.get("cells", ())
        cell_count = len(cells) if isinstance(cells, Sequence) and not isinstance(cells, (str, bytes)) else 0
        topologies.append(
            (
                str(raw.get("kind", "")),
                int(raw["rows"]) if raw.get("rows") is not None else None,
                int(raw["columns"]) if raw.get("columns") is not None else None,
                cell_count,
            )
        )

    return CanonicalStructureSignature(nodes=tuple(nodes), topologies=tuple(topologies))


def compare_canonical_structures(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    left_supported: bool,
    right_supported: bool,
) -> CrossFormatComparison:
    if not left_supported or not right_supported:
        return CrossFormatComparison(
            status="DEFERRED_BY_SUPPORT_TIER",
            diagnostic="cross-format comparison deferred because at least one manifestation is outside the supported tier",
        )

    left_signature = canonical_structure_signature(left)
    right_signature = canonical_structure_signature(right)
    equivalent = left_signature == right_signature
    return CrossFormatComparison(
        status="EQUIVALENT" if equivalent else "DIFFERENT",
        left_signature=left_signature,
        right_signature=right_signature,
        diagnostic=(
            "canonical structure signatures are equivalent"
            if equivalent
            else "canonical structure signatures differ"
        ),
    )
