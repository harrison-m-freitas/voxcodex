# M2 Holdout Executor Gate

Status: **READY FOR CANDIDATE V2 FREEZE**

Date: 2026-09-17

## Scope closed before reveal

The production M2 execution surface now composes:

`Frozen scope → Source identity → Evidence → Reconstruction → CBM v0.1 materialization → ValidationPolicy:m2-poc-strict:v1 → frozen CanonicalRevision / explicit failure classification`.

Implemented pre-reveal controls include:

- candidate V2 semantic implementation-tree binding;
- frozen holdout scope parsing;
- candidate/reveal/freeze preflight before source I/O;
- production reconstruction stage driven by frozen config;
- end-to-end `M2PipelineProcessor`;
- exact PDF page and Markdown ZIP member execution;
- auditable result classes: `PASS`, `PROCESSING_FAILURE`, `MODEL_GAP`, `MODEL_FAILURE`;
- immutable schema-evolution observation for model gaps/failures;
- `voxcodex corpus run-holdouts` with all preflights completed before processor construction;
- exclusive-create blind run report;
- synthetic PDF, Markdown and Markdown-ZIP end-to-end coverage.

## Candidate history

Historical candidate V1 remains unchanged:

- file: `M2-IMPLEMENTATION-CANDIDATE-V1.json`
- id: `m2-implementation-candidate-v1`
- digest: `666271411488ab2563263efda93a8aa5d182396098eac92e8a356aa69dbfacf9`
- state: **SUPERSEDED PRE-REVEAL / IMMUTABLE HISTORICAL EVIDENCE**

V1 was never used to reveal or execute the four M2 blind holdouts.

Replacement target:

- file: `M2-IMPLEMENTATION-CANDIDATE-V2.json`
- id: `m2-implementation-candidate-v2`
- state: **NOT YET FROZEN**
- implementation SHA: to be taken from the next full-green CI commit containing this gate and the V2 pre-freeze report.

## CI evidence

Green workflow runs used by `planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json`:

- candidate V2 identity: `35287071862`
- holdout preflight: `35287239312`
- production reconstruction: `35287477664`
- M2 pipeline processor: `35287924432`
- blind runner CLI: `35288130043`
- full expanded pre-freeze gate: `35288230172`

The expanded gate passed Plan 01, Evidence, CLI, quarantine, Reconstruction, CBM, Materialization/Validation, canonical trace, Execution, Corpus/candidate and historical V1 verification.

The local-corpus waiver remains narrow: physical compatibility SourceArtifacts not mounted in GitHub Actions are not counted as physical-conformance PASS.

## Blind protocol integrity

The following real SourceArtifacts remain **FROZEN / UNREVEALED / untouched**:

- `CC-05`
- `CC-07`
- `CC-14`
- `CC-18`

During executor implementation:

- no real holdout `source/` path was resolved by the implementation flow;
- no real holdout was opened, unpacked, parsed, rendered, summarized or semantically inspected;
- no real holdout SourceArtifact was re-hashed;
- no `M2-HOLDOUT-REVEAL-V1.json` was created;
- `REVEAL_M2_HOLDOUTS_V1` was not executed against the real manifests.

All pre-reveal executor tests used synthetic fixtures plus already-public frozen selection metadata.

## Remaining pre-reveal steps

1. Run the complete CI on the exact commit containing this gate and the V2 pre-freeze report.
2. Record that green commit SHA as the V2 implementation SHA.
3. Generate `M2-IMPLEMENTATION-CANDIDATE-V2.json` reproducibly from that exact SHA.
4. Commit the exact generated candidate bytes.
5. Convert CI to mandatory V2 verify-only mode with no V1 fallback.
6. Run the final pre-reveal CI.

Only after those steps is the repository allowed to reach the irreversible action:

`REVEAL_M2_HOLDOUTS_V1`

No reveal is authorized by this document.
