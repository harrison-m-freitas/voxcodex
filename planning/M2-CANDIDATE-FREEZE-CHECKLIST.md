# M2 Candidate Freeze Checklist

Status: **READY_FOR_CANDIDATE_FREEZE**

Branch: `m2-plan06-corpus-candidate-freeze`

This checklist records the preconditions for freezing `M2-IMPLEMENTATION-CANDIDATE-V1`. It does not authorize or perform a blind-holdout reveal.

## Frozen authorities

- Compatibility corpus freeze manifest: `COMPATIBILITY-CORPUS-V1-FREEZE-MANIFEST.json`.
- Holdout freeze manifest: `M2-HOLDOUT-V1-FREEZE-MANIFEST.json`.
- Regression assertion manifest: `corpus/manifests/M2-REGRESSION-ASSERTIONS-V1.json`.
- Regression assertion manifest SHA-256: `60cadbb29497e07c7c9a622337fd4c19df0afd7822948b43c442d3312e8ede9c`.
- Validation policy to bind: `m2_poc_strict()` / `validation-policy:m2-poc-strict:v1`.
- Blind holdouts: `CC-05`, `CC-07`, `CC-14`, `CC-18` — **FROZEN / UNREVEALED / untouched**.

The Plan 06 prose contains one stale reference to three quarantined cases. The frozen registry, holdout manifest, architecture contract and executable quarantine gate all establish **four** holdouts; those frozen authorities control.

## Gate evidence

| Gate | Result | CI evidence |
| --- | --- | --- |
| Plan 05 reprocessing/provenance | `PASS_WITH_LOCAL_CORPUS_WAIVER` | `35280023568` |
| Frozen assertions, 42/42 semantic expectations | `PASS` | `35281317506` |
| 26 non-holdout support classifications | `PASS_WITH_LOCAL_CORPUS_WAIVER` | `35281736953` |
| Cross-format canonical signature contract | `PASS` | `35281946772` |
| Candidate readiness contract | `PASS` | `35282082200` |
| Candidate freeze CLI + full workflow | `PASS` | `35282483313` |

The local-corpus waiver is narrow: registered physical SourceArtifacts outside the repository are not mounted in public CI. A skipped physical-source check is never counted as physical-conformance PASS.

## Frozen capability claims

The candidate may claim only the following pre-holdout capabilities:

1. Tier 1 PDF and Markdown evidence/reconstruction/materialization execution contracts.
2. Forty-two frozen M2 regression semantic assertions execute through explicit operators with auditable PASS/FAIL diagnostics.
3. Selective reprocessing preserves provenance-safe dependency reuse and invalidation.
4. Supported-format canonical structural comparison ignores operational IDs and source locators while retaining source-significant structure/surface/topology.

The candidate does **not** claim blind-holdout conformance, general HTML/EPUB/DOCX support, physical conformance for corpus SourceArtifacts absent from CI, or cross-format equivalence when one member is outside the supported tier.

## Freeze contents

`M2-IMPLEMENTATION-CANDIDATE-V1.json` must bind, at minimum:

- implementation Git commit SHA;
- `uv.lock` SHA-256;
- Python and uv versions;
- processor versions;
- semantic execution-config digests;
- strict ValidationPolicy digest;
- frozen regression assertion manifest digest;
- compatibility-corpus freeze digest;
- holdout freeze digest;
- pre-freeze regression report digest;
- explicit capability claims;
- known non-holdout classifications;
- the four withheld holdout IDs.

The freeze command is:

```bash
uv run voxcodex candidate freeze \
  --repo-root . \
  --regression-report planning/M2-PREFREEZE-REGRESSION-REPORT.json \
  --git-commit-sha "$GITHUB_SHA" \
  --output M2-IMPLEMENTATION-CANDIDATE-V1.json
```

## Holdout integrity before freeze

- No holdout SourceArtifact has been opened, unpacked, parsed, re-hashed, or used for tuning during Plans 01–06 to this point.
- Candidate construction reads only frozen registry/manifests, code/configuration and regression evidence.
- Production reveal remains unauthorized.
- The exact one-way reveal acknowledgement has not been recorded.
- Any future reveal must occur only after the candidate manifest is committed and the dedicated reveal-control contract is green.
