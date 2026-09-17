from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from typer.testing import CliRunner

from voxcodex.cli import app
from voxcodex.digests import canonical_json_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, ProcessorIdentity
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


KINDS = (
    "paragraph",
    "verse",
    "terminal_command",
    "table_cell",
    "footnote",
    "formula",
)


def _put_payload(blobs: LocalBlobStore, payload: dict) -> str:
    return blobs.put_bytes(canonical_json_bytes(payload)).sha256


def _workspace(home: Path) -> MetadataStore:
    home.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{home / 'metadata.db'}")
    metadata.create_all(engine)
    return MetadataStore(engine)


def _activity(activity_id: str, activity_type: str) -> ProcessingActivity:
    now = datetime(2026, 9, 17, tzinfo=UTC)
    return ProcessingActivity(
        id=activity_id,
        type=activity_type,
        processor=ProcessorIdentity(kind="python", name=activity_type, version="0.1"),
        configuration_ref="config:test",
        started_at=now,
        completed_at=now,
        status="succeeded",
    )


@pytest.mark.parametrize("object_kind", KINDS)
def test_trace_cli_reaches_evidence_locator_and_source_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    object_kind: str,
):
    home = tmp_path / ".voxcodex"
    blobs = LocalBlobStore(home / "blobs")
    store = _workspace(home)

    source_payload = {
        "id": "source:test",
        "checksum": "s" * 64,
        "media_type": "application/pdf",
        "original_filename": "known.pdf",
    }
    evidence_payload = {
        "id": "evidence:p6:line7",
        "source_artifact_ref": "source:test",
        "evidence_class": "line",
        "surface": "known surface",
        "locator": {
            "source_page_index": 5,
            "printed_page_label": "6",
            "region": {"x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.3},
        },
    }
    canonical_payload = {
        "id": f"canonical:{object_kind}:test",
        "object_kind": object_kind,
        "source_anchor_refs": ["anchor:test"],
    }

    source = ArtifactRef(
        id="source:test",
        digest=_put_payload(blobs, source_payload),
        kind="source_artifact",
    )
    evidence = ArtifactRef(
        id="evidence:p6:line7",
        digest=_put_payload(blobs, evidence_payload),
        kind="evidence_unit",
    )
    canonical = ArtifactRef(
        id=f"canonical:{object_kind}:test",
        digest=_put_payload(blobs, canonical_payload),
        kind=f"canonical_{object_kind}",
    )
    for ref in (source, evidence, canonical):
        store.register_artifact(ref)

    extract_activity = _activity("activity:extract:test", "source_evidence")
    materialize_activity = _activity("activity:materialize:test", "materialization")
    store.register_activity(extract_activity)
    store.register_activity(materialize_activity)
    store.register_derivation(
        Derivation(
            id="derivation:extract:test",
            activity_ref=extract_activity.id,
            input_refs=(source,),
            output_refs=(evidence,),
            derivation_kind="extracted",
        )
    )
    store.register_derivation(
        Derivation(
            id=f"derivation:materialize:{object_kind}",
            activity_ref=materialize_activity.id,
            input_refs=(evidence,),
            output_refs=(canonical,),
            derivation_kind="materialized",
        )
    )

    monkeypatch.setenv("VOXCODEX_HOME", str(home))
    result = CliRunner().invoke(app, ["trace", canonical.id])

    assert result.exit_code == 0, result.stdout
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert lines[0]["artifact_id"] == canonical.id
    assert any(item.get("derivation_id") == f"derivation:materialize:{object_kind}" for item in lines)
    assert any(item.get("activity_id") == "activity:materialize:test" for item in lines)
    evidence_items = [item for item in lines if item.get("artifact_id") == evidence.id]
    assert evidence_items
    assert evidence_items[0]["locator"]["source_page_index"] == 5
    assert evidence_items[0]["locator"]["printed_page_label"] == "6"
    source_items = [item for item in lines if item.get("artifact_id") == source.id]
    assert source_items
    assert source_items[0]["checksum"] == "s" * 64
