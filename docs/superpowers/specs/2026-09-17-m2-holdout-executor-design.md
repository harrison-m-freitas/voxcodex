# M2 Holdout Executor — Design

**Date:** 2026-09-17  
**Status:** Proposed / pre-implementation  
**Branch:** `m2-plan06-corpus-candidate-freeze`

## 1. Context

The M2 blind protocol requires the implementation candidate to be frozen before any blind holdout is revealed. The current repository already freezes the M2 architecture, assertion manifest, holdout selection, support-tier claims, processor identities, semantic configuration, ValidationPolicy, pre-freeze regression evidence, and an implementation candidate.

The current candidate is:

- candidate id: `m2-implementation-candidate-v1`
- candidate digest: `666271411488ab2563263efda93a8aa5d182396098eac92e8a356aa69dbfacf9`
- implementation commit: `2b20be89d01aa1add802d3fff91d9e3d4fb43719`

The repository also has a tested one-way reveal gate and a CLI entrypoint requiring the exact acknowledgement `REVEAL_M2_HOLDOUTS_V1`.

However, the repository does not yet expose one production execution surface that composes the already-frozen M2 Evidence, Reconstruction, CBM Materialization, Validation, and corpus result classification layers end to end. Known regressions currently exercise the processors and reconstruction functions directly.

Revealing the holdouts before this composition exists would force semantically relevant execution wiring to be introduced after the freeze. That would weaken invariant C16 and make the blind result harder to interpret.

Therefore this design adds the execution composition **before reveal**, while all holdouts remain FROZEN / UNREVEALED.

## 2. Goal

Provide one auditable M2 holdout execution surface that:

1. accepts a frozen corpus case and frozen scope;
2. refuses access until the frozen candidate and reveal record have been validated;
3. runs only the already-approved M2 pipeline components;
4. executes the frozen holdout scope rather than an arbitrary whole-source probe;
5. emits an explicit corpus result class;
6. preserves failure evidence and diagnostics;
7. performs no tuning or capability downgrade after reveal.

The executor is composition, not a new semantic heuristic layer.

## 3. Non-goals

This work must not:

- inspect, extract, render, summarize, hash again, unpack, or otherwise access the four real holdout SourceArtifacts before explicit reveal;
- introduce rules specialized to CC-05, CC-07, CC-14, CC-18 or to the hidden contents of their selected scopes;
- alter CBM v0.1;
- change the frozen regression assertions;
- change the frozen holdout selection;
- downgrade Tier 1 claims to reinterpret a future failure;
- fabricate PASS from source availability or processor invocation alone;
- add support for deferred formats beyond the frozen M2 capability claim.

## 4. Architectural approach

Introduce a single orchestration component, conceptually `M2PipelineProcessor`.

It composes the existing layers in this order:

```text
Frozen CorpusCase + Frozen Scope
        ↓
preflight integrity checks
        ↓
SourceArtifact resolution
        ↓
Evidence extraction
        ↓
Document Reconstruction
        ↓
CBM materialization
        ↓
ValidationPolicy:m2-poc-strict:v1
        ↓
evidence-accountability / diagnostics
        ↓
Corpus result classification
```

No semantic decision is allowed merely because the executor is running a holdout. The executor must use the same profiles, processors, mappings, policies, and support-tier boundary frozen into the candidate.

## 5. Components

### 5.1 HoldoutExecutionSpec

An immutable runtime description derived from the already-frozen holdout selection manifest.

Minimum fields:

- holdout id;
- corpus case id;
- support tier;
- source format;
- selected scope;
- frozen source SHA-256;
- candidate digest;
- holdout freeze manifest digest.

For PDFs, the selected 1-based physical pages are converted mechanically to adapter page indexes.

For Markdown ZIP holdouts, the selected member path is taken verbatim from the frozen selection manifest. No additional member discovery is permitted after reveal beyond what is mechanically necessary to open the frozen member.

### 5.2 M2PipelineProcessor

A production processor that owns orchestration only.

Responsibilities:

- verify the input SourceArtifact matches the frozen source digest;
- select the correct frozen adapter path;
- build Evidence for the frozen scope;
- invoke reconstruction using the production reconstruction profile and stages;
- materialize the resulting reconstruction into CBM v0.1;
- run the frozen strict ValidationPolicy;
- assemble evidence-accountability data;
- classify the execution result.

The processor must not own corpus reveal policy. Reveal authorization remains a separate preflight concern.

### 5.3 HoldoutPreflight

The preflight runs before SourceArtifact resolution.

It must verify:

- the candidate manifest supplied to preflight is internally authentic; for the real blind run this must be `M2-IMPLEMENTATION-CANDIDATE-V2.json`;
- current repository bindings still match the frozen candidate;
- `M2-HOLDOUT-V1-FREEZE-MANIFEST.json` digest equals the candidate binding;
- a valid one-way `M2-HOLDOUT-REVEAL-V1.json` exists;
- the reveal record binds the same candidate digest and holdout freeze digest;
- the requested case is one of the four frozen holdouts;
- the requested scope exactly matches the frozen selection manifest.

If any check fails, source resolution is prohibited.

### 5.4 HoldoutRunReport

The executor writes an immutable machine-readable report for every holdout.

Minimum per-case data:

- candidate digest;
- holdout id;
- corpus case id;
- frozen selected scope;
- source digest verification result;
- processor/profile/version bindings;
- evidence snapshot ref/digest;
- reconstruction snapshot ref/digest;
- canonical revision ref/digest when produced;
- ValidationReport ref/result;
- evidence-accountability summary;
- final result class;
- diagnostic;
- schema-evolution observation when applicable.

The report must distinguish absence of a produced stage from a successful empty stage.

## 6. Result classification

The blind executor uses the already-approved result vocabulary.

### PASS

Allowed only when:

- the source matches the frozen identity;
- all required pipeline stages execute;
- no blocking reconstruction/materialization issue remains;
- strict validation passes;
- no significant evidence is silently lost;
- no unresolved condition contradicts the frozen Tier 1 claim.

### PASS_WITH_EXTENSION

Allowed only when the source is successfully represented by an already-permitted extension path that does not alter CBM v0.1 or weaken the frozen capability claim.

### PROCESSING_FAILURE

Used for execution failures where the model may still be adequate but the processor cannot complete the frozen scope.

Examples include adapter failure, corrupt intermediate generation, or runtime execution failure.

### MODEL_GAP

Used when source-significant structure cannot be represented under the frozen model/baseline.

It must create a schema-evolution observation and must not mutate CBM v0.1.

### MODEL_FAILURE

Used when the frozen model can represent the phenomenon but the frozen reconstruction/materialization behavior produces the wrong structure or interpretation.

### DEFERRED_BY_SUPPORT_TIER

Not valid as a post-reveal downgrade for the four frozen M2 holdouts, because the selected cases were frozen against the candidate's declared M2 support boundary. It remains valid only for ordinary compatibility-corpus execution outside the blind set.

## 7. CLI

Add:

```text
voxcodex corpus run-holdouts
```

Required inputs:

- frozen candidate path;
- frozen holdout selection manifest;
- frozen holdout freeze manifest;
- reveal record;
- corpus registry;
- output report path.

The CLI does **not** accept a capability override, support-tier override, alternative ValidationPolicy, processor override, or arbitrary scope.

The command must fail before source I/O if preflight integrity does not pass.

The CLI should support a synthetic-fixture root for tests, but production invocation over the repository must derive the actual paths from frozen manifests.

## 8. Blind protocol and candidate versioning

The current `M2-IMPLEMENTATION-CANDIDATE-V1.json` with digest `666271411488ab2563263efda93a8aa5d182396098eac92e8a356aa69dbfacf9` is preserved as a valid historical **pre-reveal superseded candidate**. It must not be deleted, renamed, or rewritten.

Because this executor adds semantically relevant production wiring before reveal, the repository will:

1. implement and regression-test the executor while holdouts remain unrevealed;
2. rerun the full M2 gates;
3. produce a new pre-freeze regression report if its bound implementation evidence changes;
4. freeze `M2-IMPLEMENTATION-CANDIDATE-V2.json` with candidate id `m2-implementation-candidate-v2` and a new digest;
5. update CI so the blind-run branch verifies V2 and never regenerates or substitutes V1;
6. require the one-way reveal acknowledgement against that candidate;
7. reveal and run the four holdouts without tuning.

No revealed result may be reassigned to the old candidate.

## 9. Real-holdout safety boundary

Until explicit reveal:

- tests use only synthetic PDF, Markdown, ZIP, registry, selection-manifest, candidate, and reveal-record fixtures;
- repository tests may read the public frozen selection metadata already committed;
- no test or implementation command may resolve any path under the four holdout `source/` directories;
- the one-way reveal command is not invoked against the real freeze manifest;
- no physical hash verification of the real SourceArtifacts is repeated.

After reveal, SourceArtifact access is allowed only through the preflight-validated executor.

## 10. Testing strategy

Implementation follows strict RED → GREEN TDD.

### Unit tests

Cover:

- frozen scope parsing for PDF;
- frozen member parsing for Markdown ZIP;
- preflight rejection without reveal;
- candidate/reveal digest mismatch;
- case/scope mismatch;
- result classification rules;
- source digest mismatch;
- schema-evolution observation on MODEL_GAP;
- no support-tier downgrade for a frozen blind case.

### Integration tests

Use only synthetic fixtures.

Cover:

- synthetic PDF through Evidence → Reconstruction → Materialization → Validation;
- synthetic Markdown through the same production orchestration path;
- synthetic Markdown ZIP selected-member extraction;
- failure before source I/O when reveal preflight is absent;
- successful audit report generation;
- deterministic rerun for identical source/configuration.

### Regression tests

Run the existing M2 regression suite unchanged.

The executor must not require changes to frozen assertion semantics to become green.

### Final pre-reveal gate

Before freezing the replacement candidate:

- Plan 01 gate green;
- Evidence gate green;
- Reconstruction gate green;
- CBM/materialization/validation gate green;
- provenance/trace gate green;
- selective-reprocessing gate green;
- 42 frozen assertions green;
- corpus support classification green;
- candidate verification green;
- holdout reveal-control tests green;
- executor synthetic integration tests green;
- no real holdout source access.

## 11. Error handling

Every stage failure must be explicit.

The executor must never:

- convert an exception into PASS;
- silently skip a selected page/member;
- infer a new support tier from observed holdout difficulty;
- continue with an unverified source digest;
- overwrite a prior blind-run report;
- modify a frozen manifest in place.

Where a failure prevents downstream stages, the report records which stages were not produced and why.

## 12. Auditability

The blind run must be reproducible from:

- candidate manifest;
- candidate digest;
- git commit bound by candidate;
- uv lock digest;
- processor versions;
- semantic config digests;
- ValidationPolicy digest;
- assertion manifest digest;
- holdout selection/freeze digests;
- reveal record;
- per-holdout run report.

The execution report is evidence of the blind evaluation, not a replacement for the frozen manifests.

## 13. Acceptance criteria

This design is complete when:

1. a production `M2PipelineProcessor` exists and is exercised by synthetic end-to-end tests;
2. `voxcodex corpus run-holdouts` cannot access a source before candidate/reveal preflight;
3. the four real holdouts remain untouched during implementation;
4. all existing regressions remain green without relaxing assertions;
5. `M2-IMPLEMENTATION-CANDIDATE-V2.json` is frozen before reveal while V1 remains unchanged as historical evidence;
6. CI verifies V2 rather than regenerating it or falling back to V1;
7. the repository is ready for a single explicit irreversible reveal followed immediately by blind execution without tuning.
