from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from voxcodex.adapters.markdown import MarkdownAdapter
from voxcodex.digests import sha256_bytes
from voxcodex.domain.evidence import ExtractionProfile
from voxcodex.domain.source import SourceArtifact
from voxcodex.storage.blobs import LocalBlobStore


MARKDOWN = """## Prólogo

*O ar está pesado.*

```python
print(\"x\")
```
"""


def make_source(path: Path) -> SourceArtifact:
    data = path.read_bytes()
    return SourceArtifact(
        id=f"source:{sha256_bytes(data)}",
        media_type="text/markdown",
        original_filename=path.name,
        byte_size=len(data),
        checksum=sha256_bytes(data),
        acquisition_kind="synthetic_test",
        original_uri=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def extract_units(path: Path, store: LocalBlobStore):
    source = make_source(path)
    adapter = MarkdownAdapter(blob_store=store)
    profile = ExtractionProfile(
        id="extraction-profile:markdown:v1",
        adapter="markdown",
        adapter_version=adapter.adapter_version,
        options={},
    )
    snapshot = adapter.extract(source, path, profile)
    partition, units = adapter.load_partition(snapshot.partition_refs[0])
    return source, snapshot, partition, units


def test_markdown_evidence_preserves_exact_heading_emphasis_and_fence_ranges(tmp_path: Path):
    path = tmp_path / "chapter.md"
    path.write_text(MARKDOWN, encoding="utf-8", newline="\n")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    store = LocalBlobStore(tmp_path / "blobs")

    source, snapshot, partition, units = extract_units(path, store)

    assert len(snapshot.partition_refs) == 1
    assert partition.partition_key == "file:0"
    syntax_units = [unit for unit in units if unit.evidence_class == "syntax_unit"]
    token_types = {unit.native_payload["token_type"] for unit in syntax_units}
    assert "heading_open" in token_types
    assert "emphasis" in token_types
    assert "fence" in token_types

    for unit in syntax_units:
        locator = unit.source_locator
        char_start = locator["char_start"]
        char_end = locator["char_end"]
        byte_start = locator["byte_start"]
        byte_end = locator["byte_end"]
        assert text[char_start:char_end] == unit.native_payload["raw_slice"]
        assert raw[byte_start:byte_end].decode("utf-8") == unit.native_payload["raw_slice"]
        assert unit.native_payload["raw_source_digest"] == source.checksum

    emphasis = next(unit for unit in syntax_units if unit.native_payload["token_type"] == "emphasis")
    assert emphasis.native_payload["raw_slice"] == "*O ar está pesado.*"
    assert emphasis.native_payload["markup"] == "*"

    fence = next(unit for unit in syntax_units if unit.native_payload["token_type"] == "fence")
    assert fence.native_payload["raw_slice"] == "```python\nprint(\"x\")\n```\n"

    serialized = "\n".join(unit.model_dump_json() for unit in units)
    assert "narrative.prologue" not in serialized


def test_lf_and_crlf_have_distinct_raw_evidence_but_compatible_syntax(tmp_path: Path):
    lf_path = tmp_path / "lf.md"
    crlf_path = tmp_path / "crlf.md"
    lf_path.write_bytes(MARKDOWN.encode("utf-8"))
    crlf_path.write_bytes(MARKDOWN.replace("\n", "\r\n").encode("utf-8"))
    store = LocalBlobStore(tmp_path / "blobs")

    lf_source, lf_snapshot, _, lf_units = extract_units(lf_path, store)
    crlf_source, crlf_snapshot, _, crlf_units = extract_units(crlf_path, store)

    assert lf_source.checksum != crlf_source.checksum
    assert lf_snapshot.snapshot_digest != crlf_snapshot.snapshot_digest

    def syntax_signature(units):
        return [
            (unit.native_payload["token_type"], unit.native_payload.get("markup"))
            for unit in units
            if unit.evidence_class == "syntax_unit"
        ]

    assert syntax_signature(lf_units) == syntax_signature(crlf_units)
