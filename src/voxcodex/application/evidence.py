from __future__ import annotations

from datetime import UTC, datetime
import mimetypes
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import create_engine

from voxcodex.adapters.markdown import MarkdownAdapter
from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.corpus.holdouts import HoldoutGuard
from voxcodex.corpus.registry import CorpusRegistry
from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef
from voxcodex.domain.evidence import EvidenceSnapshot, ExtractionProfile
from voxcodex.domain.source import SourceArtifact, SourceProfile
from voxcodex.storage.blobs import BlobRef, LocalBlobStore
from voxcodex.storage.metadata import MetadataStore
from voxcodex.storage.schema import metadata


class DirectCorpusSourceError(ValueError):
    """Raised when a corpus source path attempts to bypass HoldoutGuard."""


class UnknownArtifactError(KeyError):
    """Raised when an artifact ID is not present in the workspace metadata."""


class ArtifactConflictError(RuntimeError):
    """Raised when an immutable artifact ID resolves to conflicting content."""


class EvidenceApplication:
    def __init__(self, home: Path) -> None:
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.blobs = LocalBlobStore(self.home / "blobs")
        engine = create_engine(f"sqlite:///{self.home / 'metadata.db'}")
        metadata.create_all(engine)
        self.metadata = MetadataStore(engine)

    def ingest_path(self, path: Path, *, allow_corpus_path: bool = False) -> SourceArtifact:
        path = Path(path)
        if not allow_corpus_path and self._looks_like_corpus_source(path):
            raise DirectCorpusSourceError(
                "direct corpus source ingestion is blocked; use 'voxcodex corpus ingest' so HoldoutGuard runs before source I/O"
            )

        source_blob = self.blobs.import_file(path)
        source_id = f"source:{source_blob.sha256}"
        existing = self.metadata.get_artifact(source_id)
        if existing is not None:
            return self._load_model(existing, SourceArtifact)

        source = SourceArtifact(
            id=source_id,
            media_type=self._detect_media_type(path),
            original_filename=path.name,
            byte_size=source_blob.byte_size,
            checksum=source_blob.sha256,
            acquisition_kind="local_file",
            original_uri=path.resolve().as_uri(),
            created_at=datetime.now(UTC),
        )
        self._store_model(source.id, "source_artifact", source)
        return source

    def ingest_corpus_case(self, registry_path: Path, case_id: str) -> SourceArtifact:
        registry = CorpusRegistry.load(registry_path)
        guard = HoldoutGuard(registry.quarantined_case_ids)
        source_path = registry.resolve_primary_source_path(
            case_id,
            guard,
            operation="ingest_source_evidence",
        )
        return self.ingest_path(source_path, allow_corpus_path=True)

    def build_evidence(
        self,
        source_id: str,
        adapter_name: Literal["pdf", "markdown"],
        *,
        scope: str = "all",
        glyph_runs: bool = False,
    ) -> EvidenceSnapshot:
        source_ref = self._require_artifact(source_id, kind="source_artifact")
        source = self._load_model(source_ref, SourceArtifact)
        source_path = self.blobs.path_for(BlobRef(source.checksum, source.byte_size))

        if adapter_name == "pdf":
            adapter = PdfAdapter(blob_store=self.blobs)
            page_indexes = self._parse_pdf_scope(scope)
            options = {"glyph_runs": glyph_runs}
        elif adapter_name == "markdown":
            if scope != "all":
                raise ValueError("Markdown evidence currently supports only --scope all")
            adapter = MarkdownAdapter(blob_store=self.blobs)
            page_indexes = None
            options = {}
        else:
            raise ValueError(f"unsupported adapter: {adapter_name}")

        source_profile = adapter.inspect(source, source_path)
        self._store_model(source_profile.id, "source_profile", source_profile)

        profile_payload = {
            "adapter": adapter_name,
            "adapter_version": adapter.adapter_version,
            "options": options,
        }
        profile_digest = sha256_bytes(canonical_json_bytes(profile_payload))
        extraction_profile = ExtractionProfile(
            id=f"extraction-profile:{adapter_name}:{profile_digest}",
            adapter=adapter_name,
            adapter_version=adapter.adapter_version,
            options=options,
        )
        self._store_model(extraction_profile.id, "extraction_profile", extraction_profile)

        if adapter_name == "pdf":
            snapshot = adapter.extract(
                source,
                source_path,
                extraction_profile,
                page_indexes=page_indexes,
            )
        else:
            snapshot = adapter.extract(source, source_path, extraction_profile)

        for partition_ref in snapshot.partition_refs:
            self._register_existing_ref(partition_ref)
        self._store_model(snapshot.id, "evidence_snapshot", snapshot)
        return snapshot

    def show_snapshot(self, snapshot_id: str) -> EvidenceSnapshot:
        ref = self._require_artifact(snapshot_id, kind="evidence_snapshot")
        return self._load_model(ref, EvidenceSnapshot)

    def _store_model(self, artifact_id: str, kind: str, model: BaseModel) -> ArtifactRef:
        payload = canonical_json_bytes(model.model_dump(mode="json", exclude_none=True))
        blob = self.blobs.put_bytes(payload)
        ref = ArtifactRef(id=artifact_id, digest=blob.sha256, kind=kind)
        existing = self.metadata.get_artifact(artifact_id)
        if existing is None:
            self.metadata.register_artifact(ref)
        elif existing != ref:
            raise ArtifactConflictError(
                f"immutable artifact conflict for {artifact_id}: {existing.digest} != {ref.digest}"
            )
        return ref

    def _register_existing_ref(self, ref: ArtifactRef) -> None:
        existing = self.metadata.get_artifact(ref.id)
        if existing is None:
            self.metadata.register_artifact(ref)
        elif existing != ref:
            raise ArtifactConflictError(
                f"immutable artifact conflict for {ref.id}: {existing.digest} != {ref.digest}"
            )

    def _require_artifact(self, artifact_id: str, *, kind: str) -> ArtifactRef:
        ref = self.metadata.get_artifact(artifact_id)
        if ref is None:
            raise UnknownArtifactError(artifact_id)
        if ref.kind != kind:
            raise TypeError(f"artifact {artifact_id} has kind {ref.kind!r}, expected {kind!r}")
        return ref

    def _load_model(self, ref: ArtifactRef, model_type: type[BaseModel]):
        data = self.blobs.read_digest(ref.digest)
        return model_type.model_validate_json(data)

    @staticmethod
    def _parse_pdf_scope(scope: str) -> tuple[int, ...] | None:
        if scope == "all":
            return None
        try:
            indexes = tuple(int(value.strip()) for value in scope.split(",") if value.strip())
        except ValueError as exc:
            raise ValueError("PDF --scope must be 'all' or comma-separated zero-based page indexes") from exc
        if not indexes or any(index < 0 for index in indexes):
            raise ValueError("PDF --scope must contain non-negative zero-based page indexes")
        return indexes

    @staticmethod
    def _detect_media_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "application/pdf"
        if suffix in {".md", ".markdown"}:
            return "text/markdown"
        guessed, _ = mimetypes.guess_type(path.name)
        return guessed or "application/octet-stream"

    @staticmethod
    def _looks_like_corpus_source(path: Path) -> bool:
        parts = [part.casefold() for part in path.parts]
        for index in range(len(parts) - 3):
            if (
                parts[index] == "corpus"
                and parts[index + 1] == "compatibility"
                and parts[index + 2].startswith("cc-")
                and parts[index + 3] == "source"
            ):
                return True
        return False
