# M2 Implementation Reprocessing Gate

**Plan:** M2.5 — Reprocessing, Provenance, and Cost  
**Branch:** `m2-plan05-reprocessing-provenance`  
**Gate status:** `PASS_WITH_LOCAL_CORPUS_WAIVER`  
**Gate CI commit:** `d8a7dc0889b208a7072df778a28ee44a306e559b`  
**GitHub Actions run:** `35279879385`  
**Environment:** Python 3.14.7, uv 0.12.13

## Scope

This gate verifies semantic activity fingerprints, provenance-safe cache reuse, contextual dependency invalidation, immutable execution planning, dry-run/runner behavior, failure/retry taxonomy, operational telemetry, partial-output atomicity, usage/cost accounting, risk-based auditable human review, and the three mandatory selective-reprocessing scenarios from frozen M2.6.

It does not reveal or process any M2 blind holdout SourceArtifact.

## Task status

```text
Task 1 — ActivityFingerprint                          PASS
Task 2 — cache reuse + contextual invalidation       PASS
Task 3 — ExecutionPlan / dry-run / runner / CLI      PASS
Task 4 — failures / retries / telemetry / partials   PASS
Task 5 — UsageRecord + cost estimation               PASS
Task 6 — ReviewRisk + ReviewDecision                  PASS
Task 7 — selective reprocessing A/B/C                 PASS
```

## Task 6 — ReviewRisk and auditable ReviewDecision

TDD RED was established on commit:

```text
77d13212ced9b296dbbc84b2d547ab20b7edfd26
```

GitHub Actions run `35261284958` collected the new review contract and failed because `voxcodex.execution.review` did not yet exist. No unrelated failure was used as the RED condition.

The implementation entered on commit:

```text
8c43996aedb932df20016465f700e65c7df43d0d
```

GitHub Actions run `35279569771` completed successfully. The execution gate at that point reported:

```text
25 passed, 3 warnings
```

The review tests prove:

- confidence is not treated as inverse review risk;
- a high-confidence/high-impact table topology issue can outrank a low-confidence/decorative issue under policy;
- human correction creates a new immutable artifact;
- correction records a real `ProcessingActivity` with a `Derivation(kind="corrected")`;
- the prior artifact remains queryable;
- acceptance records human review without fabricating a new content artifact or falsely claiming that review produced the pre-existing content.

## Task 7 — mandatory selective reprocessing scenarios

The integration proof is implemented in:

```text
tests/integration/execution/test_selective_reprocessing.py
```

The final execution gate in GitHub Actions run `35279879385` reported:

```text
28 passed, 3 warnings
```

All three frozen M2.6 scenarios passed over persisted artifact/derivation DAGs.

### Scenario A — ValidationPolicy change only

A DAG containing Evidence → Reconstruction → CanonicalRevision plus versioned ValidationPolicy → ValidationReport is built in the metadata store.

Changing the prior ValidationPolicy context affects exactly:

```text
ValidationReport
```

Evidence, Reconstruction, and CanonicalRevision are reused. The existing revision remains immutable/queryable, consistent with the M2 rule that policy-only revalidation may produce a supplemental external validation report without rematerializing the revision or replacing a frozen revision's authorizing report.

Result:

```text
PASS
```

### Scenario B — local table reconstruction-profile change

The test builds independent table and paragraph branches. The table branch has a versioned reconstruction profile as a semantic input and both branches converge only at revision assembly.

Changing the table profile affects exactly:

```text
table ReconstructionUnit
materialized table
CanonicalRevision assembly
ValidationReport
```

The following remain reusable:

```text
table Evidence
paragraph Evidence
paragraph ReconstructionUnit
materialized paragraph
```

Result:

```text
PASS
```

### Scenario C — one region Evidence replacement

The test builds three regions. Regions A and B meet at an explicit reconciliation node; region C is independent.

Replacing region A invalidates exactly the downstream dependency closure:

```text
region A reconstruction
A/B reconciliation
A/B materialization
CanonicalRevision assembly
ValidationReport
```

It does not invalidate region B's own reconstruction merely because B participates in reconciliation, and it does not invalidate independent region C or its materialization. This demonstrates a bounded reconciliation radius rather than whole-document invalidation.

Result:

```text
PASS
```

## Provenance and cache invariants

The accepted implementation preserves the following Plan 05 invariants:

- a cache hit returns original output refs and does not fabricate a new producing activity/derivation;
- `voxcodex plan` is a dry-run and creates no provenance records;
- a planned activity becomes a real `ProcessingActivity` only when execution starts;
- semantic input/config/model/schema changes alter activity identity/fingerprint as required;
- incomplete pricing yields unknown monetary cost rather than a misleading partial subtotal;
- actual usage is attached to a real processing activity;
- staleness/invalidation is contextual metadata and does not mutate historical artifacts;
- human correction adds new lineage instead of rewriting prior history.

## Broader regression evidence

On gate candidate `d8a7dc0889b208a7072df778a28ee44a306e559b`, GitHub Actions run `35279879385` completed all workflow steps successfully.

Key results:

```text
Plan 01/unit/storage/corpus gate             107 passed, 3 warnings
Evidence implementation gate                 13 passed, 4 skipped
Evidence CLI integration                      12 passed
Quarantine                                     4 passed
Reconstruction implementation                 31 passed, 7 skipped
Broader reconstruction/regression             28 passed, 16 skipped
CBM contracts                                  8 passed
Materialization + validation                  21 passed
Canonical implementation gate                29 passed, 5 skipped
Canonical trace                                6 passed
Quarantine after canonical                     4 passed
Execution / reprocessing                      28 passed, 3 warnings
```

The known-corpus skips remain inherited local-corpus verification debt: the corresponding source files are intentionally absent from the public repository/CI workspace. They are not counted as physical conformance PASS.

## Blind holdout quarantine

Compatibility corpus metadata remained:

```text
total=30 acquired=30 quarantined=4
```

The frozen blind holdouts remain unrevealed:

- CC-05
- CC-07
- CC-14
- CC-18

No blind holdout SourceArtifact was opened, unpacked, parsed, used for assertions, or used for tuning during Plan 05 implementation or this gate.

## Decision

The selective-reprocessing subgate is:

```text
PASS
```

The complete `M2.5 Reprocessing, Provenance, and Cost` implementation is accepted as:

```text
PASS_WITH_LOCAL_CORPUS_WAIVER
```

The waiver is inherited solely from unavailable known local-corpus physical regressions; it does not weaken the three selective-reprocessing proofs, all of which are executable and passing in CI.

This closes Plan 05 while preserving the blind-holdout protocol and the existing obligation to run known-source physical regressions locally before any later claim that requires that conformance evidence.
