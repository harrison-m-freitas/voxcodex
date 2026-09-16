from __future__ import annotations

from collections import deque

from sqlalchemy import Engine, event, insert, select

from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.processing import Derivation, ProcessingActivity, UsageRecord
from voxcodex.storage.schema import (
    artifacts,
    derivation_inputs,
    derivation_outputs,
    derivations,
    processing_activities,
    usage_records,
)


class MetadataStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        if engine.dialect.name == "sqlite":
            self._enable_sqlite_foreign_keys()

    def _enable_sqlite_foreign_keys(self) -> None:
        @event.listens_for(self.engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Engines can have an already-opened pooled connection from create_all.
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")

    def get_artifact(self, artifact_id: str) -> ArtifactRef | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                select(artifacts.c.id, artifacts.c.digest, artifacts.c.kind).where(
                    artifacts.c.id == artifact_id
                )
            ).one_or_none()
        if row is None:
            return None
        return ArtifactRef(id=row.id, digest=row.digest, kind=row.kind)

    def register_artifact(self, record: ArtifactRef) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(artifacts).values(id=record.id, digest=record.digest, kind=record.kind)
            )

    def register_activity(self, activity: ProcessingActivity) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(processing_activities).values(
                    id=activity.id,
                    type=activity.type,
                    status=activity.status,
                    payload_json=activity.model_dump_json(),
                )
            )

    def register_usage(self, usage: UsageRecord) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(usage_records).values(
                    id=usage.id,
                    activity_ref=usage.activity_ref,
                    payload_json=usage.model_dump_json(),
                )
            )

    def register_derivation(self, derivation: Derivation) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                insert(derivations).values(
                    id=derivation.id,
                    activity_ref=derivation.activity_ref,
                    derivation_kind=derivation.derivation_kind,
                    confidence_ref=derivation.confidence_ref,
                )
            )
            if derivation.input_refs:
                connection.execute(
                    insert(derivation_inputs),
                    [
                        {"derivation_id": derivation.id, "artifact_ref": ref.id}
                        for ref in derivation.input_refs
                    ],
                )
            if derivation.output_refs:
                connection.execute(
                    insert(derivation_outputs),
                    [
                        {"derivation_id": derivation.id, "artifact_ref": ref.id}
                        for ref in derivation.output_refs
                    ],
                )

    def get_downstream(self, ref: ArtifactRef) -> set[ArtifactRef]:
        discovered: dict[str, ArtifactRef] = {}
        pending: deque[str] = deque([ref.id])
        visited: set[str] = {ref.id}

        with self.engine.connect() as connection:
            while pending:
                current = pending.popleft()
                rows = connection.execute(
                    select(artifacts.c.id, artifacts.c.digest, artifacts.c.kind)
                    .select_from(
                        derivation_inputs
                        .join(
                            derivation_outputs,
                            derivation_inputs.c.derivation_id == derivation_outputs.c.derivation_id,
                        )
                        .join(artifacts, artifacts.c.id == derivation_outputs.c.artifact_ref)
                    )
                    .where(derivation_inputs.c.artifact_ref == current)
                ).all()
                for row in rows:
                    artifact = ArtifactRef(id=row.id, digest=row.digest, kind=row.kind)
                    discovered[artifact.id] = artifact
                    if artifact.id not in visited:
                        visited.add(artifact.id)
                        pending.append(artifact.id)

        return set(discovered.values())
