# M2.5 Reprocessing, Provenance, and Cost Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the M2 pipeline incrementally re-runnable with semantic fingerprints, cache reuse, dependency-driven invalidation, explicit execution plans, usage/cost accounting, localized confidence, and auditable human review.

**Architecture:** Build an execution planner over the persisted Derivation DAG. Every planned activity has semantic inputs/config and a reproducibility class; reusable outputs are found by ActivityFingerprint. Staleness is computed contextually from the target lineage and never mutates historical artifacts.

**Tech Stack:** Foundation persistence stack; no distributed workflow engine in M2 v0.1.

**Spec:** `architecture/M2-DESIGN-V0.1.md` M2.5 (P01–P16).

## Global Constraints

- Cache reuse preserves original producing activity/derivation; it does not fabricate a new causal derivation.
- Operational configuration such as log verbosity is excluded from semantic fingerprints.
- Confidence scales are not compared across incompatible producer/type contexts unless calibrated.
- Human correction creates new activity/derivation/snapshot; no direct mutation of prior artifacts.

---

### Task 1: Implement ActivityFingerprint and processor/config registry

**Files:**
- Create: `src/voxcodex/execution/fingerprint.py`
- Test: `tests/unit/execution/test_fingerprint.py`

**Interfaces:**
- Produces `ActivityFingerprint.compute(activity_type, processor, semantic_config_digest, input_digests, profile_versions, schema_versions) -> str`.

- [ ] **Step 1: Write failing fingerprint tests**

Changing input digest, processor version, semantic threshold, or schema version changes fingerprint; changing log level does not.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_fingerprint.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement canonical fingerprint payload + SHA-256**

Sort input references by declared semantic order when order matters; otherwise normalize declared sets before canonicalization.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/fingerprint.py tests/unit/execution/test_fingerprint.py
git commit -m "feat: fingerprint semantic processing activities"
```

### Task 2: Implement cache lookup and contextual staleness/invalidation

**Files:**
- Create: `src/voxcodex/execution/invalidation.py`
- Modify: `src/voxcodex/storage/metadata.py`
- Test: `tests/unit/execution/test_invalidation.py`
- Test: `tests/integration/execution/test_cache_reuse.py`

**Interfaces:**
- Produces `find_reusable_output(fingerprint) -> Sequence[ArtifactRef]`.
- Produces `compute_affected(changed_refs, target_refs) -> AffectedGraph`.

- [ ] **Step 1: Write failing DAG propagation tests**

Graph A->B->C and A->D; changing B affects C, not D. Historical B/C records remain queryable.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_invalidation.py tests/integration/execution/test_cache_reuse.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement reverse-edge traversal and fingerprint index**

Add indexed `activity_fingerprint` to activity metadata and query original completed outputs for reuse.

- [ ] **Step 4: Prove cache hit does not create false provenance**

Second identical execution returns existing output refs; producing activity ID remains the original activity.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/invalidation.py src/voxcodex/storage/metadata.py tests/unit/execution tests/integration/execution/test_cache_reuse.py
git commit -m "feat: add dependency invalidation and provenance safe cache"
```

### Task 3: Implement ExecutionPlan and runner

**Files:**
- Create: `src/voxcodex/execution/planner.py`
- Create: `src/voxcodex/execution/runner.py`
- Test: `tests/unit/execution/test_planner.py`

**Interfaces:**
- Produces `ExecutionPlan`, `PlannedActivity`, `ReuseCandidate`, `InvalidatedArtifact`.
- Produces `plan_to_cbm(source_ref, target_context, config) -> ExecutionPlan` and `execute_plan(plan) -> ExecutionResult`.

- [ ] **Step 1: Write failing dry-run test**

After a completed pipeline, a second unchanged `plan_to_cbm` must report eligible reuse for all deterministic stages and zero required processor work.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_planner.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement planner from dependency/fingerprint queries**

Plan is immutable and separate from execution. A planned activity becomes a ProcessingActivity only when execution starts.

- [ ] **Step 4: Add CLI `voxcodex plan` and `voxcodex run`**

`voxcodex plan SOURCE_ID --target cbm` prints reuse/process counts and estimated usage without executing.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/planner.py src/voxcodex/execution/runner.py src/voxcodex/cli.py tests/unit/execution/test_planner.py
git commit -m "feat: plan and execute reusable m2 workflows"
```


### Task 4: Implement reproducibility classes, failure taxonomy, retry policy, and separate telemetry

**Files:**
- Create: `src/voxcodex/execution/failures.py`
- Create: `src/voxcodex/execution/telemetry.py`
- Modify: `src/voxcodex/execution/runner.py`
- Test: `tests/unit/execution/test_failures_retries.py`
- Test: `tests/unit/execution/test_telemetry.py`

**Interfaces:**
- Produces `ReproducibilityClass` values `deterministic`, `seeded`, `non_deterministic`, `externally_variable`.
- Produces `FailureClass` values `transient`, `permanent_input`, `processor_bug`, `policy_block`, `resource_limit`, `external_dependency`.
- Produces `RetryPolicy.decide(failure, attempt) -> RetryDecision`.
- Produces operational `ExecutionTelemetry` that is not used as provenance authority.

- [ ] **Step 1: Write failing retry-policy tests**

A timeout classified `transient` can retry under policy; `processor_bug`, `policy_block`, and `permanent_input` cannot blind-retry. Changing semantic config/model/input creates a new ProcessingActivity rather than a retry of the original activity.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_failures_retries.py tests/unit/execution/test_telemetry.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement taxonomy, retry decision, and telemetry**

Telemetry fields include duration, queue/wait time when present, retry count, peak/observed resource metrics when measurable, and error diagnostics. Telemetry may reference an activity ID but does not define its causal inputs/outputs.

- [ ] **Step 4: Add partial-output atomicity test**

A multi-page extraction job may fail after page N, but only page artifacts marked complete are reusable. The aggregate snapshot is not marked complete until its manifest policy succeeds.

Run: `uv run pytest tests/unit/execution/test_failures_retries.py tests/unit/execution/test_telemetry.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/failures.py src/voxcodex/execution/telemetry.py src/voxcodex/execution/runner.py tests/unit/execution/test_failures_retries.py tests/unit/execution/test_telemetry.py
git commit -m "feat: classify failures retries and execution telemetry"
```

### Task 5: Implement UsageRecord and deterministic cost estimation hooks

**Files:**
- Create: `src/voxcodex/execution/usage.py`
- Test: `tests/unit/execution/test_usage.py`

**Interfaces:**
- Produces `UsageEstimator.estimate(planned_activity) -> UsageEstimate`.
- Produces `UsageRecord` persistence from actual execution metrics.

- [ ] **Step 1: Write failing estimate-vs-actual tests**

For deterministic local PDF page extraction, estimate page count; actual records processed page count/duration/bytes. No invented currency cost is emitted when pricing policy lacks one.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_usage.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement usage dimensions**

Initial dimensions: input bytes, page/file units, CPU duration, output bytes, external model/API units (zero for current processors), optional estimated/actual monetary cost with `pricing_ref`.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/usage.py tests/unit/execution/test_usage.py
git commit -m "feat: account for m2 usage and cost estimates"
```

### Task 6: Implement ReviewRisk and auditable ReviewDecision

**Files:**
- Create: `src/voxcodex/execution/review.py`
- Test: `tests/unit/execution/test_review.py`

**Interfaces:**
- Produces `ReviewCandidate`, `ReviewRiskPolicy`, `ReviewDecision` application producing new derivation/snapshot.

- [ ] **Step 1: Write failing test proving confidence != review risk**

A high-confidence/high-impact table topology issue may rank above a low-confidence/decorative marker issue according to policy.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/execution/test_review.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement policy-based prioritization and correction lineage**

A correction must produce a new immutable output and `manual_asserted`/`corrected` derivation; prior output remains accessible.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/execution/review.py tests/unit/execution/test_review.py
git commit -m "feat: add risk based auditable human review"
```

### Task 7: Prove the three mandatory selective-reprocessing scenarios

**Files:**
- Create: `tests/integration/execution/test_selective_reprocessing.py`
- Create: `planning/M2-IMPLEMENTATION-REPROCESSING-GATE.md`

**Interfaces:**
- Demonstrates M2.6 required scenarios A/B/C with real artifact DAGs.

- [ ] **Step 1: Write Scenario A test — ValidationPolicy change only**

Assert Evidence, Reconstruction, and CanonicalRevision payload refs are reused; only ValidationReport changes.

- [ ] **Step 2: Write Scenario B test — local table/formula reconstruction profile change**

Assert evidence reused, affected reconstruction/materialization rerun, unrelated reconstruction artifacts reused.

- [ ] **Step 3: Write Scenario C test — one page/region evidence replacement**

Assert only downstream dependents of changed page/region are invalidated plus necessary reconciliation radius; unrelated regions reused.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/integration/execution/test_selective_reprocessing.py -v`
Expected: PASS for all three scenarios.

- [ ] **Step 5: Record gate evidence and commit**

```bash
git add tests/integration/execution/test_selective_reprocessing.py planning/M2-IMPLEMENTATION-REPROCESSING-GATE.md
git commit -m "test: prove selective m2 reprocessing"
```
