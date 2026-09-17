# M2 Reconstruction Implementation Gate

Date: 2026-09-16 (America/Sao_Paulo)  
Branch: `m2-plan03-reconstruction`  
Implementation candidate before this report: `bd16f5a0321c1b67ed275d907e661ae911469131`  
CI run: `35168826729`  
Toolchain: CPython 3.14.7, uv 0.12.13

## Gate status

`PASS_WITH_LOCAL_CORPUS_WAIVER`

The executable M2.3 Reconstruction implementation gate is green and no silent-loss failure was observed. Historical regression checks that require the known local corpus remain unexecuted in GitHub Actions because `/data` / `VOXCODEX_KNOWN_CORPUS_DIR` is not present. These skips are not converted into PASS and are retained below as explicit verification gaps.

This status does not reveal, process, unpack, read, or hash any M2 blind holdout SourceArtifact. CC05, CC07, CC14, and CC18 remain `FROZEN_UNREVEALED`.

## Fresh gate evidence

| Gate | Result |
|---|---:|
| Plan 01/general regression gate | 58 passed, 0 failed |
| Evidence implementation gate | 13 passed, 0 failed, 4 skipped (known local corpus unavailable) |
| Evidence CLI integration | 4 passed, 0 failed |
| Quarantine before Reconstruction | 4 passed, 0 failed |
| Reconstruction implementation suite | 31 passed, 0 failed, 7 skipped (known local corpus unavailable) |
| Exact Task 8 command: `pytest tests/unit/reconstruction tests/integration/reconstruction tests/regression -v` | 28 passed, 0 failed, 11 skipped |
| Quarantine after Reconstruction gate | 4 passed, 0 failed |
| Corpus registry status | `total=30 acquired=30 quarantined=4` |

The exact Task 8 gate and the post-gate quarantine both completed successfully in CI run `35168826729`.

## Frozen Reconstruction invariants R01-R13

| Invariant | Implementation evidence | Status |
|---|---|---|
| R01 — Reconstruction never mutates EvidenceSnapshot | `test_engine_does_not_mutate_evidence_snapshot` | PASS |
| R02 — reconstructed units are justified by evidence or derivation | reconstruction contracts, stage derivations, snapshot evidence-accounting integration test | PASS |
| R03 — logical reading order is derived, not native-order assumption | `test_reading_order_uses_region_topology_before_native_interleaving` | PASS |
| R04 — processing boundaries do not create document boundaries | page/worker-chunk reconciliation tests | PASS |
| R05 — units can remain open through pages/chunks | `OpenStructuralState` paragraph/speech/note continuation tests | PASS |
| R06 — physical recurrence does not imply logical duplication | recurrent editorial collapse test | PASS |
| R07 — classification uses multiple signals; no style has universal meaning | bold-alone negative test, multi-signal heading/speaker tests, anti-overfit synthetic names | PASS |
| R08 — structured content preserves topology before linearization | table topology, terminal roles, formula visual region, figure asset-region tests | PASS |
| R09 — uncertainty remains explicit | unresolved-boundary issue, ambiguous-role assembly issue, unresolved reference behavior | PASS |
| R10 — interpretation failure does not authorize evidence loss | unmatched-boundary evidence retention, formula candidate without symbolic parse, assembly evidence accounting | PASS |
| R11 — ReconstructionSnapshot is immutable/versionable | frozen contracts plus content-addressed snapshot persistence and timestamp-independent semantic digest | PASS |
| R12 — genre is not a reconstruction router | feature-based speaker/heading classifiers and unseen synthetic inputs | PASS |
| R13 — `parent_ref + order_key` are normative hierarchy authority | reconstruction contract test and R7 assembly hierarchy/order assertions | PASS |

## Historical known-corpus verification gaps

The following tests are present and deliberately skip when the local known corpus is absent:

- F1 — Fedra evidence slice;
- F2 — Fedra cross-page continuation;
- F-RND — Fedra page beginning mid-speech;
- W1 — Weidman evidence slice, recurrent header, and terminal candidate;
- W2 — table candidate;
- C1 — evidence geometry and cross-page handoff;
- C3 — evidence math/visual assets and formula/figure candidates.

These are classified as `VERIFICATION_GAP_LOCAL_CORPUS`, not `PROCESSING_FAILURE`, because the processors were not run against those physical source files in this CI environment.

C2 and W-RND do not currently have dedicated physical-corpus regression tests in `tests/regression`. Their relevant behavior is exercised by synthetic Markdown/technical-structure tests, but physical-corpus confirmation remains `VERIFICATION_GAP_COVERAGE` for a later known-corpus run. This does not change M2.3 contracts or the frozen corpus.

## Processing failures

No `PROCESSING_FAILURE` was observed in the executable Task 8 gate.

No failure was hidden by editing CBM v0.1, weakening a frozen invariant, or hardcoding exact corpus text.

## Quarantine result

The post-gate quarantine suite passed 4/4. It verifies:

- frozen holdout IDs are blocked;
- registry metadata can be read without source access;
- corpus status reports four quarantined cases;
- quarantined source resolution fails before path I/O.

Therefore the M2 blind holdouts remain unrevealed and unavailable to Reconstruction development/tuning.

## Promotion boundary

M2.3 implementation is eligible to proceed to M2.4 under the existing local-corpus waiver. The waiver is a verification exception only: it does not turn skipped historical checks into PASS, does not expand capability claims, and does not relax the frozen holdout protocol.
