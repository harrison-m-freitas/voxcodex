# M2.3 Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert immutable EvidenceSnapshots into immutable ReconstructionSnapshots with logical reading order, block structure, cross-boundary reconciliation, structured candidates, localized confidence, and explicit issues.

**Architecture:** Implement R0–R7 as composable processors behind a reconstruction engine. Processors consume evidence/reconstruction artifacts and emit new immutable artifacts plus Derivations; no processor mutates evidence. The first implementation is deterministic/rule-based and genre-agnostic.

**Tech Stack:** Foundation stack; no LLM/OCR dependency.

**Spec:** `architecture/M2-DESIGN-V0.1.md` M2.3 (R01–R13).

## Global Constraints

- `parent_ref + order_key` is normative reconstruction hierarchy/order; `child_refs` is derived only.
- Chunk/page/worker boundaries never become document boundaries without source evidence.
- Uncertainty creates `ReconstructionIssue`; it never licenses dropping evidence.
- Rules may use typography/layout/textual patterns/context but cannot encode book-specific literal text as special cases.

---

### Task 1: Define Reconstruction contracts and deterministic stage protocol

**Files:**
- Create: `src/voxcodex/domain/reconstruction.py`
- Create: `src/voxcodex/reconstruction/engine.py`
- Test: `tests/unit/domain/test_reconstruction_contracts.py`
- Test: `tests/unit/reconstruction/test_engine.py`

**Interfaces:**
- Produces `ReconstructionUnit`, `ReconstructionSnapshot`, `OpenStructuralState`, `ReconstructionIssue`, `ReconstructionStage` protocol.
- `ReconstructionStage.run(context, units) -> StageResult`.

- [ ] **Step 1: Write failing authority/invariance tests**

Assert `child_refs` is absent or marked derived/non-normative, `parent_ref` exists, and snapshot/stage results are frozen.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/domain/test_reconstruction_contracts.py tests/unit/reconstruction/test_engine.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement contracts and stage orchestration**

Engine executes explicitly configured stages and records a ProcessingActivity + Derivation for every persisted stage output.

- [ ] **Step 4: Add no-evidence-mutation test**

Hash input EvidenceSnapshot before/after reconstruction and assert unchanged.

Run: `uv run pytest tests/unit/reconstruction/test_engine.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/domain/reconstruction.py src/voxcodex/reconstruction/engine.py tests/unit/domain/test_reconstruction_contracts.py tests/unit/reconstruction/test_engine.py
git commit -m "feat: define staged reconstruction engine"
```

### Task 2: Implement R0 normalization and R1 geometric grouping

**Files:**
- Create: `src/voxcodex/reconstruction/normalize.py`
- Create: `src/voxcodex/reconstruction/blocks.py`
- Test: `tests/unit/reconstruction/test_normalize_grouping.py`

**Interfaces:**
- Produces normalized comparison views without replacing source surface.
- Produces visual line/region candidates with evidence refs.

- [ ] **Step 1: Write failing ligature/dehyphenation-precondition/grouping tests**

Test that `ﬁ` can expose comparison view `fi` while source remains `ﬁ`; test spans on same baseline group into a visual line; distant spans do not.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/reconstruction/test_normalize_grouping.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement normalization views and geometry grouping**

Do not perform logical dehyphenation yet. Group using normalized baseline/overlap/gap thresholds supplied by versioned `ReconstructionProfile`.

- [ ] **Step 4: Add column synthetic fixture test**

Two visual columns must form distinct region candidates even when PDF native object order interleaves spans.

Run: `uv run pytest tests/unit/reconstruction/test_normalize_grouping.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/normalize.py src/voxcodex/reconstruction/blocks.py tests/unit/reconstruction/test_normalize_grouping.py
git commit -m "feat: add evidence normalization and geometric grouping"
```

### Task 3: Implement R2 reading order and R3 block reconstruction

**Files:**
- Create: `src/voxcodex/reconstruction/reading_order.py`
- Modify: `src/voxcodex/reconstruction/blocks.py`
- Test: `tests/unit/reconstruction/test_reading_order_blocks.py`

**Interfaces:**
- Produces deterministic `order_key` sequences inside parent regions.
- Produces paragraph/heading/monospace/auxiliary block candidates without final CBM role assignment.

- [ ] **Step 1: Write failing two-column reading-order test**

Construct evidence where native span order alternates left/right columns; expected reconstructed order is complete left column then complete right column.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/reconstruction/test_reading_order_blocks.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement hierarchical reading-order solver**

Use region topology first, then line y/x order within a region. Persist confidence basis and evidence refs for derived ordering.

- [ ] **Step 4: Implement block grouping + explicit layout dehyphenation derivation**

Only remove terminal hyphen when continuation evidence and lexical/layout rules satisfy profile policy. Preserve both source fragments and reconstructed text with derivation kind `reconstructed`.

Run: `uv run pytest tests/unit/reconstruction/test_reading_order_blocks.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/reading_order.py src/voxcodex/reconstruction/blocks.py tests/unit/reconstruction/test_reading_order_blocks.py
git commit -m "feat: reconstruct logical reading order and blocks"
```

### Task 4: Implement R4 classification without genre routing

**Files:**
- Create: `src/voxcodex/reconstruction/classifiers.py`
- Test: `tests/unit/reconstruction/test_classifiers.py`

**Interfaces:**
- Produces `RoleHypothesis(role, score, evidence_basis)` and optional `resolved_role` under policy.
- Initial deterministic classifiers cover heading, running header/folio, prose block, speaker cue shape, monospace technical block, footnote candidate, caption candidate.

- [ ] **Step 1: Write failing multi-signal tests**

Assert bold alone does not resolve `text.heading`; repeated same-position page text becomes running-header candidate; short uppercase line followed by verse-like lines may produce speaker-cue hypothesis without requiring drama genre metadata.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/reconstruction/test_classifiers.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement feature-based rule classifiers**

Features may include relative font size, weight, position, spacing, recurrence, neighboring block types, text shape, monospace pattern. Rules are versioned in `ReconstructionProfile`.

- [ ] **Step 4: Add anti-overfit tests**

Use synthetic names/headers unseen in corpus and assert rules classify by features rather than exact strings.

Run: `uv run pytest tests/unit/reconstruction/test_classifiers.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/classifiers.py tests/unit/reconstruction/test_classifiers.py
git commit -m "feat: add genre agnostic structural classifiers"
```

### Task 5: Implement R5 open-boundary reconciliation and recurrence

**Files:**
- Create: `src/voxcodex/reconstruction/boundaries.py`
- Test: `tests/unit/reconstruction/test_boundaries.py`
- Test: `tests/regression/test_cross_page_reconstruction.py`

**Interfaces:**
- Produces/consumes `OpenStructuralState` between processing partitions.
- Reconciles paragraph/speech/note continuations and repeated editorial material.

- [ ] **Step 1: Write failing partition-boundary tests**

Split a synthetic paragraph at a page boundary and at an arbitrary worker chunk boundary; both must reconstruct the same final logical block.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/reconstruction/test_boundaries.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement boundary state handoff and reconciliation**

Persist open units, pending continuations, unresolved boundaries; reconciliation emits new immutable reconstruction artifacts.

- [ ] **Step 4: Run known F2/F-RND/C1 regression checks without holdouts**

Use only historical M1 sources/slices that are already known; assert cross-page/open-state invariants and running-header non-duplication.

Run: `uv run pytest tests/regression/test_cross_page_reconstruction.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/boundaries.py tests/unit/reconstruction/test_boundaries.py tests/regression/test_cross_page_reconstruction.py
git commit -m "feat: reconcile cross boundary document state"
```

### Task 6: Implement R6 structured candidates

**Files:**
- Create: `src/voxcodex/reconstruction/structured.py`
- Test: `tests/unit/reconstruction/test_structured_candidates.py`
- Test: `tests/regression/test_structured_reconstruction.py`

**Interfaces:**
- Produces `TableCandidate`, `TechnicalBlockCandidate`, `TerminalCandidate`, `FormulaCandidate`, `FigureCandidate`, `FootnoteLinkCandidate` stored as reconstruction properties/payload refs.

- [ ] **Step 1: Write failing synthetic table/terminal/formula tests**

Table test asserts row/column topology; terminal test distinguishes prompt/input/output candidates from typography/position/patterns; formula test preserves visual region even when symbolic parse is absent; footnote test links marker to note body; reference test distinguishes detection from target resolution.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/reconstruction/test_structured_candidates.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement geometry-first table/figure/formula detection and technical-line grouping**

No LLM; symbolic formula reconstruction is optional and must not block FormulaCandidate creation.

- [ ] **Step 4: Run W1/W2/C3 known regression assertions applicable to reconstruction**

Run: `uv run pytest tests/regression/test_structured_reconstruction.py -v`
Expected: PASS or explicit `ReconstructionIssue` only where frozen assertion permits unresolved interpretation; never silent omission.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/structured.py tests/unit/reconstruction/test_structured_candidates.py tests/regression/test_structured_reconstruction.py
git commit -m "feat: reconstruct structured document candidates"
```

### Task 7: Implement R7 assembly, issues, and ReconstructionSnapshot persistence

**Files:**
- Modify: `src/voxcodex/reconstruction/engine.py`
- Create: `tests/integration/reconstruction/test_snapshot_assembly.py`

**Interfaces:**
- Produces immutable `ReconstructionSnapshot` whose root refs/hierarchy/order are sufficient for M2.4 without re-reading source bytes.

- [ ] **Step 1: Write failing end-to-end synthetic assembly test**

EvidenceSnapshot -> ReconstructionSnapshot must preserve all evidence accounting refs and emit issues for intentionally ambiguous block role.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/reconstruction/test_snapshot_assembly.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement final assembly and snapshot persistence**

Persist stage outputs and final snapshot as canonical artifacts; derive snapshot digest from semantic payload, not activity timestamps.

- [ ] **Step 4: Run reconstruction suite twice for idempotence**

Run the same fixtures twice with identical profile; expected semantic snapshot digests equal.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/reconstruction/engine.py tests/integration/reconstruction/test_snapshot_assembly.py
git commit -m "feat: assemble immutable reconstruction snapshots"
```

### Task 8: Reconstruction gate

**Files:**
- Create: `planning/M2-IMPLEMENTATION-RECONSTRUCTION-GATE.md`

**Interfaces:**
- Produces a gate report mapping frozen Reconstruction assertions to passing tests or explicit classified gaps.

- [ ] **Step 1: Run all reconstruction tests**

Run: `uv run pytest tests/unit/reconstruction tests/integration/reconstruction tests/regression -v`
Expected: zero silent-loss failures and no holdout access.

- [ ] **Step 2: Run quarantine suite again**

Expected: PASS.

- [ ] **Step 3: Record any remaining `PROCESSING_FAILURE` explicitly**

A remaining failure that the CBM can represent must be documented as `PROCESSING_FAILURE`; do not edit CBM v0.1 or hardcode corpus text.

- [ ] **Step 4: Commit**

```bash
git add planning/M2-IMPLEMENTATION-RECONSTRUCTION-GATE.md
git commit -m "docs: record m2 reconstruction implementation gate"
```
