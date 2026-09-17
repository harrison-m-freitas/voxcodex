from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from voxcodex.digests import canonical_json_bytes, semantic_digest, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel
from voxcodex.validation.policies import m2_poc_strict


class CandidateReadinessError(ValueError):
    """Raised when an implementation candidate is not safe to freeze."""


class KnownClassification(FrozenModel):
    case_id: str
    support_tier: str
    result_class: str
    quarantined: bool
    diagnostic: str


class ImplementationCandidateManifest(FrozenModel):
    candidate_id: str
    git_commit_sha: str
    uv_lock_sha256: str
    python_version: str
    uv_version: str
    processor_versions: dict[str, str]
    semantic_config_digests: dict[str, str]
    validation_policy_digest: str
    regression_assertion_manifest_digest: str
    corpus_freeze_manifest_digest: str
    holdout_freeze_manifest_digest: str
    regression_report_digest: str
    capability_claims: tuple[str, ...]
    known_classifications: tuple[KnownClassification, ...]
    regression_status: str
    selective_reprocessing_status: str
    local_corpus_waiver: str | None = None
    holdouts_withheld: tuple[str, ...]


_REQUIRED_TEXT_FIELDS = (
    "candidate_id",
    "git_commit_sha",
    "uv_lock_sha256",
    "python_version",
    "uv_version",
    "validation_policy_digest",
    "regression_assertion_manifest_digest",
    "corpus_freeze_manifest_digest",
    "holdout_freeze_manifest_digest",
    "regression_report_digest",
)
_BLOCKING_TIER1_RESULTS = {"MODEL_GAP", "MODEL_FAILURE", "PROCESSING_FAILURE"}
_GREEN_REGRESSION = {"PASS", "PASS_WITH_LOCAL_CORPUS_WAIVER"}


def _assert_ready(manifest: ImplementationCandidateManifest) -> None:
    for field in _REQUIRED_TEXT_FIELDS:
        if not str(getattr(manifest, field)).strip():
            raise CandidateReadinessError(f"{field} must be bound before freeze")

    if not manifest.capability_claims:
        raise CandidateReadinessError("capability_claims must be explicit before freeze")
    if not manifest.processor_versions:
        raise CandidateReadinessError("processor_versions must be bound before freeze")
    if not manifest.semantic_config_digests:
        raise CandidateReadinessError("semantic_config_digests must be bound before freeze")
    if not manifest.holdouts_withheld:
        raise CandidateReadinessError("holdouts_withheld must remain explicit before freeze")

    if manifest.regression_status not in _GREEN_REGRESSION:
        raise CandidateReadinessError(
            f"regression_status must be green before freeze; got {manifest.regression_status}"
        )
    if (
        manifest.regression_status == "PASS_WITH_LOCAL_CORPUS_WAIVER"
        and not (manifest.local_corpus_waiver or "").strip()
    ):
        raise CandidateReadinessError(
            "local_corpus_waiver must describe the scope of a waived regression gate"
        )
    if manifest.selective_reprocessing_status != "PASS":
        raise CandidateReadinessError(
            "selective_reprocessing_status must be PASS before freeze"
        )

    for classification in manifest.known_classifications:
        if classification.quarantined:
            continue
        if classification.support_tier.casefold() != "tier 1":
            continue
        if classification.result_class in _BLOCKING_TIER1_RESULTS:
            raise CandidateReadinessError(
                f"blocking Tier 1 classification for {classification.case_id}: "
                f"{classification.result_class}"
            )


def candidate_digest(manifest: ImplementationCandidateManifest) -> str:
    payload = manifest.model_dump(mode="json", exclude_none=True)
    return sha256_bytes(canonical_json_bytes(payload))


def _file_digest(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return sha256_bytes(path.read_bytes())


def _stage_config_digest(stage: str, schema_versions: tuple[str, ...]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "stage": stage,
                "profile": "m2-default:0.1",
                "schema_versions": schema_versions,
            }
        )
    )


def _uv_version() -> str:
    try:
        completed = subprocess.run(
            ["uv", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    if completed.returncode != 0:
        return "unavailable"
    text = completed.stdout.strip()
    if not text:
        return "unavailable"
    parts = text.split()
    return parts[1] if len(parts) > 1 else text


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object in {path}")
    return data


def build_repository_candidate(
    *,
    repo_root: Path,
    git_commit_sha: str,
    regression_report_path: Path,
) -> ImplementationCandidateManifest:
    root = repo_root.resolve()
    report = _load_json(regression_report_path)
    registry = _load_json(root / "corpus" / "COMPATIBILITY-CORPUS-V1.json")

    holdouts = tuple(
        sorted(
            str(case_id)
            for case_id in registry.get("blind_holdouts", {}).get("reserved_case_ids", ())
        )
    )
    if set(holdouts) != {"CC-05", "CC-07", "CC-14", "CC-18"}:
        raise CandidateReadinessError(
            "holdouts_withheld must match the frozen M2 v1 set before candidate freeze"
        )

    regression_status = str(report.get("status", ""))
    classifications: list[KnownClassification] = []
    for entry in registry.get("cases", ()):
        if not isinstance(entry, dict):
            continue
        case_id = str(entry.get("corpus_case_id", ""))
        if not case_id or case_id in holdouts:
            continue
        support_tier = str(entry.get("support_tier", "Experimental"))
        manifestation = str(entry.get("acquired_manifestation_format", "unknown"))
        tier1_supported = support_tier.casefold() == "tier 1" and (
            "pdf" in manifestation.casefold() or "markdown" in manifestation.casefold()
        )
        if tier1_supported:
            result_class = regression_status
            diagnostic = (
                "covered by the pre-freeze non-holdout regression gate; physical "
                "SourceArtifact availability is governed by the report waiver scope"
            )
        else:
            result_class = "DEFERRED_BY_SUPPORT_TIER"
            diagnostic = (
                f"{support_tier} / {manifestation} is outside the frozen Tier 1 "
                "PDF/Markdown capability claim"
            )
        classifications.append(
            KnownClassification(
                case_id=case_id,
                support_tier=support_tier,
                result_class=result_class,
                quarantined=False,
                diagnostic=diagnostic,
            )
        )

    return ImplementationCandidateManifest(
        candidate_id="m2-implementation-candidate-v1",
        git_commit_sha=git_commit_sha,
        uv_lock_sha256=_file_digest(root / "uv.lock"),
        python_version=platform.python_version(),
        uv_version=_uv_version(),
        processor_versions={
            "source_evidence": "0.1.0",
            "reconstruction": "0.1.0",
            "cbm_materialization": "0.1.0",
            "frozen_assertion_runner": "1",
            "corpus_runner": "1",
            "canonical_equivalence": "1",
        },
        semantic_config_digests={
            "evidence": _stage_config_digest("evidence", ("evidence:0.1",)),
            "reconstruction": _stage_config_digest(
                "reconstruction",
                ("evidence:0.1", "reconstruction:0.1"),
            ),
            "materialization": _stage_config_digest(
                "materialization",
                ("reconstruction:0.1", "cbm:0.1"),
            ),
        },
        validation_policy_digest=semantic_digest(m2_poc_strict()),
        regression_assertion_manifest_digest=_file_digest(
            root / "corpus" / "manifests" / "M2-REGRESSION-ASSERTIONS-V1.json"
        ),
        corpus_freeze_manifest_digest=_file_digest(
            root / "COMPATIBILITY-CORPUS-V1-FREEZE-MANIFEST.json"
        ),
        holdout_freeze_manifest_digest=_file_digest(
            root / "M2-HOLDOUT-V1-FREEZE-MANIFEST.json"
        ),
        regression_report_digest=_file_digest(regression_report_path),
        capability_claims=(
            "Tier 1 PDF and Markdown evidence/reconstruction/materialization execution contracts",
            "42 frozen M2 regression semantic assertions execute through explicit operators",
            "selective reprocessing preserves provenance-safe dependency reuse and invalidation",
            "supported-format canonical structure comparison excludes operational IDs and source locators",
        ),
        known_classifications=tuple(classifications),
        regression_status=regression_status,
        selective_reprocessing_status=str(
            report.get("selective_reprocessing_status", "")
        ),
        local_corpus_waiver=(
            str(report["local_corpus_waiver"])
            if report.get("local_corpus_waiver") is not None
            else None
        ),
        holdouts_withheld=holdouts,
    )


def load_frozen_candidate(
    path: Path,
) -> tuple[ImplementationCandidateManifest, str]:
    if not path.is_file():
        raise CandidateReadinessError(f"frozen candidate manifest is missing: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateReadinessError(f"frozen candidate manifest is unreadable: {path}") from exc
    if not isinstance(data, dict):
        raise CandidateReadinessError("frozen candidate manifest must be a JSON object")

    frozen_digest = data.pop("candidate_digest", None)
    if not isinstance(frozen_digest, str) or not frozen_digest:
        raise CandidateReadinessError(
            "frozen candidate manifest is missing candidate_digest"
        )

    try:
        manifest = ImplementationCandidateManifest.model_validate(data)
    except ValueError as exc:
        raise CandidateReadinessError(
            "frozen candidate manifest does not satisfy the candidate contract"
        ) from exc

    _assert_ready(manifest)
    recomputed = candidate_digest(manifest)
    if recomputed != frozen_digest:
        raise CandidateReadinessError(
            "candidate digest mismatch: frozen candidate content has changed"
        )
    return manifest, frozen_digest


def verify_repository_candidate(
    *,
    repo_root: Path,
    candidate_path: Path,
    regression_report_path: Path,
) -> ArtifactRef:
    frozen, frozen_digest = load_frozen_candidate(candidate_path)
    current = build_repository_candidate(
        repo_root=repo_root,
        git_commit_sha=frozen.git_commit_sha,
        regression_report_path=regression_report_path,
    )
    _assert_ready(current)

    if current.model_dump(mode="json", exclude_none=True) != frozen.model_dump(
        mode="json", exclude_none=True
    ):
        raise CandidateReadinessError(
            "repository no longer matches frozen candidate"
        )
    if candidate_digest(current) != frozen_digest:
        raise CandidateReadinessError(
            "repository no longer matches frozen candidate digest"
        )

    return ArtifactRef(
        id=frozen.candidate_id,
        digest=frozen_digest,
        kind="implementation_candidate_manifest",
    )


def freeze_candidate(
    manifest: ImplementationCandidateManifest,
    *,
    output_path: Path | None = None,
) -> ArtifactRef:
    _assert_ready(manifest)
    digest = candidate_digest(manifest)
    artifact = ArtifactRef(
        id=manifest.candidate_id,
        digest=digest,
        kind="implementation_candidate_manifest",
    )

    if output_path is not None:
        payload = manifest.model_dump(mode="json", exclude_none=True)
        payload["candidate_digest"] = digest
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    return artifact
