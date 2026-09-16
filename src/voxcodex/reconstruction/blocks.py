from __future__ import annotations

from collections.abc import Sequence

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import FrozenModel
from voxcodex.domain.evidence import EvidenceUnit, NormalizedGeometry
from voxcodex.domain.reconstruction import ReconstructionProfile


class VisualLineCandidate(FrozenModel):
    id: str
    evidence_refs: tuple[str, ...]
    bbox: NormalizedGeometry


class VisualRegionCandidate(FrozenModel):
    id: str
    line_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    bbox: NormalizedGeometry


def group_visual_lines(
    units: Sequence[EvidenceUnit],
    profile: ReconstructionProfile,
) -> tuple[VisualLineCandidate, ...]:
    positioned = [unit for unit in units if unit.normalized_geometry is not None]
    positioned.sort(
        key=lambda unit: (
            _center_y(unit.normalized_geometry),
            unit.normalized_geometry.x0,
            unit.id,
        )
    )

    buckets: list[list[EvidenceUnit]] = []
    for unit in positioned:
        geometry = unit.normalized_geometry
        assert geometry is not None
        if not buckets:
            buckets.append([unit])
            continue

        bucket = buckets[-1]
        bucket_geometry = _bbox_for_units(bucket)
        bucket_baseline = sum(
            _center_y(candidate.normalized_geometry)
            for candidate in bucket
            if candidate.normalized_geometry is not None
        ) / len(bucket)
        vertical_delta = abs(_center_y(geometry) - bucket_baseline)
        horizontal_gap = geometry.x0 - bucket_geometry.x1

        if (
            vertical_delta <= profile.baseline_tolerance
            and horizontal_gap <= profile.max_inline_gap
        ):
            bucket.append(unit)
        else:
            buckets.append([unit])

    lines: list[VisualLineCandidate] = []
    for bucket in buckets:
        ordered = sorted(
            bucket,
            key=lambda unit: (
                unit.normalized_geometry.x0 if unit.normalized_geometry else 0.0,
                unit.id,
            ),
        )
        refs = tuple(unit.id for unit in ordered)
        bbox = _bbox_for_units(ordered)
        lines.append(
            VisualLineCandidate(
                id=_candidate_id("line", refs),
                evidence_refs=refs,
                bbox=bbox,
            )
        )

    return tuple(sorted(lines, key=lambda line: (line.bbox.y0, line.bbox.x0, line.id)))


def group_visual_regions(
    units: Sequence[EvidenceUnit],
    profile: ReconstructionProfile,
) -> tuple[VisualRegionCandidate, ...]:
    lines = group_visual_lines(units, profile)
    region_buckets: list[list[VisualLineCandidate]] = []

    for line in lines:
        matched: list[VisualLineCandidate] | None = None
        for bucket in region_buckets:
            bbox = _bbox_for_lines(bucket)
            if _horizontally_related(line.bbox, bbox, profile.region_x_tolerance):
                matched = bucket
                break
        if matched is None:
            region_buckets.append([line])
        else:
            matched.append(line)

    regions: list[VisualRegionCandidate] = []
    for bucket in region_buckets:
        ordered_lines = sorted(bucket, key=lambda line: (line.bbox.y0, line.bbox.x0, line.id))
        line_refs = tuple(line.id for line in ordered_lines)
        evidence_refs = tuple(
            evidence_ref
            for line in ordered_lines
            for evidence_ref in line.evidence_refs
        )
        regions.append(
            VisualRegionCandidate(
                id=_candidate_id("region", evidence_refs),
                line_refs=line_refs,
                evidence_refs=evidence_refs,
                bbox=_bbox_for_lines(ordered_lines),
            )
        )

    return tuple(sorted(regions, key=lambda region: (region.bbox.x0, region.bbox.y0, region.id)))


def _candidate_id(kind: str, refs: tuple[str, ...]) -> str:
    digest = sha256_bytes(canonical_json_bytes({"kind": kind, "refs": refs}))
    return f"visual-{kind}:{digest}"


def _center_y(geometry: NormalizedGeometry | None) -> float:
    if geometry is None:
        return 0.0
    return (geometry.y0 + geometry.y1) / 2.0


def _bbox_for_units(units: Sequence[EvidenceUnit]) -> NormalizedGeometry:
    geometries = [unit.normalized_geometry for unit in units if unit.normalized_geometry is not None]
    if not geometries:
        raise ValueError("visual grouping requires normalized geometry")
    return _bbox(geometries)


def _bbox_for_lines(lines: Sequence[VisualLineCandidate]) -> NormalizedGeometry:
    if not lines:
        raise ValueError("region grouping requires at least one line")
    return _bbox([line.bbox for line in lines])


def _bbox(geometries: Sequence[NormalizedGeometry]) -> NormalizedGeometry:
    return NormalizedGeometry(
        x0=min(geometry.x0 for geometry in geometries),
        y0=min(geometry.y0 for geometry in geometries),
        x1=max(geometry.x1 for geometry in geometries),
        y1=max(geometry.y1 for geometry in geometries),
    )


def _horizontally_related(
    left: NormalizedGeometry,
    right: NormalizedGeometry,
    tolerance: float,
) -> bool:
    overlap = min(left.x1, right.x1) - max(left.x0, right.x0)
    if overlap >= 0.0:
        return True
    return abs(left.x0 - right.x0) <= tolerance
