# M2 — Source Evidence Implementation Gate

**Date:** 2026-09-16  
**Milestone:** M2.2 — Source Artifact & Evidence Model  
**Implementation plan:** `docs/superpowers/plans/2026-09-14-m2-02-source-evidence.md`  
**Candidate branch:** `m2-plan02-source-evidence`  
**Last fully verified implementation commit before promotion record:** `47d2cef6763773b24aac5f1b47815b2a903de0a0`  
**GitHub Actions run:** `35121925701`  
**Job:** `104881560566`  
**Overall implementation status:** `PROMOTED_WITH_LOCAL_CORPUS_WAIVER`  
**Evidence conformance status:** `BLOCKED_LOCAL_CORPUS`

## Promotion decision

Plan 02 is administratively promoted to unblock Plan 03 by explicit project-owner instruction on 2026-09-16.

This promotion is a **waiver of the local-corpus completion prerequisite**, not a conversion of missing evidence into a PASS. The physical known-slice conformance remains open until F1/W1/C1/C3 execute locally against the fixed editions with zero skips and their digests are recorded here.

The distinction is normative for implementation tracking:

- implementation may proceed to M2.3 Reconstruction;
- Source Evidence CI behavior is verified;
- holdout quarantine remains mandatory;
- the M2.2 known-slice evidence-accountability gate is still incomplete;
- downstream final candidate/freeze may not treat this waiver as evidence that the four physical regressions passed.

## Reproducible environment

- Python: `3.14.7`
- uv: `0.12.13`
- PyMuPDF: `1.28.2`
- markdown-it-py: `4.2.0`
- pytest: `9.1.1`
- Hypothesis: `6.168.0`

The workflow installs from the committed `uv.lock` using `uv sync --frozen`.

## CI evidence

### Foundation / Plan 01 regression

Command set:

```bash
uv run alembic upgrade head
uv run pytest tests/unit tests/integration/storage tests/integration/corpus -v
uv run voxcodex corpus status --registry corpus/COMPATIBILITY-CORPUS-V1.json
```

Result from run `35121925701`:

```text
29 passed
total=30 acquired=30 quarantined=4
```

### M2 Source Evidence implementation gate

Normative command:

```bash
uv run pytest \
  tests/unit/domain/test_evidence_contracts.py \
  tests/unit/adapters \
  tests/integration/adapters \
  tests/regression/test_evidence_known_slices.py -v
```

CI result:

```text
13 passed, 4 skipped
```

The four skips are exactly the local known-slice checks:

- F1 — *Fedra*, PDF p.6;
- W1 — Weidman, PDF p.112;
- C1 — Leandro Lima, PDF pp.6–7 and 38–39;
- C3 — James Stewart, *Calculus*, PDF pp.83, 87, 139 and 145.

They skip only because `/data/` is intentionally absent from the published repository. `.gitignore` explicitly excludes `/data/` and `corpus/compatibility/*/source/`.

### CLI integration

Command:

```bash
uv run pytest tests/integration/cli -v
```

Result:

```text
4 passed
```

Covered behavior:

- `voxcodex ingest PATH` returns a stable source ID;
- repeated ingestion of identical bytes is idempotent;
- `voxcodex evidence build` supports Markdown and page-scoped PDF extraction;
- `voxcodex evidence show` reloads stored snapshots;
- direct ingestion from `corpus/compatibility/*/source/*` is rejected.

### Quarantine regression

Normative command:

```bash
uv run pytest tests/unit/corpus/test_quarantine.py tests/integration/corpus -v
```

Result:

```text
4 passed
```

The integration guard raises before source-path I/O for unrevealed M2 holdouts.

## Known-slice local completion command

Run from the repository root on the machine that holds the fixed non-published source corpus:

```bash
VOXCODEX_KNOWN_CORPUS_DIR="$PWD/data" \
uv run pytest tests/regression/test_evidence_known_slices.py -v -s
```

Required result for **full evidence conformance**:

```text
4 passed
0 skipped
```

The test harness emits one line per validated slice in this form:

```text
KNOWN_SLICE F1 snapshot_digest=<sha256> partition_digests=<sha256,...>
KNOWN_SLICE W1 snapshot_digest=<sha256> partition_digests=<sha256,...>
KNOWN_SLICE C1 snapshot_digest=<sha256> partition_digests=<sha256,...>
KNOWN_SLICE C3 snapshot_digest=<sha256> partition_digests=<sha256,...>
```

Those digests must be copied into the section below without copying source text or derived source content.

## Known-slice snapshot digests

Status: `PENDING_LOCAL_CORPUS`

| Slice | Snapshot digest | Partition digests | Result |
|---|---|---|---|
| F1 | pending | pending | pending local execution |
| W1 | pending | pending | pending local execution |
| C1 | pending | pending | pending local execution |
| C3 | pending | pending | pending local execution |

## Holdout safety

M2 blind holdouts remain `FROZEN_UNREVEALED`:

- `CC-05` / M2-H3;
- `CC-07` / M2-H1;
- `CC-14` / M2-H4;
- `CC-18` / M2-H2.

No holdout SourceArtifact was opened, unpacked, parsed, extracted or used for implementation tuning during this gate. Registry metadata may be read for quarantine enforcement only.

## Gate decision

Current decision: **PLAN 02 PROMOTED FOR IMPLEMENTATION CONTINUITY UNDER EXPLICIT WAIVER; EVIDENCE CONFORMANCE REMAINS OPEN.**

Completed and verified:

- immutable Evidence contracts;
- PDF/Markdown SourceProfile inspection;
- PDF per-page Evidence extraction;
- Markdown exact-range Evidence extraction;
- content-addressed evidence partitions and assets;
- deterministic snapshot identity by extraction profile;
- ingest/evidence CLI integration;
- quarantine-before-I/O behavior;
- known-slice regression harness.

Deferred evidence debt carried into later gates:

1. execute F1/W1/C1/C3 against the fixed local source corpus;
2. obtain `4 passed, 0 skipped`;
3. record snapshot and partition digests above;
4. rerun quarantine after recording the digests;
5. do not treat the administrative promotion as a substitute for these results during final candidate/freeze review.
