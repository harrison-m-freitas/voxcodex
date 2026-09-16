# M2 — Source Evidence Implementation Gate

**Date:** 2026-09-16  
**Milestone:** M2.2 — Source Artifact & Evidence Model  
**Implementation plan:** `docs/superpowers/plans/2026-09-14-m2-02-source-evidence.md`  
**Candidate branch:** `m2-plan02-source-evidence`  
**Candidate commit verified in CI:** `d9a4dad70910524c9d77b98b24403718f3400b5e`  
**GitHub Actions run:** `35121795618`  
**Job:** `104881130283`  
**Overall gate status:** `BLOCKED_LOCAL_CORPUS`

## Gate interpretation

The implementation-level Source Evidence pipeline is green in the reproducible CI environment. The final known-slice physical-evidence conformance cannot be promoted to PASS in GitHub Actions because the fixed source PDFs are intentionally not published or versioned.

This is an environmental/data-availability boundary, not a relaxed assertion. The four known-slice regressions are implemented and collected, but they are skipped when the local source corpus is absent. Promotion of Plan 02 remains blocked until those four regressions execute against the fixed local editions with zero skips and their snapshot digests are recorded here.

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

Result:

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

The integration guard still raises before source-path I/O for unrevealed M2 holdouts.

## Known-slice local completion command

Run from the repository root on the machine that holds the fixed non-published source corpus:

```bash
VOXCODEX_KNOWN_CORPUS_DIR="$PWD/data" \
uv run pytest tests/regression/test_evidence_known_slices.py -v -s
```

Required result before promotion:

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

Current decision: **DO NOT PROMOTE PLAN 02 YET.**

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

Remaining blocking evidence:

1. execute F1/W1/C1/C3 against the fixed local source corpus;
2. obtain `4 passed, 0 skipped`;
3. record snapshot and partition digests above;
4. rerun the quarantine regression after recording the digests;
5. only then change this gate from `BLOCKED_LOCAL_CORPUS` to `PASS` and promote Plan 02.
