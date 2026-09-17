# M2 Implementation Canonical Gate

**Plan:** M2.4 — CBM Materialization and Validation  
**Branch:** `m2-plan04-cbm-materialization`  
**Gate status:** `PASS_WITH_LOCAL_CORPUS_WAIVER`  
**Gate CI commit:** `f7a74842f26b8e0af74b1e8a390e92b4b0e2fc63`  
**GitHub Actions run:** `35259087938`  
**Environment:** Python 3.14.7, uv 0.12.13

## Scope

This gate verifies the physical CBM v0.1 contracts, deterministic materialization, SourceAnchor/fidelity mapping, layered validation, revision freeze lifecycle, semantic digest idempotence, and upstream provenance tracing. It does not reveal or process any M2 blind holdout SourceArtifact.

## Canonical gate command

```bash
uv run pytest \
  tests/unit/cbm \
  tests/unit/materialization \
  tests/unit/validation \
  tests/integration/materialization \
  tests/regression/test_materialization_known_cases.py \
  -v
```

Result in GitHub Actions run `35259087938`:

```text
29 passed, 5 skipped
```

The five skips are the known-source materialization regressions whose source PDFs are intentionally excluded from the public repository and CI workspace:

- F1 — Fedra
- W2 — Weidman
- C1 — Leandro Lima
- C3 — Stewart Calculus
- W-RND — historical M1 Weidman regression

These skips are **not** counted as physical conformance PASS. They remain local-corpus verification debt under the same waiver policy already used by the Evidence and Reconstruction gates.

## Executable materialization/validation evidence

The dedicated CBM/materialization/validation suite completed with:

```text
21 passed
```

Covered behavior includes:

- cross-page objects materialize multiple physical SourceAnchors;
- inherited fidelity cannot be silently weakened;
- RoleProfile/Fidelity policy artifacts are versioned and deterministic;
- TablePayload preserves topology with non-owning content refs;
- FormulaPayload keeps source and reconstructed representations distinct;
- registry sharding is deterministic across Python insertion order;
- unmapped resolved roles emit explicit `MODEL_GAP` issues rather than disappearing;
- dangling refs, tree cycles, illegal role/node combinations, malformed tables, missing source accountability, fidelity weakening, and significant suspected loss block strict validation;
- passing validation + required manifests permits freeze;
- blocking validation prevents freeze;
- the authorizing validation report of a frozen revision cannot be replaced by supplemental revalidation;
- semantic revision digest is idempotent across activity IDs and timestamps.

## Physical CBM v0.1 contract evidence

The CBM contract suite completed with:

```text
8 passed
```

JSON Schema snapshots under `schemas/cbm/0.1/` are generated from the frozen Pydantic contracts and checked for deterministic equality.

## Provenance trace gate

Command surface:

```text
voxcodex trace OBJECT_ID
```

The trace integration gate invokes the CLI for six required canonical object kinds and requires each lineage to terminate upstream at an Evidence locator and SourceArtifact:

```text
paragraph         PASS
verse             PASS
terminal_command  PASS
table_cell        PASS
footnote          PASS
formula           PASS
```

Aggregate result:

```text
6 passed
```

The trace verifies explicit materialization/extraction Derivations and ProcessingActivities, Evidence locator fields including physical page information, and the terminal SourceArtifact checksum.

## Quarantine evidence

The quarantine suite was re-run **after** the canonical gate:

```bash
uv run pytest tests/unit/corpus/test_quarantine.py tests/integration/corpus -v
```

Result:

```text
4 passed
```

Compatibility corpus metadata remained:

```text
total=30 acquired=30 quarantined=4
```

M2 blind holdouts remain frozen and unrevealed:

- CC-05
- CC-07
- CC-14
- CC-18

No blind holdout SourceArtifact was opened, unpacked, hashed anew, parsed, or used for tuning during M2.4 implementation or this gate.

## Broader regression status

The broad Plan 01/unit/integration gate on the same candidate completed with:

```text
83 passed
```

The broader Reconstruction regression command continues to distinguish executable coverage from unavailable local corpus:

```text
28 passed, 16 skipped
```

Those skips are local known-corpus regressions inherited from prior Evidence/Reconstruction gates plus the five materialization known-source regressions; they are not presented as PASS.

## Decision

`M2.4 CBM Materialization and Validation` is accepted as:

```text
PASS_WITH_LOCAL_CORPUS_WAIVER
```

This authorizes progression to M2.5 Reprocessing / Provenance / Cost while preserving the obligation to run known-source materialization regressions locally before any later claim that requires their physical conformance evidence.
