# M2.4 CBM Materialization and Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize resolved ReconstructionSnapshots into physical CBM v0.1 revisions, generate SourceAnchors/fidelity/provenance, validate source accountability and structural integrity, and freeze only policy-compliant revisions.

**Architecture:** Build a `CanonicalDraft` from reconstruction through explicit mapping tables, then validate in deterministic layers before producing/finalizing a `CanonicalRevision`. CBM physical models mirror the frozen conceptual contract; registries are persisted as deterministic sharded artifacts to handle large documents.

**Tech Stack:** Foundation stack; no semantic-enrichment model provider.

**Spec:** `architecture/CBM-V0.1.md` plus `architecture/M2-DESIGN-V0.1.md` M2.4 (M01–M14).

## Global Constraints

- M2.4 cannot change reading order or reinterpret Evidence.
- Semantic/document relations already resolved by Reconstruction may be materialized; interpretive enrichment remains downstream.
- Frozen revision semantic payload is immutable. Supplemental validation after freeze never replaces the authorizing freeze report.
- `RoleProfile`/fidelity mappings are versioned policy artifacts.

---

### Task 1: Implement physical CBM v0.1 Pydantic contracts

**Files:**
- Create: `src/voxcodex/domain/cbm/document.py`
- Create: `src/voxcodex/domain/cbm/content.py`
- Create: `src/voxcodex/domain/cbm/semantic.py`
- Create: `src/voxcodex/domain/cbm/structured.py`
- Create: `src/voxcodex/domain/cbm/provenance.py`
- Create: `src/voxcodex/domain/cbm/validation.py`
- Test: `tests/unit/cbm/test_cbm_contracts.py`

**Interfaces:**
- Produces physical models for CBM v0.1 primitives and registries without adding new universal primitives.

- [ ] **Step 1: Write failing schema-invariant tests for S01–S56 representable checks**

Cover single owner for ContentFragment, SemanticRegistry authority, TableCell non-owning refs, FormulaPayload source/reconstructed separation, revision schema_version authority, and frozen immutability.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/cbm/test_cbm_contracts.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement frozen Pydantic contracts**

Use names/fields from `architecture/CBM-V0.1.md`; do not introduce additional required core fields. Extension roles/predicates/annotation types remain namespaced strings validated by registries/policies.

- [ ] **Step 4: Generate JSON Schema snapshots and compare in tests**

Write schemas under `schemas/cbm/0.1/*.schema.json`; test that generation is deterministic.

Run: `uv run pytest tests/unit/cbm/test_cbm_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/domain/cbm schemas/cbm tests/unit/cbm/test_cbm_contracts.py
git commit -m "feat: encode frozen cbm v0.1 contracts"
```

### Task 2: Implement deterministic registry sharding and CanonicalDraft

**Files:**
- Create: `src/voxcodex/materialization/builder.py`
- Create: `src/voxcodex/materialization/mappings.py`
- Test: `tests/unit/materialization/test_builder.py`

**Interfaces:**
- Produces `CanonicalTargetContext`, `CanonicalDraft`, `RegistryManifest`, deterministic shard writer.
- Shards are ordered by explicit logical/stable keys and max 1000 objects per shard for M2.

- [ ] **Step 1: Write failing deterministic sharding test**

Same objects in different Python insertion order must produce identical shard digests/manifests. Add a resolved reconstruction role that has no registered CBM mapping and assert the builder emits a `MaterializationIssue` rather than dropping the unit.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/materialization/test_builder.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement target context/bootstrap and sharding**

`CanonicalTargetContext` supplies existing Work/Edition/CanonicalDocument refs or explicit auditable source metadata/refs from which those identities are created deterministically; materialization must not infer or invent bibliographic identity. Deterministic stable object IDs derive from reconstruction snapshot digest + reconstruction stable key.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/materialization/builder.py src/voxcodex/materialization/mappings.py tests/unit/materialization/test_builder.py
git commit -m "feat: build deterministic canonical drafts"
```

### Task 3: Implement SourceAnchor, Fidelity, and structured payload mapping

**Files:**
- Create: `src/voxcodex/materialization/anchors.py`
- Create: `src/voxcodex/materialization/fidelity.py`
- Modify: `src/voxcodex/materialization/mappings.py`
- Test: `tests/unit/materialization/test_anchors_fidelity.py`
- Test: `tests/regression/test_materialization_known_cases.py`

**Interfaces:**
- Produces direct/aggregate SourceAnchors, effective fidelity calculation, and mappings from structured candidates to TablePayload/FormulaPayload/figure structure.

- [ ] **Step 1: Write failing cross-page anchor and fidelity-inheritance tests**

A paragraph spanning two pages gets two physical anchors; child constraints can strengthen but not weaken inherited fidelity.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/materialization/test_anchors_fidelity.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement mapping policies**

Version `RoleProfileRegistry` and `FidelityPolicy` as canonical JSON policy artifacts; include mappings needed by frozen regression vocabulary. Core node/payload kinds are strict; namespaced role/predicate/annotation extensions are allowed only through the registry; an unregistered new primitive is classified as a possible `MODEL_GAP`.

- [ ] **Step 4: Run F1/W2/C1/C3/W-RND materialization assertions from known sources**

Assert SpeakerCue sibling Speech, TablePayload topology, footnote relation, FormulaPayload source representation, and terminal omission-marker separation where those cases are not M2 quarantined sources.

Run: `uv run pytest tests/regression/test_materialization_known_cases.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/materialization tests/unit/materialization tests/regression/test_materialization_known_cases.py
git commit -m "feat: map reconstruction into traceable cbm"
```

### Task 4: Implement layered validation and `m2_poc_strict`

**Files:**
- Create: `src/voxcodex/validation/engine.py`
- Create: `src/voxcodex/validation/schema_checks.py`
- Create: `src/voxcodex/validation/structural_checks.py`
- Create: `src/voxcodex/validation/traceability_checks.py`
- Create: `src/voxcodex/validation/fidelity_checks.py`
- Create: `src/voxcodex/validation/coverage_checks.py`
- Create: `src/voxcodex/validation/policies.py`
- Test: `tests/unit/validation/test_validation_layers.py`

**Interfaces:**
- Produces `validate_revision(revision_ref, policy_ref) -> ValidationReport`.
- Produces versioned `m2_poc_strict` ValidationPolicy.

- [ ] **Step 1: Write failing validation tests**

Construct invalid cases: dangling ref, tree cycle, illegal role/node_class pair, malformed table topology, missing source accountability, child fidelity weakening, suspected unmapped loss. Assert blocking severities according to policy.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/validation/test_validation_layers.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement checks and evidence-accountability classification**

Unmapped evidence classification must be one of `canonicalized`, `intentionally_noncanonical`, `unresolved`, `suspected_loss`. A versioned `EvidenceSignificancePolicy` decides significance; any known significant `suspected_loss` blocks freeze under `m2_poc_strict`.

- [ ] **Step 4: Run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/validation tests/unit/validation
git commit -m "feat: validate cbm structure traceability and fidelity"
```

### Task 5: Implement revision lifecycle/freeze gate and idempotence

**Files:**
- Modify: `src/voxcodex/materialization/builder.py`
- Create: `tests/integration/materialization/test_revision_freeze.py`

**Interfaces:**
- Produces `materialize_revision(reconstruction_ref, target_context, config_ref) -> CanonicalRevision`.
- Produces `freeze_revision(revision_ref, validation_report_ref) -> FrozenRevisionRecord`.

- [ ] **Step 1: Write failing freeze-gate tests**

Blocking report prevents freeze; passing report + manifests permits freeze; a frozen revision's authorizing `validation_report_ref` cannot be replaced by supplemental revalidation.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/materialization/test_revision_freeze.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement lifecycle transitions and semantic digest**

Compute frozen revision digest from canonical semantic content/manifests excluding administrative superseded/invalid markers and execution timestamps. Freeze must bind `source_mapping_manifest_ref`, `provenance_manifest_ref`, the authorizing `validation_report_ref`, and `content_digest`; `fidelity_manifest_ref` remains optional per CBM v0.1. Frozen-revision source/evidence/provenance refs remain addressable under retention/audit policy.

- [ ] **Step 4: Materialize same ReconstructionSnapshot twice**

Assert equal semantic revision digest for same schema/config; run IDs/activity IDs may differ.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/materialization/builder.py tests/integration/materialization/test_revision_freeze.py
git commit -m "feat: freeze validated canonical revisions"
```

### Task 6: Canonical gate

**Files:**
- Create: `planning/M2-IMPLEMENTATION-CANONICAL-GATE.md`

**Interfaces:**
- Produces traceability evidence for selected paragraph, verse, terminal command, table cell, footnote, and formula objects.

- [ ] **Step 1: Run CBM/materialization/validation suites**

Run: `uv run pytest tests/unit/cbm tests/unit/materialization tests/unit/validation tests/integration/materialization tests/regression/test_materialization_known_cases.py -v`
Expected: PASS.

- [ ] **Step 2: Execute provenance trace command for six object kinds**

Add/use CLI `voxcodex trace OBJECT_ID`; each trace must terminate at SourceArtifact + EvidenceUnit/locator through explicit derivations/activities.

- [ ] **Step 3: Record results without opening M2 holdouts**

- [ ] **Step 4: Commit**

```bash
git add planning/M2-IMPLEMENTATION-CANONICAL-GATE.md
git commit -m "docs: record m2 canonical implementation gate"
```
