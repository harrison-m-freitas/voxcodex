from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidencePartition, EvidenceSnapshot, EvidenceUnit, ExtractionProfile
from voxcodex.domain.source import SourceArtifact, SourceProfile
from voxcodex.storage.blobs import LocalBlobStore


class MarkdownAdapter:
    adapter_version = "0.1.0"

    def __init__(self, blob_store: LocalBlobStore | None = None) -> None:
        self.blob_store = blob_store

    def inspect(self, source: SourceArtifact, bytes_path: Path) -> SourceProfile:
        raw = bytes_path.read_bytes()
        text = raw.decode("utf-8-sig")
        tokens = MarkdownIt().parse(text)

        crlf_count = raw.count(b"\r\n")
        lf_count = raw.count(b"\n")
        bare_lf_count = lf_count - crlf_count
        if crlf_count and bare_lf_count:
            line_endings = "mixed"
        elif crlf_count:
            line_endings = "crlf"
        elif bare_lf_count:
            line_endings = "lf"
        else:
            line_endings = "none"

        token_types = {token.type for token in tokens}
        characteristics = {
            "encoding": "utf-8",
            "line_endings": line_endings,
            "heading_syntax_present": "heading_open" in token_types,
            "code_fence_present": "fence" in token_types,
            "link_syntax_present": "link_open" in token_types,
            "embedded_html_present": bool({"html_block", "html_inline"} & token_types),
            "table_syntax_present": "table_open" in token_types,
        }

        return SourceProfile(
            id=f"profile:{source.id}:markdown:{self.adapter_version}",
            source_artifact_ref=source.id,
            format_family="markdown",
            declared_media_type=source.media_type,
            detected_media_type="text/markdown",
            characteristics=characteristics,
            recommended_routes=("markdown_syntax",),
            provenance_ref=f"derivation:inspect:{source.id}:markdown:{self.adapter_version}",
        )

    def extract(
        self,
        source: SourceArtifact,
        path: Path,
        profile: ExtractionProfile,
    ) -> EvidenceSnapshot:
        store = self._require_blob_store()
        if profile.adapter != "markdown":
            raise ValueError(f"expected markdown extraction profile, got {profile.adapter!r}")

        raw = path.read_bytes()
        bom_size = 3 if raw.startswith(b"\xef\xbb\xbf") else 0
        text = raw.decode("utf-8-sig")
        tokens = MarkdownIt().parse(text)
        mapper = _SourceMapper(text=text, bom_size=bom_size)

        identity_payload = {
            "source_artifact_ref": source.id,
            "source_checksum": source.checksum,
            "extraction_profile": profile.model_dump(mode="json"),
        }
        identity_digest = sha256_bytes(canonical_json_bytes(identity_payload))
        snapshot_id = f"snapshot:markdown:{identity_digest}"
        provenance_ref = f"derivation:markdown-extract:{identity_digest}"
        partition_id = f"partition:markdown:{identity_digest}"
        units: list[EvidenceUnit] = []

        for token_index, token in enumerate(tokens):
            if token.map is None:
                continue
            start_line, end_line = token.map
            char_start, char_end, byte_start, byte_end = mapper.line_range(start_line, end_line)
            raw_slice = text[char_start:char_end]
            if not raw_slice:
                continue
            units.append(
                self._syntax_unit(
                    snapshot_id=snapshot_id,
                    provenance_ref=provenance_ref,
                    source=source,
                    unit_index=f"token:{token_index}",
                    token_type=token.type,
                    tag=token.tag,
                    markup=token.markup,
                    info=token.info,
                    raw_slice=raw_slice,
                    char_start=char_start,
                    char_end=char_end,
                    byte_start=byte_start,
                    byte_end=byte_end,
                    line_start=start_line,
                    line_end=end_line,
                )
            )

            if token.type == "inline" and token.children:
                units.extend(
                    self._inline_emphasis_units(
                        token=token,
                        token_index=token_index,
                        block_raw=raw_slice,
                        block_char_start=char_start,
                        mapper=mapper,
                        snapshot_id=snapshot_id,
                        provenance_ref=provenance_ref,
                        source=source,
                        line_start=start_line,
                        line_end=end_line,
                    )
                )

        partition_payload = {
            "id": partition_id,
            "source_artifact_ref": source.id,
            "partition_key": "file:0",
            "unit_refs": [unit.id for unit in units],
            "provenance_ref": provenance_ref,
            "units": [unit.model_dump(mode="json", exclude_none=True) for unit in units],
        }
        stored = store.put_bytes(canonical_json_bytes(partition_payload))
        partition_ref = ArtifactRef(
            id=partition_id,
            digest=stored.sha256,
            kind="evidence_partition",
        )
        snapshot_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "source_artifact_ref": source.id,
                    "source_checksum": source.checksum,
                    "extraction_profile": profile.model_dump(mode="json"),
                    "partition_ref": partition_ref.model_dump(mode="json"),
                }
            )
        )
        return EvidenceSnapshot(
            id=snapshot_id,
            source_artifact_ref=source.id,
            extraction_activity_ref=f"activity:markdown-extract:{identity_digest}",
            extraction_profile_ref=profile.id,
            partition_refs=(partition_ref,),
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
        partition = EvidencePartition(**payload, partition_digest=ref.digest)
        if tuple(unit.id for unit in units) != partition.unit_refs:
            raise ValueError(f"partition unit refs do not match payload for {ref.id}")
        return partition, units

    def _syntax_unit(
        self,
        *,
        snapshot_id: str,
        provenance_ref: str,
        source: SourceArtifact,
        unit_index: str,
        token_type: str,
        tag: str,
        markup: str,
        info: str,
        raw_slice: str,
        char_start: int,
        char_end: int,
        byte_start: int,
        byte_end: int,
        line_start: int,
        line_end: int,
    ) -> EvidenceUnit:
        unit_seed = canonical_json_bytes(
            {
                "snapshot_ref": snapshot_id,
                "unit_index": unit_index,
                "token_type": token_type,
                "char_start": char_start,
                "char_end": char_end,
            }
        )
        return EvidenceUnit(
            id=f"evidence:{sha256_bytes(unit_seed)}",
            snapshot_ref=snapshot_id,
            parent_ref=None,
            evidence_class="syntax_unit",
            source_locator={
                "char_start": char_start,
                "char_end": char_end,
                "byte_start": byte_start,
                "byte_end": byte_end,
                "line_start": line_start,
                "line_end": line_end,
            },
            surface=raw_slice,
            native_payload={
                "token_type": token_type,
                "tag": tag,
                "markup": markup,
                "info": info,
                "raw_slice": raw_slice,
                "raw_source_digest": source.checksum,
            },
            provenance_ref=provenance_ref,
        )

    def _inline_emphasis_units(
        self,
        *,
        token: Any,
        token_index: int,
        block_raw: str,
        block_char_start: int,
        mapper: "_SourceMapper",
        snapshot_id: str,
        provenance_ref: str,
        source: SourceArtifact,
        line_start: int,
        line_end: int,
    ) -> list[EvidenceUnit]:
        children = token.children or []
        result: list[EvidenceUnit] = []
        cursor = 0
        occurrence = 0
        child_index = 0
        while child_index < len(children):
            child = children[child_index]
            if child.type != "em_open":
                child_index += 1
                continue
            markup = child.markup or "*"
            inner_parts: list[str] = []
            close_index = child_index + 1
            depth = 1
            while close_index < len(children):
                current = children[close_index]
                if current.type == "em_open":
                    depth += 1
                elif current.type == "em_close":
                    depth -= 1
                    if depth == 0:
                        break
                if depth >= 1 and current.type in {"text", "code_inline"}:
                    inner_parts.append(current.content)
                close_index += 1
            if close_index >= len(children):
                child_index += 1
                continue

            needle = f"{markup}{''.join(inner_parts)}{markup}"
            local_start = block_raw.find(needle, cursor)
            if local_start < 0:
                child_index = close_index + 1
                continue
            local_end = local_start + len(needle)
            char_start = block_char_start + local_start
            char_end = block_char_start + local_end
            byte_start, byte_end = mapper.byte_range(char_start, char_end)
            result.append(
                self._syntax_unit(
                    snapshot_id=snapshot_id,
                    provenance_ref=provenance_ref,
                    source=source,
                    unit_index=f"token:{token_index}:emphasis:{occurrence}",
                    token_type="emphasis",
                    tag="em",
                    markup=markup,
                    info="",
                    raw_slice=needle,
                    char_start=char_start,
                    char_end=char_end,
                    byte_start=byte_start,
                    byte_end=byte_end,
                    line_start=line_start,
                    line_end=line_end,
                )
            )
            occurrence += 1
            cursor = local_end
            child_index = close_index + 1
        return result

    def _require_blob_store(self) -> LocalBlobStore:
        if self.blob_store is None:
            raise RuntimeError("Markdown evidence extraction requires a blob store")
        return self.blob_store


class _SourceMapper:
    def __init__(self, *, text: str, bom_size: int = 0) -> None:
        self.text = text
        self.bom_size = bom_size
        self.lines = text.splitlines(keepends=True)
        if not self.lines and text:
            self.lines = [text]
        self.char_starts = [0]
        for line in self.lines:
            self.char_starts.append(self.char_starts[-1] + len(line))

    def line_range(self, start_line: int, end_line: int) -> tuple[int, int, int, int]:
        char_start = self.char_starts[start_line]
        char_end = self.char_starts[end_line]
        byte_start, byte_end = self.byte_range(char_start, char_end)
        return char_start, char_end, byte_start, byte_end

    def byte_range(self, char_start: int, char_end: int) -> tuple[int, int]:
        byte_start = self.bom_size + len(self.text[:char_start].encode("utf-8"))
        byte_end = self.bom_size + len(self.text[:char_end].encode("utf-8"))
        return byte_start, byte_end
