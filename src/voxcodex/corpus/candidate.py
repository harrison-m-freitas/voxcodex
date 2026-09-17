from __future__ import annotations

import json
from pathlib import Path

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.common import ArtifactRef, FrozenModel


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
