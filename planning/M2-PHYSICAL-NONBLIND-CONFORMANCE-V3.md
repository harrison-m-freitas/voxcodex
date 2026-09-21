# M2 Physical Non-Blind Conformance — Candidate V3 Prefreeze

Status: **PASS — ALL KNOWN NON-BLIND TIER 1**

The five and only five known non-blind Tier 1 SourceArtifacts in Compatibility Corpus v1 were executed end-to-end against the final V3 semantic implementation tree `3c5f6eac26c855579b27adc354fa31aeb21b278e3af0567189a59ebeaedcdb0f`.

Execution used Python **3.14.7** and the frozen dependency environment from the green V3 CI runtime. The final Candidate V3 freeze-control source was overlaid byte-for-byte from Git blob `1fa43b0ddb7d712d13072900d17ccd84810a1ec6`; processing-pipeline sources were unchanged. CI run `35607282725` is green for the same semantic tree.

All physical files matched their frozen SHA-256 and byte-size identities before processing. Every case passed `m2_poc_strict`, with zero significant suspected loss.

| Case | Physical scope | Result |
|---|---:|---|
| CC-04 — Os Lusíadas | full PDF, 628 pages | PASS |
| CC-12 — Histories, Vol. 1 | full PDF, 770 pages | PASS |
| CC-19 — CommonMark Specification source | full source text | PASS |
| CC-22 — Euclid — First Six Books | full PDF, 228 pages | PASS |
| CC-25 — NASA Systems Engineering Handbook | full PDF, 297 pages | PASS |

The remaining Tier 1 cases are exactly the four blind holdouts: `CC-05`, `CC-07`, `CC-14`, and `CC-18`. They remain **FROZEN / UNREVEALED** and no holdout bytes were opened, resolved, hashed, parsed, rendered, or processed.

The physical runs used a deterministic prefreeze provenance binding because the final Candidate V3 digest does not exist until freeze. This does not relax or bypass the strict validation result; final candidate-bound provenance can be re-executed after freeze without tuning.
