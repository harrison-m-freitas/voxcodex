from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select

from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import (
    artifacts,
    derivation_inputs,
    derivation_outputs,
    derivations,
    metadata,
    processing_activities,
)


class UnknownTraceArtifactError(KeyError):
    """Raised when provenance tracing starts from an unknown artifact."""


class TraceApplication:
    def __init__(self, home: Path) -> None:
        self.home = Path(home)
        self.blobs = LocalBlobStore(self.home / "blobs")
        engine = create_engine(f"sqlite:///{self.home / 'metadata.db'}")
        metadata.create_all(engine)
        self.metadata = MetadataStore(engine)

    def trace(self, artifact_id: str) -> tuple[dict[str, Any], ...]:
        root = self.metadata.get_artifact(artifact_id)
        if root is None:
            raise UnknownTraceArtifactError(artifact_id)

        events: list[dict[str, Any]] = []
        pending: deque[str] = deque([artifact_id])
        visited: set[str] = set()

        while pending:
            current_id = pending.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            ref = self.metadata.get_artifact(current_id)
            if ref is None:
                continue
            events.append(self._artifact_event(ref.id, ref.digest, ref.kind))

            for lineage in self._upstream_derivations(current_id):
                events.append(
                    {
                        "record_type": "derivation",
                        "derivation_id": lineage["derivation_id"],
                        "derivation_kind": lineage["derivation_kind"],
                        "output_artifact_id": current_id,
                    }
                )
                activity_payload = json.loads(lineage["activity_payload_json"])
                events.append(
                    {
                        "record_type": "activity",
                        "activity_id": lineage["activity_id"],
                        "activity_type": lineage["activity_type"],
                        "processor": activity_payload.get("processor"),
                        "configuration_ref": activity_payload.get("configuration_ref"),
                        "status": activity_payload.get("status"),
                    }
                )
                for input_id in lineage["input_artifact_ids"]:
                    if input_id not in visited:
                        pending.append(input_id)

        return tuple(events)

    def _artifact_event(self, artifact_id: str, digest: str, kind: str) -> dict[str, Any]:
        event: dict[str, Any] = {
            "record_type": "artifact",
            "artifact_id": artifact_id,
            "artifact_kind": kind,
            "digest": digest,
        }
        try:
            payload = json.loads(self.blobs.read_digest(digest))
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return event

        if kind == "evidence_unit":
            if "locator" in payload:
                event["locator"] = payload["locator"]
            if "source_artifact_ref" in payload:
                event["source_artifact_ref"] = payload["source_artifact_ref"]
            if "evidence_class" in payload:
                event["evidence_class"] = payload["evidence_class"]
        elif kind == "source_artifact":
            for key in ("checksum", "media_type", "original_filename", "original_uri"):
                if key in payload:
                    event[key] = payload[key]
        return event

    def _upstream_derivations(self, output_artifact_id: str) -> tuple[dict[str, Any], ...]:
        with self.metadata.engine.connect() as connection:
            rows = connection.execute(
                select(
                    derivations.c.id.label("derivation_id"),
                    derivations.c.derivation_kind,
                    processing_activities.c.id.label("activity_id"),
                    processing_activities.c.type.label("activity_type"),
                    processing_activities.c.payload_json.label("activity_payload_json"),
                )
                .select_from(
                    derivation_outputs
                    .join(derivations, derivation_outputs.c.derivation_id == derivations.c.id)
                    .join(processing_activities, derivations.c.activity_ref == processing_activities.c.id)
                )
                .where(derivation_outputs.c.artifact_ref == output_artifact_id)
                .order_by(derivations.c.id)
            ).all()

            result: list[dict[str, Any]] = []
            for row in rows:
                input_rows = connection.execute(
                    select(derivation_inputs.c.artifact_ref)
                    .where(derivation_inputs.c.derivation_id == row.derivation_id)
                    .order_by(derivation_inputs.c.artifact_ref)
                ).all()
                result.append(
                    {
                        "derivation_id": row.derivation_id,
                        "derivation_kind": row.derivation_kind,
                        "activity_id": row.activity_id,
                        "activity_type": row.activity_type,
                        "activity_payload_json": row.activity_payload_json,
                        "input_artifact_ids": tuple(input_row.artifact_ref for input_row in input_rows),
                    }
                )
        return tuple(result)
