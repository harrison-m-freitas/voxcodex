from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voxcodex.corpus.candidate import (
    load_frozen_candidate,
    verify_repository_candidate,
)
from voxcodex.digests import sha256_bytes
from voxcodex.domain.common import FrozenModel


class HoldoutPreflightError(ValueError):
    """Raised before any holdout SourceArtifact is allowed to resolve."""


class HoldoutExecutionSpec(FrozenModel):
    holdout_id: str
    corpus_case_id: str
    support_tier: str
    format: str
    source_relative_path: str
    source_sha256: str
    source_byte_size: int
    candidate_digest: str
    holdout_freeze_digest: str
    selected_page_indexes: tuple[int, ...] = ()
    zip_member_path: str | None = None
    zip_member_sha256: str | None = None
    zip_member_byte_size: int | None = None


class HoldoutRevealRecord(FrozenModel):
    candidate_digest: str
    holdout_manifest_digest: str
    revealed_at: str
    actor: str
    context: str
    reveal_version: str


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise HoldoutPreflightError(f"{label} is missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HoldoutPreflightError(f"{label} is unreadable: {path}") from exc
    if not isinstance(data, dict):
        raise HoldoutPreflightError(f"{label} must be a JSON object")
    return data


def load_holdout_execution_specs(
    selection_manifest_path: Path,
    *,
    candidate_digest: str,
    holdout_freeze_digest: str,
) -> tuple[HoldoutExecutionSpec, ...]:
    manifest = _load_object(selection_manifest_path, label="selection manifest")
    if manifest.get("status") != "FROZEN_UNREVEALED":
        raise HoldoutPreflightError(
            "selection manifest must remain FROZEN_UNREVEALED before blind execution"
        )

    specs: list[HoldoutExecutionSpec] = []
    for entry in manifest.get("holdouts", ()):
        if not isinstance(entry, dict):
            raise HoldoutPreflightError("selection manifest contains a non-object holdout")
        source = entry.get("source_artifact")
        selection = entry.get("selection")
        if not isinstance(source, dict) or not isinstance(selection, dict):
            raise HoldoutPreflightError("holdout selection is missing source/scope metadata")
        selected_scope = selection.get("selected_scope")
        if not isinstance(selected_scope, dict):
            raise HoldoutPreflightError("holdout selection is missing selected_scope")

        pages = selected_scope.get("physical_pdf_pages_1_based")
        selected_page_indexes: tuple[int, ...] = ()
        zip_member_path: str | None = None
        zip_member_sha256: str | None = None
        zip_member_byte_size: int | None = None

        if pages is not None:
            if (
                not isinstance(pages, list)
                or not pages
                or any(not isinstance(page, int) or page < 1 for page in pages)
            ):
                raise HoldoutPreflightError(
                    "PDF selected scope must contain positive 1-based physical pages"
                )
            selected_page_indexes = tuple(page - 1 for page in pages)
        elif selected_scope.get("zip_member_path") is not None:
            zip_member_path = str(selected_scope["zip_member_path"])
            raw_member_digest = selected_scope.get("member_sha256")
            raw_member_size = selected_scope.get("member_byte_size")
            if (
                not zip_member_path
                or not isinstance(raw_member_digest, str)
                or not raw_member_digest
                or not isinstance(raw_member_size, int)
                or raw_member_size < 0
            ):
                raise HoldoutPreflightError(
                    "Markdown ZIP selected scope must bind member path, digest, and byte size"
                )
            zip_member_sha256 = raw_member_digest
            zip_member_byte_size = raw_member_size
        else:
            raise HoldoutPreflightError(
                "holdout selected scope must be frozen PDF pages or one Markdown ZIP member"
            )

        try:
            source_byte_size = int(source["byte_size"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HoldoutPreflightError("holdout source byte_size is invalid") from exc

        specs.append(
            HoldoutExecutionSpec(
                holdout_id=str(entry.get("holdout_id", "")),
                corpus_case_id=str(entry.get("corpus_case_id", "")),
                support_tier=str(entry.get("support_tier", "")),
                format=str(entry.get("format", "")),
                source_relative_path=str(source.get("relative_path", "")),
                source_sha256=str(source.get("sha256", "")),
                source_byte_size=source_byte_size,
                candidate_digest=candidate_digest,
                holdout_freeze_digest=holdout_freeze_digest,
                selected_page_indexes=selected_page_indexes,
                zip_member_path=zip_member_path,
                zip_member_sha256=zip_member_sha256,
                zip_member_byte_size=zip_member_byte_size,
            )
        )

    if not specs:
        raise HoldoutPreflightError("selection manifest has no frozen holdouts")
    if any(
        not spec.holdout_id
        or not spec.corpus_case_id
        or not spec.source_relative_path
        or not spec.source_sha256
        for spec in specs
    ):
        raise HoldoutPreflightError("selection manifest contains incomplete holdout identity")

    return tuple(specs)


def verify_holdout_preflight(
    *,
    repo_root: Path,
    candidate_path: Path,
    regression_report_path: Path,
    selection_manifest_path: Path,
    holdout_freeze_manifest_path: Path,
    reveal_record_path: Path,
    corpus_case_id: str,
) -> HoldoutExecutionSpec:
    frozen_candidate, candidate_digest = load_frozen_candidate(candidate_path)

    # This verification is deliberately before any source path resolution.
    verify_repository_candidate(
        repo_root=repo_root,
        candidate_path=candidate_path,
        regression_report_path=regression_report_path,
    )

    if not holdout_freeze_manifest_path.is_file():
        raise HoldoutPreflightError(
            f"holdout freeze manifest is missing: {holdout_freeze_manifest_path}"
        )
    holdout_bytes = holdout_freeze_manifest_path.read_bytes()
    holdout_digest = sha256_bytes(holdout_bytes)
    if holdout_digest != frozen_candidate.holdout_freeze_manifest_digest:
        raise HoldoutPreflightError(
            "holdout manifest digest does not match frozen candidate binding"
        )

    try:
        freeze_manifest = json.loads(holdout_bytes)
    except json.JSONDecodeError as exc:
        raise HoldoutPreflightError("holdout freeze manifest is invalid JSON") from exc
    if not isinstance(freeze_manifest, dict):
        raise HoldoutPreflightError("holdout freeze manifest must be a JSON object")
    if freeze_manifest.get("status") != "FROZEN_UNREVEALED":
        raise HoldoutPreflightError(
            "holdout freeze manifest must remain FROZEN_UNREVEALED"
        )

    if not selection_manifest_path.is_file():
        raise HoldoutPreflightError(
            f"selection manifest is missing: {selection_manifest_path}"
        )
    selection_digest = sha256_bytes(selection_manifest_path.read_bytes())
    expected_selection_digest = freeze_manifest.get(
        "holdout_selection_manifest_sha256"
    )
    if selection_digest != expected_selection_digest:
        raise HoldoutPreflightError(
            "selection manifest digest does not match holdout freeze manifest"
        )

    if not reveal_record_path.is_file():
        raise HoldoutPreflightError(
            f"reveal record is missing; blind source access remains blocked: {reveal_record_path}"
        )
    try:
        reveal = HoldoutRevealRecord.model_validate_json(
            reveal_record_path.read_bytes()
        )
    except ValueError as exc:
        raise HoldoutPreflightError("reveal record is invalid") from exc

    if reveal.reveal_version != "M2_HOLDOUTS_V1":
        raise HoldoutPreflightError(
            f"reveal version mismatch: {reveal.reveal_version}"
        )
    if reveal.candidate_digest != candidate_digest:
        raise HoldoutPreflightError(
            "reveal candidate digest does not match frozen candidate"
        )
    if reveal.holdout_manifest_digest != holdout_digest:
        raise HoldoutPreflightError(
            "reveal holdout digest does not match frozen holdout manifest"
        )

    specs = load_holdout_execution_specs(
        selection_manifest_path,
        candidate_digest=candidate_digest,
        holdout_freeze_digest=holdout_digest,
    )
    spec_by_case = {spec.corpus_case_id: spec for spec in specs}

    candidate_cases = set(frozen_candidate.holdouts_withheld)
    selected_cases = set(spec_by_case)
    if candidate_cases != selected_cases:
        raise HoldoutPreflightError(
            "selection holdout set does not match candidate holdouts_withheld"
        )

    spec = spec_by_case.get(corpus_case_id)
    if spec is None:
        raise HoldoutPreflightError(
            f"unknown frozen holdout corpus case: {corpus_case_id}"
        )
    return spec
