# M2.6 Corpus Runner, Candidate Freeze, and Holdout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the frozen Regression Assertions v1 and Compatibility Corpus v1 into executable gates, classify support results, freeze an M2 implementation candidate, then perform a one-way blind-holdout evaluation and promotion review.

**Architecture:** A corpus runner reads frozen registries/assertion manifests through a quarantine-aware registry, executes only capability-appropriate cases, and produces immutable reports. Candidate freeze binds code commit, lockfile, semantic configurations, capability claims, policies, regression assertions, and corpus manifest before holdout reveal.

**Tech Stack:** Existing M2 stack; no new parsing libraries introduced in this plan.

**Spec:** `architecture/M2-DESIGN-V0.1.md` M2.6 (C01–C16), `planning/M2-REGRESSION-ASSERTIONS-V1.md`, `M2-HOLDOUT-V1-FREEZE-MANIFEST.json`, `COMPATIBILITY-CORPUS-V1-FREEZE-MANIFEST.json`.

## Global Constraints

- Never read quarantined SourceArtifacts before candidate freeze.
- The candidate must freeze code identity, `uv.lock`, semantic config digests, validation policy, support/capability claims, assertion manifest, and corpus freeze manifest before holdout reveal.
- Holdout reveal is irreversible. If the frozen candidate fails a holdout capability claim, that candidate fails; tuning on that revealed holdout cannot convert it into a blind pass.
- Unsupported/deferred formats are classified by support tier and do not masquerade as Tier 1 failures.

---

### Task 1: Implement executable regression assertion schema/engine

**Files:**
- Create: `src/voxcodex/corpus/assertions.py`
- Test: `tests/unit/corpus/test_assertions.py`
- Create: `tests/regression/test_frozen_assertions.py`

**Interfaces:**
- Produces `AssertionSpec`, `AssertionResult`, `AssertionRunner.run(case, outputs, assertions) -> list[AssertionResult]`.
- Supports structural assertions, surface equality, topology, relation existence, provenance reachability, validation result, and negative assertions.

- [ ] **Step 1: Write failing parser test against frozen assertion manifest**

Load `corpus/manifests/M2-REGRESSION-ASSERTIONS-V1.json`; assert all entries validate and no unknown assertion operator is silently ignored.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/corpus/test_assertions.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement assertion operators with explicit dispatch**

Unknown operator raises `UnsupportedAssertionOperator`; every result includes case ID, assertion ID, status, affected refs, and diagnostic.

- [ ] **Step 4: Execute all 42 frozen assertions on known regression outputs**

Run: `uv run pytest tests/regression/test_frozen_assertions.py -v`
Expected: PASS before proceeding to compatibility runs.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/corpus/assertions.py tests/unit/corpus/test_assertions.py tests/regression/test_frozen_assertions.py
git commit -m "feat: execute frozen m2 regression assertions"
```

### Task 2: Implement compatibility/support-tier runner

**Files:**
- Create: `src/voxcodex/corpus/runner.py`
- Create: `src/voxcodex/corpus/evolution.py`
- Test: `tests/unit/corpus/test_runner.py`
- Test: `tests/corpus/test_non_holdout_compatibility.py`

**Interfaces:**
- Produces `CorpusRunResult` with result class `PASS|PASS_WITH_EXTENSION|PROCESSING_FAILURE|MODEL_GAP|MODEL_FAILURE|DEFERRED_BY_SUPPORT_TIER`.
- Produces immutable `SchemaEvolutionObservation` records for every `MODEL_GAP`/`MODEL_FAILURE`; observations do not mutate CBM v0.1.

- [ ] **Step 1: Write failing support-tier tests**

Tier 1 PDF/Markdown enters pipeline; HTML/EPUB/DOCX cases without adapters are reported `DEFERRED_BY_SUPPORT_TIER`, not `PROCESSING_FAILURE`.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/corpus/test_runner.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement runner and classification contract**

Use registry support tiers/capability claims; quarantined IDs must be rejected before source resolution. `MODEL_GAP`/`MODEL_FAILURE` creates a Schema Evolution Log observation with source/case, phenomenon, affected model area, evidence refs, and candidate resolutions; it does not change CBM v0.1.

- [ ] **Step 4: Run all 26 non-quarantined corpus cases**

Run: `uv run pytest tests/corpus/test_non_holdout_compatibility.py -v`
Expected: each case gets explicit classification; no unclassified source-significant loss; Tier 1 failures block candidate readiness.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/corpus/runner.py src/voxcodex/corpus/evolution.py tests/unit/corpus/test_runner.py tests/corpus/test_non_holdout_compatibility.py
git commit -m "feat: run compatibility corpus by support tier"
```

### Task 3: Implement cross-format equivalence assertions for available non-holdout pairs

**Files:**
- Create: `tests/corpus/test_equivalence.py`
- Modify: `src/voxcodex/corpus/assertions.py`

**Interfaces:**
- Produces comparison over canonical structure signatures rather than object IDs/serialization bytes.

- [ ] **Step 1: Write structural-signature unit tests**

Signature includes ordered role/tree shape, normalized source-supported surfaces, and structured topology summaries while excluding source locators and operational IDs.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/corpus/test_equivalence.py -v`
Expected: FAIL before comparator exists.

- [ ] **Step 3: Implement comparator only for pairs whose formats are supported**

Unsupported-format pair members are reported deferred; do not add HTML/EPUB adapters just to make this test green.

- [ ] **Step 4: Run tests**

Expected: supported pairs compare; unsupported pairs report explicit deferred status.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/corpus/assertions.py tests/corpus/test_equivalence.py
git commit -m "test: compare supported cross format canonical structure"
```

### Task 4: Implement candidate manifest/freeze gate

**Files:**
- Create: `src/voxcodex/corpus/candidate.py`
- Test: `tests/unit/corpus/test_candidate.py`
- Create: `planning/M2-CANDIDATE-FREEZE-CHECKLIST.md`

**Interfaces:**
- Produces `ImplementationCandidateManifest` and `freeze_candidate(...) -> ArtifactRef`.
- Required bound fields: git commit SHA, `uv.lock` SHA-256, Python/runtime versions, processor versions, semantic config digests, `m2_poc_strict` policy digest, regression assertion manifest digest, corpus freeze manifest digest, capability claims, known classifications, regression report digest.

- [ ] **Step 1: Write failing incomplete-candidate tests**

Omitting capability claims, lockfile digest, or validation policy digest must prevent freeze.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/corpus/test_candidate.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement candidate manifest and readiness checks**

Readiness requires regression green, required selective-reprocessing tests green, and no unresolved blocking Tier 1 `MODEL_GAP`, `MODEL_FAILURE`, `PROCESSING_FAILURE`, or known significant silent loss among non-quarantined cases. Three quarantined shortlist cases are intentionally withheld from pre-freeze shortlist evidence and are evaluated only through the blind protocol.

- [ ] **Step 4: Freeze candidate artifact**

Run: `uv run voxcodex candidate freeze --output M2-IMPLEMENTATION-CANDIDATE-V1.json`
Expected: exits 0 only when readiness checks pass.

- [ ] **Step 5: Commit candidate manifest without revealing holdouts**

```bash
git add M2-IMPLEMENTATION-CANDIDATE-V1.json planning/M2-CANDIDATE-FREEZE-CHECKLIST.md
git commit -m "release: freeze m2 implementation candidate v1"
```

### Task 5: Implement one-way holdout reveal control

**Files:**
- Modify: `src/voxcodex/corpus/holdouts.py`
- Test: `tests/unit/corpus/test_holdout_reveal.py`

**Interfaces:**
- Produces `reveal_holdouts(candidate_manifest_ref, holdout_manifest_ref, explicit_ack: str) -> RevealRecord`.
- Required acknowledgement string: `REVEAL_M2_HOLDOUTS_V1`.

- [ ] **Step 1: Write failing safety tests**

Reveal without frozen candidate, with mismatched manifest digest, or without exact acknowledgement must fail before source resolution.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/corpus/test_holdout_reveal.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement reveal record and irreversible state**

Reveal record stores candidate digest, holdout manifest digest, timestamp, actor/context, and marks v1 as revealed for this implementation history. It does not modify original holdout manifest.

- [ ] **Step 4: Run tests without actually revealing production holdouts**

Use synthetic holdout manifest fixture only.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/corpus/holdouts.py tests/unit/corpus/test_holdout_reveal.py
git commit -m "feat: gate irreversible m2 holdout reveal"
```

### Task 6: Execute blind holdouts against the frozen candidate

**Files:**
- Create: `planning/M2-HOLDOUT-CONFORMANCE-V1.md`
- Create: `M2-HOLDOUT-CONFORMANCE-V1.json`

**Interfaces:**
- Produces final blind results bound to the frozen candidate manifest.

- [ ] **Step 1: Verify candidate and repository are clean/frozen**

Run: `git status --porcelain`; expected empty. Recompute candidate manifest-bound hashes; expected exact match.

- [ ] **Step 2: Reveal once**

Run: `uv run voxcodex holdouts reveal --candidate M2-IMPLEMENTATION-CANDIDATE-V1.json --ack REVEAL_M2_HOLDOUTS_V1`
Expected: creates RevealRecord and unlocks only scopes defined by the frozen holdout manifest.

- [ ] **Step 3: Run holdout evaluation without changing code/config**

Run: `uv run voxcodex corpus run-holdouts --candidate M2-IMPLEMENTATION-CANDIDATE-V1.json`
Expected: outputs explicit result per holdout/capability claim. Do not edit code until results are recorded and candidate status declared.

- [ ] **Step 4: Record outcome**

If any claimed Tier 1 capability has `PROCESSING_FAILURE`, `MODEL_GAP`, `MODEL_FAILURE`, or unexplained significant silent loss, record candidate `FAILED_BLIND_CONFORMANCE`. Otherwise record `PASS_BLIND_CONFORMANCE`. A failed candidate may be fixed only as a new candidate; the revealed v1 holdouts become known regression evidence and a future blind claim requires newly selected external/unseen holdout evidence, not a rerun of the same holdouts.

- [ ] **Step 5: Commit results**

```bash
git add planning/M2-HOLDOUT-CONFORMANCE-V1.md M2-HOLDOUT-CONFORMANCE-V1.json
git commit -m "test: record m2 blind holdout conformance"
```

### Task 7: Promotion review and M2 closure

**Files:**
- Create: `planning/M2-PROMOTION-REVIEW.md`
- Create: `M2-PROMOTION-MANIFEST.json`
- Modify: `STATUS.json`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces auditable M2 completion state only if all frozen exit gates are satisfied.

- [ ] **Step 1: Verify all exit evidence**

Regression Assertions v1 pass; required Tier 1 compatibility cases are acceptable; provenance trace gate passes; validation/freeze gate passes; reprocessing A/B/C pass; blind conformance passes.

- [ ] **Step 2: Verify no CBM v0.1/schema mutation occurred**

Recompute `architecture/CBM-V0.1.md` hash against `PROMOTION-MANIFEST.json`; expected exact match unless an explicitly approved schema-evolution/rebaseline process occurred.

- [ ] **Step 3: Write promotion review and manifest**

Manifest binds candidate digest, reports, corpus freeze manifest, holdout result, code commit, and final capability claims.

- [ ] **Step 4: Mark M2 complete only if review is PASS**

Set `STATUS.json` stage to `m2_complete` and next step to the separately designed downstream milestone; otherwise preserve `m2_implementation` and classify blockers.

- [ ] **Step 5: Run full verification and commit**

Run: `uv run pytest -v`
Expected: PASS.

```bash
git add planning/M2-PROMOTION-REVIEW.md M2-PROMOTION-MANIFEST.json STATUS.json PROJECT_CONTEXT.md CHANGELOG.md
git commit -m "release: promote m2 document reconstruction baseline"
```
