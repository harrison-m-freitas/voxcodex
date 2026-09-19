# M2 Holdout Executor Gate

Status: **CANDIDATE V2 FROZEN / VERIFIED / READY FOR PHYSICAL NON-BLIND VALIDATION**

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

Replacement candidate V2 is frozen:

- file: `M2-IMPLEMENTATION-CANDIDATE-V2.json`
- id: `m2-implementation-candidate-v2`
- candidate digest: `9c89f18b3c680a5d726adba9a4529f3326653f115543a57e207bd0d221ba3c0e`
- implementation SHA: `2b7daad66713da004bb3cb7c3fabf39f5fd755b5`
- implementation-tree digest: `6c71e4cebf9232de50ef97aa260da83b3d516d880b1a421d72f25453cf216ea3`
- candidate-file commit: `93f921c24d469c23dbb8b9966b656be503d52547`
- verify-only workflow commit: `124fc56e2e994c6c78caf8c95a49f179a59342f0`
- final verify-only workflow run: `35288497263`
- state: **FROZEN / VERIFIED**

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

Candidate V2 freeze and verify-only CI are complete.

Before spending the blind holdouts, the preferred remaining reversible step is physical execution of the known Tier 1 non-holdout SourceArtifacts from the local corpus mount:

- `CC-04`
- `CC-12`
- `CC-19`
- `CC-22`
- `CC-25`

These physical SourceArtifacts are intentionally not stored in GitHub. Their results should either close or narrow the existing local-corpus waiver. A failure here must be resolved with a new candidate **before** any blind reveal.

After that reversible validation, the repository is allowed to reach the irreversible action:

`REVEAL_M2_HOLDOUTS_V1`

No reveal is authorized by this document.


## Repository physical-source availability check

At verify-only head `124fc56e2e994c6c78caf8c95a49f179a59342f0`, GitHub contains no tracked `source/` files for the known Tier 1 non-holdout cases `CC-04`, `CC-12`, `CC-19`, `CC-22`, or `CC-25`.

Therefore physical non-blind validation must run against the separately acquired local corpus bundle; this absence is the reason the GitHub CI retains the local-corpus waiver and is not interpreted as a physical PASS.
