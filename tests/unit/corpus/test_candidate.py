from __future__ import annotations

import json
from pathlib import Path

import pytest

from voxcodex.corpus import candidate as candidate_module
from voxcodex.corpus.candidate import (
    CandidateReadinessError,
    ImplementationCandidateManifest,
    KnownClassification,
    freeze_candidate,
)


def _manifest(**overrides) -> ImplementationCandidateManifest:
    data = {
        "candidate_id": "m2-implementation-candidate-v1",
        "git_commit_sha": "a" * 40,
        "uv_lock_sha256": "b" * 64,
        "python_version": "3.14.7",
        "uv_version": "0.12.13",
        "processor_versions": {"pdf": "1", "markdown": "1", "reconstruction": "1", "materialization": "1"},
        "semantic_config_digests": {"reconstruction": "c" * 64, "materialization": "d" * 64},
        "validation_policy_digest": "e" * 64,
        "regression_assertion_manifest_digest": "f" * 64,
        "corpus_freeze_manifest_digest": "1" * 64,
        "holdout_freeze_manifest_digest": "2" * 64,
        "regression_report_digest": "3" * 64,
        "capability_claims": (
            "Tier 1 PDF and Markdown processing contracts",
            "selective reprocessing with provenance-safe reuse",
        ),
        "known_classifications": (
            KnownClassification(
                case_id="CC-04",
                support_tier="Tier 1",
                result_class="PASS",
                quarantined=False,
                diagnostic="known non-holdout contract passes",
            ),
            KnownClassification(
                case_id="CC-16",
                support_tier="Experimental",
                result_class="DEFERRED_BY_SUPPORT_TIER",
                quarantined=False,
                diagnostic="outside current claim",
            ),
        ),
        "regression_status": "PASS_WITH_LOCAL_CORPUS_WAIVER",
        "selective_reprocessing_status": "PASS",
        "local_corpus_waiver": "registered SourceArtifacts are not mounted in public CI",
        "holdouts_withheld": ("CC-05", "CC-07", "CC-14", "CC-18"),
    }
    data.update(overrides)
    return ImplementationCandidateManifest(**data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("capability_claims", ()),
        ("uv_lock_sha256", ""),
        ("validation_policy_digest", ""),
        ("regression_report_digest", ""),
    ],
)
def test_incomplete_candidate_cannot_freeze(field: str, value, tmp_path: Path) -> None:
    manifest = _manifest(**{field: value})

    with pytest.raises(CandidateReadinessError, match=field):
        freeze_candidate(manifest, output_path=tmp_path / "candidate.json")


def test_blocking_non_holdout_tier1_classification_prevents_freeze(tmp_path: Path) -> None:
    blocking = KnownClassification(
        case_id="CC-04",
        support_tier="Tier 1",
        result_class="MODEL_GAP",
        quarantined=False,
        diagnostic="source-significant structure not representable",
    )
    manifest = _manifest(known_classifications=(blocking,))

    with pytest.raises(CandidateReadinessError, match="CC-04"):
        freeze_candidate(manifest, output_path=tmp_path / "candidate.json")


def test_candidate_requires_green_regression_and_selective_reprocessing(tmp_path: Path) -> None:
    with pytest.raises(CandidateReadinessError, match="regression_status"):
        freeze_candidate(_manifest(regression_status="FAIL"), output_path=tmp_path / "a.json")

    with pytest.raises(CandidateReadinessError, match="selective_reprocessing_status"):
        freeze_candidate(_manifest(selective_reprocessing_status="FAIL"), output_path=tmp_path / "b.json")


def test_freeze_writes_deterministic_manifest_and_returns_artifact_ref(tmp_path: Path) -> None:
    output = tmp_path / "candidate.json"
    manifest = _manifest()

    artifact = freeze_candidate(manifest, output_path=output)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert artifact.id == "m2-implementation-candidate-v1"
    assert artifact.kind == "implementation_candidate_manifest"
    assert len(artifact.digest) == 64
    assert written["candidate_id"] == manifest.candidate_id
    assert written["holdouts_withheld"] == ["CC-05", "CC-07", "CC-14", "CC-18"]
    assert written["candidate_digest"] == artifact.digest



def test_load_frozen_candidate_rejects_tampered_manifest(tmp_path: Path) -> None:
    output = tmp_path / "candidate.json"
    freeze_candidate(_manifest(), output_path=output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["git_commit_sha"] = "9" * 40
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CandidateReadinessError, match="digest"):
        candidate_module.load_frozen_candidate(output)
