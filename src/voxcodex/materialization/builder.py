from __future__ import annotations

from datetime import UTC, datetime
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import Field

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.content import DocumentNode
from voxcodex.domain.cbm.document import CanonicalDocument, CanonicalRevision
from voxcodex.domain.cbm.validation import ValidationReport
from voxcodex.domain.common import FrozenModel
from voxcodex.domain.reconstruction import ReconstructionUnit
from voxcodex.materialization.mappings import RoleMappingRegistry


class CanonicalTargetContext(FrozenModel):
    canonical_document_ref: str | None = None
    work_ref: str
    edition_ref: str
    source_artifact_refs: tuple[str, ...] = Field(min_length=1)
    base_revision_ref: str | None = None
    assertion_provenance_ref: str


class MaterializationIssue(FrozenModel):
    id: str
    issue_type: str
    classification: Literal["PROCESSING_FAILURE", "MODEL_GAP", "MODEL_FAILURE"]
    affected_refs: tuple[str, ...] = ()
    message: str


class RegistryShard(FrozenModel):
    index: int
    object_refs: tuple[str, ...]
    digest: str


class RegistryManifest(FrozenModel):
    registry_name: str
    object_count: int
    object_refs: tuple[str, ...]
    shards: tuple[RegistryShard, ...]
    shard_digests: tuple[str, ...]
    manifest_digest: str


class CanonicalDraft(FrozenModel):
    canonical_document: CanonicalDocument
    nodes: tuple[DocumentNode, ...] = ()
    issues: tuple[MaterializationIssue, ...] = ()
    unmaterialized_unit_refs: tuple[str, ...] = ()


class FrozenRevisionRecord(FrozenModel):
    revision: CanonicalRevision
    semantic_digest: str
    authorizing_validation_report_ref: str
    supplemental_validation_report_refs: tuple[str, ...] = ()


def _stable_digest(payload: object) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def revision_semantic_digest(revision: CanonicalRevision) -> str:
    payload = {
        "canonical_document_ref": revision.canonical_document_ref,
        "revision_number": revision.revision_number,
        "parent_revision_refs": list(revision.parent_revision_refs),
        "schema_version": revision.schema_version,
        "root_node_ref": revision.root_node_ref,
        "node_registry_ref": revision.node_registry_ref,
        "content_registry_ref": revision.content_registry_ref,
        "entity_registry_ref": revision.entity_registry_ref,
        "semantic_registry_ref": revision.semantic_registry_ref,
        "structured_payload_registry_ref": revision.structured_payload_registry_ref,
        "source_mapping_manifest_ref": revision.source_mapping_manifest_ref,
        "fidelity_manifest_ref": revision.fidelity_manifest_ref,
        "provenance_manifest_ref": revision.provenance_manifest_ref,
    }
    return _stable_digest(payload)


def freeze_revision(
    revision: CanonicalRevision,
    validation_report: ValidationReport,
) -> FrozenRevisionRecord:
    if revision.lifecycle_state != "validated":
        raise ValueError("only a validated revision can be frozen")
    if validation_report.revision_ref != revision.id:
        raise ValueError("validation report revision_ref does not match revision")
    if validation_report.result != "PASS":
        raise ValueError("validation report does not authorize freeze")
    if revision.source_mapping_manifest_ref is None:
        raise ValueError("freeze requires source_mapping_manifest_ref")
    if revision.provenance_manifest_ref is None:
        raise ValueError("freeze requires provenance_manifest_ref")

    digest = revision_semantic_digest(revision)
    frozen_payload = revision.model_dump(mode="python")
    frozen_payload.update(
        lifecycle_state="frozen",
        validation_report_ref=validation_report.id,
        content_digest=digest,
    )
    frozen_revision = CanonicalRevision.model_validate(frozen_payload)
    return FrozenRevisionRecord(
        revision=frozen_revision,
        semantic_digest=digest,
        authorizing_validation_report_ref=validation_report.id,
    )


def with_supplemental_validation(
    frozen: FrozenRevisionRecord,
    validation_report: ValidationReport,
) -> FrozenRevisionRecord:
    if frozen.revision.lifecycle_state != "frozen":
        raise ValueError("supplemental validation requires a frozen revision")
    if validation_report.revision_ref != frozen.revision.id:
        raise ValueError("validation report revision_ref does not match revision")

    supplemental = frozen.supplemental_validation_report_refs
    if validation_report.id not in supplemental:
        supplemental = (*supplemental, validation_report.id)
    return FrozenRevisionRecord(
        revision=frozen.revision,
        semantic_digest=frozen.semantic_digest,
        authorizing_validation_report_ref=frozen.authorizing_validation_report_ref,
        supplemental_validation_report_refs=supplemental,
    )


def shard_registry_objects(
    registry_name: str,
    objects: dict[str, dict[str, Any]],
    *,
    max_objects_per_shard: int = 1000,
) -> RegistryManifest:
    if not 1 <= max_objects_per_shard <= 1000:
        raise ValueError("max_objects_per_shard must be between 1 and 1000")

    object_refs = tuple(sorted(objects))
    shards: list[RegistryShard] = []
    for index, offset in enumerate(range(0, len(object_refs), max_objects_per_shard)):
        refs = object_refs[offset : offset + max_objects_per_shard]
        payload = {
            "registry_name": registry_name,
            "index": index,
            "objects": [objects[ref] for ref in refs],
        }
        shards.append(
            RegistryShard(
                index=index,
                object_refs=refs,
                digest=_stable_digest(payload),
            )
        )

    shard_digests = tuple(shard.digest for shard in shards)
    manifest_payload = {
        "registry_name": registry_name,
        "object_count": len(object_refs),
        "object_refs": list(object_refs),
        "shard_digests": list(shard_digests),
    }
    return RegistryManifest(
        registry_name=registry_name,
        object_count=len(object_refs),
        object_refs=object_refs,
        shards=tuple(shards),
        shard_digests=shard_digests,
        manifest_digest=_stable_digest(manifest_payload),
    )


def build_canonical_draft(
    *,
    reconstruction_snapshot_digest: str,
    units: tuple[ReconstructionUnit, ...],
    target_context: CanonicalTargetContext,
    role_mappings: RoleMappingRegistry,
    source_anchor_refs_by_unit: Mapping[str, tuple[str, ...]] | None = None,
    structured_payload_refs_by_unit: Mapping[str, str] | None = None,
) -> CanonicalDraft:
    document_seed = {
        "work_ref": target_context.work_ref,
        "edition_ref": target_context.edition_ref,
        "source_artifact_refs": sorted(target_context.source_artifact_refs),
        "assertion_provenance_ref": target_context.assertion_provenance_ref,
    }
    document_id = target_context.canonical_document_ref or (
        f"canonical-document:{_stable_digest(document_seed)}"
    )
    revision_seed = {
        "canonical_document_ref": document_id,
        "reconstruction_snapshot_digest": reconstruction_snapshot_digest,
        "base_revision_ref": target_context.base_revision_ref,
    }
    revision_ref = f"canonical-revision:{_stable_digest(revision_seed)}"
    canonical_document = CanonicalDocument(
        id=document_id,
        work_ref=target_context.work_ref,
        edition_ref=target_context.edition_ref,
        source_artifact_refs=tuple(sorted(target_context.source_artifact_refs)),
        revision_refs=(revision_ref,),
        created_at=datetime(1970, 1, 1, tzinfo=UTC),
    )

    materialized: list[DocumentNode] = []
    issues: list[MaterializationIssue] = []
    unmaterialized: list[str] = []

    sorted_units = sorted(units, key=lambda unit: (unit.order_key, unit.id))
    id_map = {
        unit.id: f"node:{_stable_digest({'snapshot_digest': reconstruction_snapshot_digest, 'stable_key': unit.id})}"
        for unit in sorted_units
    }

    for unit in sorted_units:
        resolved_role = unit.properties.get("resolved_role")
        mapping = role_mappings.resolve(resolved_role) if isinstance(resolved_role, str) else None
        if mapping is None:
            role_label = resolved_role if isinstance(resolved_role, str) else "<missing>"
            issue_seed = {
                "snapshot_digest": reconstruction_snapshot_digest,
                "unit_ref": unit.id,
                "issue_type": "unmapped_role",
                "role": role_label,
            }
            issues.append(
                MaterializationIssue(
                    id=f"materialization-issue:{_stable_digest(issue_seed)}",
                    issue_type="unmapped_role",
                    classification="MODEL_GAP",
                    affected_refs=(unit.id,),
                    message=(
                        "resolved reconstruction role has no registered CBM v0.1 mapping: "
                        f"{role_label}"
                    ),
                )
            )
            unmaterialized.append(unit.id)
            continue

        parent_ref = id_map.get(unit.parent_ref) if unit.parent_ref is not None else None
        materialized.append(
            DocumentNode(
                id=id_map[unit.id],
                parent_ref=parent_ref,
                order_key=unit.order_key,
                node_class=mapping.node_class,
                role=mapping.cbm_role,
                structured_payload_ref=(
                    structured_payload_refs_by_unit.get(unit.id)
                    if structured_payload_refs_by_unit is not None
                    else None
                ),
                source_anchor_refs=(
                    source_anchor_refs_by_unit.get(unit.id, ())
                    if source_anchor_refs_by_unit is not None
                    else ()
                ),
                provenance_ref=unit.provenance_ref,
            )
        )

    return CanonicalDraft(
        canonical_document=canonical_document,
        nodes=tuple(materialized),
        issues=tuple(issues),
        unmaterialized_unit_refs=tuple(unmaterialized),
    )
