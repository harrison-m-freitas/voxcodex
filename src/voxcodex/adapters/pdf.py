from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import pymupdf

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import (
    EvidencePartition,
    EvidenceSnapshot,
    EvidenceUnit,
    ExtractionProfile,
    NativeGeometry,
    NormalizedGeometry,
)
from voxcodex.domain.source import SourceArtifact, SourceProfile
from voxcodex.storage.blobs import LocalBlobStore


class PdfAdapter:
    adapter_version = "0.1.0"

    def __init__(self, blob_store: LocalBlobStore | None = None) -> None:
        self.blob_store = blob_store

    def inspect(self, source: SourceArtifact, bytes_path: Path) -> SourceProfile:
        text_page_count = 0
        image_only_page_count = 0
        mixed_content_page_count = 0
        total_images = 0
        rotations: set[int] = set()
        fonts: set[str] = set()

        with pymupdf.open(bytes_path) as document:
            page_count = document.page_count
            for page in document:
                text = page.get_text("text").strip()
                images = page.get_images(full=True)
                has_text = bool(text)
                has_images = bool(images)

                if has_text:
                    text_page_count += 1
                if has_images:
                    total_images += len(images)
                if has_images and not has_text:
                    image_only_page_count += 1
                if has_images and has_text:
                    mixed_content_page_count += 1

                rotations.add(int(page.rotation))
                for font in page.get_fonts(full=True):
                    if len(font) > 3 and font[3]:
                        fonts.add(str(font[3]))

        if text_page_count == 0:
            coverage_kind = "none"
        elif text_page_count == page_count:
            coverage_kind = "full"
        else:
            coverage_kind = "mixed"

        characteristics = {
            "page_count": page_count,
            "text_layer_present": text_page_count > 0,
            "text_page_count": text_page_count,
            "image_only_page_count": image_only_page_count,
            "mixed_content_page_count": mixed_content_page_count,
            "image_count": total_images,
            "coverage_kind": coverage_kind,
            "rotations": tuple(sorted(rotations)),
            "font_count": len(fonts),
        }

        recommended_routes = ["pdf_text"] if text_page_count else []
        if image_only_page_count or mixed_content_page_count:
            recommended_routes.append("pdf_visual_evidence")

        return SourceProfile(
            id=f"profile:{source.id}:pdf:{self.adapter_version}",
            source_artifact_ref=source.id,
            format_family="pdf",
            declared_media_type=source.media_type,
            detected_media_type="application/pdf",
            characteristics=characteristics,
            recommended_routes=tuple(recommended_routes),
            provenance_ref=f"derivation:inspect:{source.id}:pdf:{self.adapter_version}",
        )

    def extract(
        self,
        source: SourceArtifact,
        path: Path,
        profile: ExtractionProfile,
        page_indexes: Sequence[int] | None = None,
    ) -> EvidenceSnapshot:
        store = self._require_blob_store()
        if profile.adapter != "pdf":
            raise ValueError(f"expected pdf extraction profile, got {profile.adapter!r}")

        with pymupdf.open(path) as document:
            selected = tuple(range(document.page_count)) if page_indexes is None else tuple(page_indexes)
            for page_index in selected:
                if page_index < 0 or page_index >= document.page_count:
                    raise IndexError(f"page index out of range: {page_index}")

            identity_payload = {
                "source_artifact_ref": source.id,
                "source_checksum": source.checksum,
                "extraction_profile": profile.model_dump(mode="json"),
                "page_indexes": selected,
            }
            identity_digest = sha256_bytes(canonical_json_bytes(identity_payload))
            snapshot_id = f"snapshot:pdf:{identity_digest}"
            provenance_ref = f"derivation:pdf-extract:{identity_digest}"
            partition_refs: list[ArtifactRef] = []

            for page_index in selected:
                partition_refs.append(
                    self._extract_page_partition(
                        document=document,
                        page_index=page_index,
                        source=source,
                        snapshot_id=snapshot_id,
                        profile=profile,
                        provenance_ref=provenance_ref,
                    )
                )

        digest_payload = {
            "source_artifact_ref": source.id,
            "source_checksum": source.checksum,
            "extraction_profile": profile.model_dump(mode="json"),
            "partition_refs": [ref.model_dump(mode="json") for ref in partition_refs],
        }
        snapshot_digest = sha256_bytes(canonical_json_bytes(digest_payload))
        return EvidenceSnapshot(
            id=snapshot_id,
            source_artifact_ref=source.id,
            extraction_activity_ref=f"activity:pdf-extract:{identity_digest}",
            extraction_profile_ref=profile.id,
            partition_refs=tuple(partition_refs),
            created_at=source.created_at,
            snapshot_digest=snapshot_digest,
        )

    def load_partition(
        self,
        ref: ArtifactRef,
    ) -> tuple[EvidencePartition, tuple[EvidenceUnit, ...]]:
        if ref.kind != "evidence_partition":
            raise ValueError(f"expected evidence_partition ref, got {ref.kind!r}")
        store = self._require_blob_store()
        payload = json.loads(store.read_digest(ref.digest).decode("utf-8"))
        units = tuple(EvidenceUnit.model_validate(item) for item in payload.pop("units"))
        partition = EvidencePartition(
            **payload,
            partition_digest=ref.digest,
        )
        if tuple(unit.id for unit in units) != partition.unit_refs:
            raise ValueError(f"partition unit refs do not match payload for {ref.id}")
        return partition, units

    def _extract_page_partition(
        self,
        *,
        document: pymupdf.Document,
        page_index: int,
        source: SourceArtifact,
        snapshot_id: str,
        profile: ExtractionProfile,
        provenance_ref: str,
    ) -> ArtifactRef:
        store = self._require_blob_store()
        page = document[page_index]
        page_rect = page.rect
        width = float(page_rect.width)
        height = float(page_rect.height)
        partition_seed = sha256_bytes(
            canonical_json_bytes(
                {
                    "snapshot_ref": snapshot_id,
                    "page_index": page_index,
                    "source_checksum": source.checksum,
                }
            )
        )
        partition_id = f"partition:pdf:{partition_seed}"
        units: list[EvidenceUnit] = []

        def unit_id(kind: str, index: str | int) -> str:
            seed = f"{partition_id}:{kind}:{index}"
            return f"evidence:{sha256_bytes(seed.encode('utf-8'))}"

        page_unit = EvidenceUnit(
            id=unit_id("physical_page", 0),
            snapshot_ref=snapshot_id,
            parent_ref=None,
            evidence_class="physical_page",
            source_locator={"page_index": page_index},
            native_geometry=NativeGeometry(
                coordinate_space="pdf_points",
                bbox=(0.0, 0.0, width, height),
            ),
            normalized_geometry=NormalizedGeometry(x0=0.0, y0=0.0, x1=1.0, y1=1.0),
            native_payload={"rotation": int(page.rotation), "width": width, "height": height},
            provenance_ref=provenance_ref,
        )
        units.append(page_unit)

        text_dict = page.get_text("dict")
        line_counter = 0
        span_counter = 0
        for block_index, block in enumerate(text_dict.get("blocks", [])):
            if block.get("type") != 0:
                continue
            for line_index, line in enumerate(block.get("lines", [])):
                line_bbox = self._bbox_tuple(line.get("bbox"))
                spans = line.get("spans", [])
                line_surface = "".join(str(span.get("text", "")) for span in spans)
                current_line_id = unit_id("line", line_counter)
                units.append(
                    EvidenceUnit(
                        id=current_line_id,
                        snapshot_ref=snapshot_id,
                        parent_ref=page_unit.id,
                        evidence_class="line",
                        source_locator={
                            "page_index": page_index,
                            "block_index": block_index,
                            "line_index": line_index,
                        },
                        surface=line_surface or None,
                        native_geometry=self._native_geometry(line_bbox),
                        normalized_geometry=self._normalized_geometry(line_bbox, width, height),
                        native_payload={"direction": line.get("dir"), "writing_mode": line.get("wmode")},
                        provenance_ref=provenance_ref,
                    )
                )
                line_counter += 1

                for span_index, span in enumerate(spans):
                    span_bbox = self._bbox_tuple(span.get("bbox"))
                    units.append(
                        EvidenceUnit(
                            id=unit_id("text_span", span_counter),
                            snapshot_ref=snapshot_id,
                            parent_ref=current_line_id,
                            evidence_class="text_span",
                            source_locator={
                                "page_index": page_index,
                                "block_index": block_index,
                                "line_index": line_index,
                                "span_index": span_index,
                            },
                            surface=str(span.get("text", "")) or None,
                            presentation={
                                "font": span.get("font"),
                                "size": span.get("size"),
                                "flags": span.get("flags"),
                                "color": span.get("color"),
                            },
                            native_geometry=self._native_geometry(span_bbox),
                            normalized_geometry=self._normalized_geometry(span_bbox, width, height),
                            native_payload={
                                "origin": span.get("origin"),
                                "ascender": span.get("ascender"),
                                "descender": span.get("descender"),
                            },
                            provenance_ref=provenance_ref,
                        )
                    )
                    span_counter += 1

        image_counter = 0
        seen_xrefs: set[int] = set()
        for image_info in page.get_images(full=True):
            xref = int(image_info[0])
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            extracted = document.extract_image(xref)
            image_bytes = extracted["image"]
            blob_ref = store.put_bytes(image_bytes)
            rects = page.get_image_rects(xref)
            if not rects:
                rects = [None]
            for occurrence, rect in enumerate(rects):
                bbox = self._bbox_tuple(rect)
                units.append(
                    EvidenceUnit(
                        id=unit_id("asset", image_counter),
                        snapshot_ref=snapshot_id,
                        parent_ref=page_unit.id,
                        evidence_class="asset",
                        source_locator={
                            "page_index": page_index,
                            "xref": xref,
                            "occurrence": occurrence,
                        },
                        native_geometry=self._native_geometry(bbox),
                        normalized_geometry=self._normalized_geometry(bbox, width, height),
                        native_payload={
                            "xref": xref,
                            "extension": extracted.get("ext"),
                            "width": extracted.get("width"),
                            "height": extracted.get("height"),
                            "blob_sha256": blob_ref.sha256,
                            "byte_size": blob_ref.byte_size,
                        },
                        provenance_ref=provenance_ref,
                    )
                )
                image_counter += 1

        if bool(profile.options.get("glyph_runs")):
            for trace_index, trace in enumerate(page.get_texttrace()):
                chars = trace.get("chars", ())
                surface = "".join(
                    chr(char[0])
                    for char in chars
                    if isinstance(char, (tuple, list))
                    and char
                    and isinstance(char[0], int)
                    and 0 <= char[0] <= 0x10FFFF
                )
                bbox = self._bbox_tuple(trace.get("bbox"))
                units.append(
                    EvidenceUnit(
                        id=unit_id("glyph_run", trace_index),
                        snapshot_ref=snapshot_id,
                        parent_ref=page_unit.id,
                        evidence_class="glyph_run",
                        source_locator={"page_index": page_index, "trace_index": trace_index},
                        surface=surface or None,
                        presentation={
                            "font": trace.get("font"),
                            "size": trace.get("size"),
                            "type": trace.get("type"),
                        },
                        native_geometry=self._native_geometry(bbox),
                        normalized_geometry=self._normalized_geometry(bbox, width, height),
                        native_payload={"direction": trace.get("dir")},
                        provenance_ref=provenance_ref,
                    )
                )

        partition_payload = {
            "id": partition_id,
            "source_artifact_ref": source.id,
            "partition_key": f"page:{page_index}",
            "unit_refs": [unit.id for unit in units],
            "provenance_ref": provenance_ref,
            "units": [unit.model_dump(mode="json", exclude_none=True) for unit in units],
        }
        stored = store.put_bytes(canonical_json_bytes(partition_payload))
        return ArtifactRef(
            id=partition_id,
            digest=stored.sha256,
            kind="evidence_partition",
        )

    def _require_blob_store(self) -> LocalBlobStore:
        if self.blob_store is None:
            raise RuntimeError("PDF evidence extraction requires a blob store")
        return self.blob_store

    @staticmethod
    def _bbox_tuple(value: Any) -> tuple[float, float, float, float] | None:
        if value is None:
            return None
        if hasattr(value, "x0"):
            return (float(value.x0), float(value.y0), float(value.x1), float(value.y1))
        if isinstance(value, (tuple, list)) and len(value) == 4:
            return tuple(float(item) for item in value)  # type: ignore[return-value]
        return None

    @staticmethod
    def _native_geometry(
        bbox: tuple[float, float, float, float] | None,
    ) -> NativeGeometry | None:
        if bbox is None:
            return None
        return NativeGeometry(coordinate_space="pdf_points", bbox=bbox)

    @staticmethod
    def _normalized_geometry(
        bbox: tuple[float, float, float, float] | None,
        width: float,
        height: float,
    ) -> NormalizedGeometry | None:
        if bbox is None or width <= 0.0 or height <= 0.0:
            return None
        x0, y0, x1, y1 = bbox

        def clamp(value: float) -> float:
            return max(0.0, min(1.0, value))

        return NormalizedGeometry(
            x0=clamp(x0 / width),
            y0=clamp(y0 / height),
            x1=clamp(x1 / width),
            y1=clamp(y1 / height),
        )
