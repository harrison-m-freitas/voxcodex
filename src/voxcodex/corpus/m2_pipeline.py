from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from sqlalchemy import create_engine

from voxcodex.adapters.markdown import MarkdownAdapter
from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.corpus.evolution import SchemaEvolutionObservation
from voxcodex.corpus.holdout_execution import HoldoutExecutionSpec
from voxcodex.corpus.runner import ResultClass
from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.document import CanonicalRevision
from voxcodex.domain.cbm.structured import FormulaPayload, TablePayload
from voxcodex.domain.evidence import EvidenceSnapshot, EvidenceUnit, ExtractionProfile
from voxcodex.domain.source import SourceArtifact
from voxcodex.domain.common import FrozenModel
from voxcodex.materialization.anchors import AnchorEvidence, build_source_anchors
from voxcodex.materialization.builder import (
    CanonicalTargetContext,
    build_canonical_draft,
    freeze_revision,
    shard_registry_objects,
)
from voxcodex.materialization.mappings import (
    RoleProfileRegistry,
    materialize_formula_payload,
    materialize_table_payload,
)
from voxcodex.reconstruction.engine import ReconstructionEngine
from voxcodex.reconstruction.production import (
    ProductionEvidenceStage,
    production_reconstruction_profile,
)
from voxcodex.reconstruction.structured import FormulaCandidate, TableCandidate
from voxcodex.storage.blobs import LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata
from voxcodex.validation.engine import RevisionValidationBundle, validate_revision
from voxcodex.validation.policies import EvidenceAccountability, m2_poc_strict


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class SourceIdentityError(ValueError):
    """Raised when physical bytes do not match the frozen holdout identity."""


class HoldoutCaseRun(FrozenModel):
    holdout_id: str
    corpus_case_id: str
    selected_scope: dict[str, object]
    source_digest_verified: bool
    evidence_snapshot_ref: str | None = None
    evidence_snapshot_digest: str | None = None
    reconstruction_snapshot_ref: str | None = None
    reconstruction_snapshot_digest: str | None = None
    canonical_revision_ref: str | None = None
    frozen_revision_digest: str | None = None
    validation_report_ref: str | None = None
    validation_result: str | None = None
    evidence_accountability: tuple[EvidenceAccountability, ...] = ()
    result_class: ResultClass
    diagnostic: str
    evolution_observation: SchemaEvolutionObservation | None = None


class M2PipelineProcessor:
    def __init__(self, work_root: Path) -> None:
        self.work_root = Path(work_root)
        self.work_root.mkdir(parents=True, exist_ok=True)
        self.blob_store = LocalBlobStore(self.work_root / "blobs")
        engine = create_engine(f"sqlite:///{self.work_root / 'metadata.db'}")
        metadata.create_all(engine)
        self.metadata_store = MetadataStore(engine)

    def process(
        self,
        spec: HoldoutExecutionSpec,
        source_path: Path,
    ) -> HoldoutCaseRun:
        selected_scope = _selected_scope(spec)
        try:
            physical_bytes = self._verify_container(spec, source_path)
            source_digest_verified = True
            (
                adapter,
                source,
                evidence_path,
                extraction_profile,
                source_refs,
            ) = self._prepare_evidence_input(spec, source_path, physical_bytes)

            snapshot = self._extract_evidence(
                spec,
                adapter,
                source,
                evidence_path,
                extraction_profile,
            )
            evidence_units = self._load_evidence_units(adapter, snapshot)

            reconstruction_engine = ReconstructionEngine(
                stages=(
                    ProductionEvidenceStage(
                        evidence_units,
                        production_reconstruction_profile(),
                    ),
                ),
                blob_store=self.blob_store,
                metadata_store=self.metadata_store,
                now=lambda: _EPOCH,
            )
            reconstruction = reconstruction_engine.assemble(
                snapshot,
                reconstruction_profile_ref="reconstruction-profile:m2-production:v0.1",
            )
            reconstruction_payload = reconstruction_engine.load_snapshot_payload(
                reconstruction
            )

            target_context = CanonicalTargetContext(
                work_ref=f"work:holdout:{spec.corpus_case_id}",
                edition_ref=f"edition:holdout:{spec.corpus_case_id}",
                source_artifact_refs=source_refs,
                assertion_provenance_ref=f"candidate:{spec.candidate_digest}",
            )
            role_mappings = RoleProfileRegistry.v01_defaults()
            provisional = build_canonical_draft(
                reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                units=reconstruction_payload.units,
                target_context=target_context,
                role_mappings=role_mappings,
            )

            if provisional.issues:
                affected_units = set(provisional.unmaterialized_unit_refs)
                affected_evidence = tuple(
                    sorted(
                        {
                            ref.id
                            for unit in reconstruction_payload.units
                            if unit.id in affected_units
                            for ref in unit.evidence_refs
                        }
                    )
                )
                observation = SchemaEvolutionObservation(
                    case_id=spec.corpus_case_id,
                    source_ref=str(source_path),
                    result_class="MODEL_GAP",
                    phenomenon="unmapped reconstruction role during CBM v0.1 materialization",
                    affected_model_area="CBM v0.1 role mapping",
                    evidence_refs=affected_evidence,
                    candidate_resolutions=(
                        "record schema-evolution observation and evaluate a future versioned candidate",
                    ),
                )
                return HoldoutCaseRun(
                    holdout_id=spec.holdout_id,
                    corpus_case_id=spec.corpus_case_id,
                    selected_scope=selected_scope,
                    source_digest_verified=source_digest_verified,
                    evidence_snapshot_ref=snapshot.id,
                    evidence_snapshot_digest=snapshot.snapshot_digest,
                    reconstruction_snapshot_ref=reconstruction.id,
                    reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                    result_class="MODEL_GAP",
                    diagnostic="materialization produced one or more unmapped CBM roles",
                    evolution_observation=observation,
                )

            evidence_by_id = {unit.id: unit for unit in evidence_units}
            ordered_units = tuple(
                sorted(reconstruction_payload.units, key=lambda unit: (unit.order_key, unit.id))
            )
            ordered_nodes = provisional.nodes
            if len(ordered_units) != len(ordered_nodes):
                raise RuntimeError(
                    "materialization lost reconstruction units without an explicit issue"
                )
            node_by_unit = {
                unit.id: node
                for unit, node in zip(ordered_units, ordered_nodes, strict=True)
            }

            structured_payload_refs, table_payloads = _structured_payloads(
                ordered_units
            )
            anchors_by_unit, all_anchor_refs = _source_anchors(
                ordered_units,
                node_by_unit,
                evidence_by_id,
                source.id,
                snapshot.extraction_activity_ref,
            )

            draft = build_canonical_draft(
                reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                units=reconstruction_payload.units,
                target_context=target_context,
                role_mappings=role_mappings,
                source_anchor_refs_by_unit=anchors_by_unit,
                structured_payload_refs_by_unit=structured_payload_refs,
            )
            if draft.issues:
                raise RuntimeError("materialization became inconsistent after anchor binding")

            canonical_ref_by_evidence: dict[str, str] = {}
            for unit in ordered_units:
                node = next(node for node in draft.nodes if node.id == node_by_unit[unit.id].id)
                for ref in unit.evidence_refs:
                    canonical_ref_by_evidence.setdefault(ref.id, node.id)

            accountability = _evidence_accountability(
                evidence_units,
                canonical_ref_by_evidence,
            )

            root_nodes = tuple(node for node in draft.nodes if node.parent_ref is None)
            if len(root_nodes) != 1:
                raise RuntimeError(
                    f"expected exactly one canonical root, found {len(root_nodes)}"
                )

            revision = _validated_revision(
                draft_nodes=draft.nodes,
                canonical_document_ref=draft.canonical_document.id,
                revision_ref=draft.canonical_document.revision_refs[0],
                root_node_ref=root_nodes[0].id,
                table_payloads=table_payloads,
                structured_payload_refs=structured_payload_refs,
                all_anchor_refs=all_anchor_refs,
            )
            validation_report = validate_revision(
                RevisionValidationBundle(
                    revision=revision,
                    nodes=draft.nodes,
                    tables=table_payloads,
                    source_anchor_refs=all_anchor_refs,
                    provenance_refs=tuple(
                        sorted({node.provenance_ref for node in draft.nodes})
                    ),
                    evidence_accountability=accountability,
                ),
                m2_poc_strict(),
            )

            has_suspected_loss = any(
                item.significance == "significant"
                and item.classification == "suspected_loss"
                for item in accountability
            )
            if has_suspected_loss:
                return HoldoutCaseRun(
                    holdout_id=spec.holdout_id,
                    corpus_case_id=spec.corpus_case_id,
                    selected_scope=selected_scope,
                    source_digest_verified=True,
                    evidence_snapshot_ref=snapshot.id,
                    evidence_snapshot_digest=snapshot.snapshot_digest,
                    reconstruction_snapshot_ref=reconstruction.id,
                    reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                    canonical_revision_ref=revision.id,
                    validation_report_ref=validation_report.id,
                    validation_result=validation_report.result,
                    evidence_accountability=accountability,
                    result_class="MODEL_FAILURE",
                    diagnostic="significant source evidence remains suspected_loss",
                    evolution_observation=SchemaEvolutionObservation(
                        case_id=spec.corpus_case_id,
                        source_ref=str(source_path),
                        result_class="MODEL_FAILURE",
                        phenomenon="significant source evidence was not represented canonically",
                        affected_model_area="M2 reconstruction/materialization",
                        evidence_refs=tuple(
                            item.evidence_ref
                            for item in accountability
                            if item.significance == "significant"
                            and item.classification == "suspected_loss"
                        ),
                    ),
                )

            if validation_report.result != "PASS":
                return HoldoutCaseRun(
                    holdout_id=spec.holdout_id,
                    corpus_case_id=spec.corpus_case_id,
                    selected_scope=selected_scope,
                    source_digest_verified=True,
                    evidence_snapshot_ref=snapshot.id,
                    evidence_snapshot_digest=snapshot.snapshot_digest,
                    reconstruction_snapshot_ref=reconstruction.id,
                    reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                    canonical_revision_ref=revision.id,
                    validation_report_ref=validation_report.id,
                    validation_result=validation_report.result,
                    evidence_accountability=accountability,
                    result_class="MODEL_FAILURE",
                    diagnostic=(
                        "strict M2 ValidationPolicy did not PASS; "
                        f"result={validation_report.result}"
                    ),
                    evolution_observation=SchemaEvolutionObservation(
                        case_id=spec.corpus_case_id,
                        source_ref=str(source_path),
                        result_class="MODEL_FAILURE",
                        phenomenon="frozen M2 pipeline produced a non-passing canonical revision",
                        affected_model_area="M2 reconstruction/materialization/validation",
                    ),
                )

            frozen = freeze_revision(revision, validation_report)
            return HoldoutCaseRun(
                holdout_id=spec.holdout_id,
                corpus_case_id=spec.corpus_case_id,
                selected_scope=selected_scope,
                source_digest_verified=True,
                evidence_snapshot_ref=snapshot.id,
                evidence_snapshot_digest=snapshot.snapshot_digest,
                reconstruction_snapshot_ref=reconstruction.id,
                reconstruction_snapshot_digest=reconstruction.snapshot_digest,
                canonical_revision_ref=frozen.revision.id,
                frozen_revision_digest=frozen.semantic_digest,
                validation_report_ref=validation_report.id,
                validation_result=validation_report.result,
                evidence_accountability=accountability,
                result_class="PASS",
                diagnostic="frozen M2 pipeline completed with strict validation PASS",
            )
        except (SourceIdentityError, BadZipFile, OSError, ValueError, IndexError) as exc:
            return HoldoutCaseRun(
                holdout_id=spec.holdout_id,
                corpus_case_id=spec.corpus_case_id,
                selected_scope=selected_scope,
                source_digest_verified=False,
                result_class="PROCESSING_FAILURE",
                diagnostic=str(exc),
            )
        except Exception as exc:
            return HoldoutCaseRun(
                holdout_id=spec.holdout_id,
                corpus_case_id=spec.corpus_case_id,
                selected_scope=selected_scope,
                source_digest_verified=True,
                result_class="PROCESSING_FAILURE",
                diagnostic=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _verify_container(
        spec: HoldoutExecutionSpec,
        source_path: Path,
    ) -> bytes:
        raw = Path(source_path).read_bytes()
        if len(raw) != spec.source_byte_size:
            raise SourceIdentityError(
                "source byte size does not match frozen holdout identity"
            )
        if sha256_bytes(raw) != spec.source_sha256:
            raise SourceIdentityError(
                "source digest does not match frozen holdout identity"
            )
        return raw

    def _prepare_evidence_input(
        self,
        spec: HoldoutExecutionSpec,
        source_path: Path,
        physical_bytes: bytes,
    ):
        if spec.zip_member_path is not None:
            with ZipFile(source_path) as archive:
                try:
                    member_bytes = archive.read(spec.zip_member_path)
                except KeyError as exc:
                    raise SourceIdentityError(
                        f"frozen Markdown ZIP member is missing: {spec.zip_member_path}"
                    ) from exc
            if spec.zip_member_byte_size is None or len(member_bytes) != spec.zip_member_byte_size:
                raise SourceIdentityError("selected Markdown member byte size mismatch")
            if (
                spec.zip_member_sha256 is None
                or sha256_bytes(member_bytes) != spec.zip_member_sha256
            ):
                raise SourceIdentityError("selected Markdown member digest mismatch")

            selected_root = self.work_root / "selected-members"
            selected_root.mkdir(parents=True, exist_ok=True)
            selected_path = selected_root / f"{spec.zip_member_sha256}.md"
            if selected_path.exists() and selected_path.read_bytes() != member_bytes:
                raise SourceIdentityError(
                    "selected Markdown member work artifact conflicts with frozen bytes"
                )
            selected_path.write_bytes(member_bytes)
            member_source = SourceArtifact(
                id=f"source:selected-markdown:{spec.zip_member_sha256}",
                media_type="text/markdown",
                original_filename=Path(spec.zip_member_path).name,
                byte_size=len(member_bytes),
                checksum=spec.zip_member_sha256,
                acquisition_kind="frozen_zip_member",
                original_uri=None,
                created_at=_EPOCH,
            )
            adapter = MarkdownAdapter(blob_store=self.blob_store)
            profile = ExtractionProfile(
                id="extraction-profile:m2-pipeline:markdown:v0.1",
                adapter="markdown",
                adapter_version=adapter.adapter_version,
                options={},
            )
            container_source_ref = (
                "source:holdout-container:" + sha256_bytes(physical_bytes)
            )
            return (
                adapter,
                member_source,
                selected_path,
                profile,
                (container_source_ref, member_source.id),
            )

        media_type = (
            "application/pdf"
            if spec.format.casefold() == "pdf"
            else "text/markdown"
        )
        source = SourceArtifact(
            id=f"source:holdout:{spec.source_sha256}",
            media_type=media_type,
            original_filename=source_path.name,
            byte_size=len(physical_bytes),
            checksum=spec.source_sha256,
            acquisition_kind="frozen_holdout_source",
            original_uri=None,
            created_at=_EPOCH,
        )
        if media_type == "application/pdf":
            adapter = PdfAdapter(blob_store=self.blob_store)
            profile = ExtractionProfile(
                id="extraction-profile:m2-pipeline:pdf:v0.1",
                adapter="pdf",
                adapter_version=adapter.adapter_version,
                options={"glyph_runs": True},
            )
        else:
            adapter = MarkdownAdapter(blob_store=self.blob_store)
            profile = ExtractionProfile(
                id="extraction-profile:m2-pipeline:markdown:v0.1",
                adapter="markdown",
                adapter_version=adapter.adapter_version,
                options={},
            )
        return adapter, source, source_path, profile, (source.id,)

    @staticmethod
    def _extract_evidence(
        spec: HoldoutExecutionSpec,
        adapter,
        source: SourceArtifact,
        evidence_path: Path,
        extraction_profile: ExtractionProfile,
    ) -> EvidenceSnapshot:
        if isinstance(adapter, PdfAdapter):
            if not spec.selected_page_indexes:
                raise SourceIdentityError(
                    "frozen PDF holdout execution requires selected page indexes"
                )
            return adapter.extract(
                source,
                evidence_path,
                extraction_profile,
                page_indexes=spec.selected_page_indexes,
            )
        return adapter.extract(source, evidence_path, extraction_profile)

    @staticmethod
    def _load_evidence_units(
        adapter,
        snapshot: EvidenceSnapshot,
    ) -> tuple[EvidenceUnit, ...]:
        units: list[EvidenceUnit] = []
        for ref in snapshot.partition_refs:
            _partition, partition_units = adapter.load_partition(ref)
            units.extend(partition_units)
        if not units:
            raise RuntimeError("evidence extraction produced no EvidenceUnits")
        return tuple(units)


def _selected_scope(spec: HoldoutExecutionSpec) -> dict[str, object]:
    if spec.zip_member_path is not None:
        return {
            "zip_member_path": spec.zip_member_path,
            "member_sha256": spec.zip_member_sha256 or "",
            "member_byte_size": spec.zip_member_byte_size or 0,
        }
    return {"page_indexes": list(spec.selected_page_indexes)}


def _structured_payloads(
    units,
) -> tuple[dict[str, str], tuple[TablePayload, ...]]:
    refs: dict[str, str] = {}
    tables: list[TablePayload] = []
    for unit in units:
        raw_table = unit.properties.get("table_candidate")
        if isinstance(raw_table, dict):
            table = materialize_table_payload(
                TableCandidate.model_validate(raw_table),
                content_refs_by_evidence={},
            )
            refs[unit.id] = table.id
            tables.append(table)
            continue

        raw_formula = unit.properties.get("formula_candidate")
        if isinstance(raw_formula, dict):
            formula: FormulaPayload = materialize_formula_payload(
                FormulaCandidate.model_validate(raw_formula)
            )
            refs[unit.id] = formula.id
    return refs, tuple(tables)


def _source_anchors(
    units,
    node_by_unit,
    evidence_by_id: dict[str, EvidenceUnit],
    source_artifact_ref: str,
    extraction_ref: str,
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    by_unit: dict[str, tuple[str, ...]] = {}
    all_refs: list[str] = []
    for unit in units:
        evidence: list[AnchorEvidence] = []
        for ref in unit.evidence_refs:
            observed = evidence_by_id.get(ref.id)
            if observed is None:
                continue
            geometry = observed.normalized_geometry
            locator_page = observed.source_locator.get("page_index")
            page_index = locator_page if isinstance(locator_page, int) else None
            kwargs: dict[str, object] = {}
            if (
                geometry is not None
                and geometry.x1 > geometry.x0
                and geometry.y1 > geometry.y0
            ):
                kwargs.update(
                    x0=geometry.x0,
                    y0=geometry.y0,
                    x1=geometry.x1,
                    y1=geometry.y1,
                )
            evidence.append(
                AnchorEvidence(
                    evidence_ref=observed.id,
                    source_artifact_ref=source_artifact_ref,
                    extraction_ref=extraction_ref,
                    source_page_index=page_index,
                    **kwargs,
                )
            )
        if not evidence:
            raise RuntimeError(
                f"reconstruction unit has no source evidence for anchoring: {unit.id}"
            )
        anchors = build_source_anchors(node_by_unit[unit.id].id, tuple(evidence))
        by_unit[unit.id] = tuple(anchor.id for anchor in anchors)
        all_refs.extend(anchor.id for anchor in anchors)
    return by_unit, tuple(sorted(set(all_refs)))


def _evidence_accountability(
    evidence_units: tuple[EvidenceUnit, ...],
    canonical_ref_by_evidence: dict[str, str],
) -> tuple[EvidenceAccountability, ...]:
    canonical_ranges = {
        _text_range(unit)
        for unit in evidence_units
        if unit.id in canonical_ref_by_evidence and _text_range(unit) is not None
    }
    result: list[EvidenceAccountability] = []
    for unit in evidence_units:
        canonical_ref = canonical_ref_by_evidence.get(unit.id)
        if canonical_ref is not None:
            significance = (
                "significant"
                if unit.evidence_class in {"text_span", "syntax_unit", "asset"}
                else "non_significant"
            )
            result.append(
                EvidenceAccountability(
                    evidence_ref=unit.id,
                    significance=significance,
                    classification="canonicalized",
                    canonical_ref=canonical_ref,
                )
            )
            continue

        if unit.evidence_class == "syntax_unit":
            range_key = _text_range(unit)
            if range_key is not None and range_key in canonical_ranges:
                result.append(
                    EvidenceAccountability(
                        evidence_ref=unit.id,
                        significance="non_significant",
                        classification="intentionally_noncanonical",
                    )
                )
            else:
                result.append(
                    EvidenceAccountability(
                        evidence_ref=unit.id,
                        significance="significant",
                        classification="suspected_loss",
                    )
                )
            continue

        if unit.evidence_class in {"text_span", "asset"}:
            result.append(
                EvidenceAccountability(
                    evidence_ref=unit.id,
                    significance="significant",
                    classification="suspected_loss",
                )
            )
            continue

        result.append(
            EvidenceAccountability(
                evidence_ref=unit.id,
                significance="non_significant",
                classification="intentionally_noncanonical",
            )
        )
    return tuple(result)


def _text_range(unit: EvidenceUnit) -> tuple[int, int] | None:
    start = unit.source_locator.get("char_start")
    end = unit.source_locator.get("char_end")
    if isinstance(start, int) and isinstance(end, int):
        return start, end
    return None


def _validated_revision(
    *,
    draft_nodes,
    canonical_document_ref: str,
    revision_ref: str,
    root_node_ref: str,
    table_payloads: tuple[TablePayload, ...],
    structured_payload_refs: dict[str, str],
    all_anchor_refs: tuple[str, ...],
) -> CanonicalRevision:
    node_manifest = shard_registry_objects(
        "nodes",
        {
            node.id: node.model_dump(mode="json", exclude_none=True)
            for node in draft_nodes
        },
    )
    structured_digest = sha256_bytes(
        canonical_json_bytes(
            {
                "payload_refs": sorted(structured_payload_refs.values()),
                "tables": [
                    table.model_dump(mode="json", exclude_none=True)
                    for table in table_payloads
                ],
            }
        )
    )
    source_mapping_digest = sha256_bytes(
        canonical_json_bytes({"source_anchor_refs": list(all_anchor_refs)})
    )
    provenance_digest = sha256_bytes(
        canonical_json_bytes(
            {"provenance_refs": sorted({node.provenance_ref for node in draft_nodes})}
        )
    )
    empty_digest = sha256_bytes(canonical_json_bytes([]))
    return CanonicalRevision(
        id=revision_ref,
        canonical_document_ref=canonical_document_ref,
        revision_number=1,
        schema_version="0.1",
        root_node_ref=root_node_ref,
        node_registry_ref=f"node-registry:{node_manifest.manifest_digest}",
        content_registry_ref=f"content-registry:{empty_digest}",
        entity_registry_ref=f"entity-registry:{empty_digest}",
        semantic_registry_ref=f"semantic-registry:{empty_digest}",
        structured_payload_registry_ref=f"structured-registry:{structured_digest}",
        source_mapping_manifest_ref=f"source-mapping:{source_mapping_digest}",
        fidelity_manifest_ref=f"fidelity-manifest:{empty_digest}",
        provenance_manifest_ref=f"provenance-manifest:{provenance_digest}",
        lifecycle_state="validated",
        created_by_activity_ref=f"activity:m2-materialization:{revision_ref}",
        created_at=_EPOCH,
    )
