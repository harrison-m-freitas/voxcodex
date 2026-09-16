# M2 Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen M2 Design v0.1 end-to-end from immutable `SourceArtifact` ingestion through validated/frozen CBM v0.1, with selective reprocessing, provenance, regression gates, and blind-holdout discipline.

**Architecture:** Build a Python modular monolith with immutable content-addressed artifacts, a transactional metadata/dependency store, deterministic PDF/Markdown adapters, staged reconstruction, explicit CBM materialization/validation, and a corpus runner. The implementation is split into six executable plans so each increment leaves independently testable software and can be reviewed before the next begins.

**Tech Stack:** Python 3.14.x; uv 0.12.x; Pydantic 2.13.x; Typer 0.27.x; SQLAlchemy 2.0.x + Alembic 1.20.x; SQLite for M2 metadata; RFC 8785 canonical JSON via `rfc8785` 0.1.4; PyMuPDF 1.28.x; markdown-it-py 4.2.x; pytest 9.1.x; Hypothesis 6.168+.

**Spec:** `architecture/M2-DESIGN-V0.1.md`

## Global Constraints

- Baseline CBM is exactly `architecture/CBM-V0.1.md`; M2 implementation MUST NOT mutate the CBM v0.1 contract.
- M2 Tier 1 input formats are textual PDF and Markdown; mixed PDF is Tier 1.5 evidence-preservation/best-effort; OCR-heavy PDF, EPUB, HTML, and DOCX remain non-gating for M2 v0.1.
- Quarantined blind-holdout SourceArtifacts `CC-05`, `CC-07`, `CC-14`, and `CC-18` MUST NOT be opened, parsed, rendered, indexed, sampled, or used in tests before implementation-candidate freeze.
- Regression Assertions v1 and M2 Blind Holdouts v1 are frozen inputs; code may consume their manifests but MUST NOT rewrite them.
- Original source bytes are immutable. Any normalization, rendering, extraction, correction, or reconstruction creates a new derived artifact.
- `ProcessingActivity` describes execution. Causal `input_refs`/`output_refs` belong to `Derivation`.
- All meaningful outputs are immutable and content-addressed with SHA-256; semantic JSON digests use RFC 8785 canonicalization.
- No LLM/OCR provider is introduced until deterministic implementation plus regression evidence demonstrates a concrete unmet need.
- Known silent loss of source-significant content blocks M2 completion.
- Same semantic inputs + same semantic configuration must yield the same semantic digest for deterministic processors.

---

## Execution precondition

Execute these plans in an isolated git worktree. If the supplied snapshot has no `.git`, initialize a repository and create one baseline commit before feature work. The implementation workspace must not expose quarantined source bytes to workers: keep the frozen manifests/metadata visible, but stage `CC-05`, `CC-07`, `CC-14`, and `CC-18` source bytes outside the normal development corpus path until the holdout reveal gate. The frozen archive remains untouched as audit evidence.

```bash
git init -b main
git add .
git commit -m "chore: import frozen m2 preimplementation baseline"
```

At execution time, use the `superpowers:using-git-worktrees` skill before starting Plan 01 feature work.

## Implementation sequence

1. `2026-09-14-m2-01-foundation-and-contracts.md` — repository/bootstrap, immutable artifact store, canonical digests, physical M2 contracts, metadata DAG, CLI, and quarantine enforcement.
2. `2026-09-14-m2-02-source-evidence.md` — SourceProfile plus PDF/Markdown Evidence adapters and inspectable EvidenceSnapshots.
3. `2026-09-14-m2-03-reconstruction.md` — normalization, reading order, blocks, cross-boundary state, structured candidates, issues, and ReconstructionSnapshots.
4. `2026-09-14-m2-04-materialization-validation.md` — CBM v0.1 physical models, CanonicalDraft, materialization, SourceAnchors/fidelity/provenance, validators, freeze gate.
5. `2026-09-14-m2-05-reprocessing-provenance.md` — ActivityFingerprint, cache reuse, dependency invalidation, ExecutionPlan, cost/usage, review decisions, selective reprocessing.
6. `2026-09-14-m2-06-corpus-candidate-freeze.md` — executable regression assertions, compatibility runner, support-tier classification, candidate freeze, one-way holdout reveal, M2 promotion evidence.

## File map locked by this roadmap

```text
pyproject.toml
uv.lock
src/voxcodex/
  __init__.py
  cli.py
  config.py
  ids.py
  digests.py
  domain/
    common.py
    source.py
    evidence.py
    reconstruction.py
    processing.py
    cbm/
      document.py
      content.py
      semantic.py
      structured.py
      provenance.py
      validation.py
  storage/
    blobs.py
    metadata.py
    schema.py
    migrations/
  adapters/
    base.py
    pdf.py
    markdown.py
  reconstruction/
    engine.py
    normalize.py
    reading_order.py
    blocks.py
    boundaries.py
    structured.py
    classifiers.py
  materialization/
    builder.py
    mappings.py
    anchors.py
    fidelity.py
  validation/
    engine.py
    schema_checks.py
    structural_checks.py
    traceability_checks.py
    fidelity_checks.py
    coverage_checks.py
    policies.py
  execution/
    fingerprint.py
    planner.py
    invalidation.py
    runner.py
    usage.py
  corpus/
    registry.py
    assertions.py
    runner.py
    candidate.py
    holdouts.py
tests/
  unit/
  integration/
  regression/
  corpus/
```

## Gates between plans

- **Gate F1 — Foundation:** canonicalization, immutable storage, metadata transactions, and quarantine tests pass.
- **Gate E1 — Evidence:** F1/W1/C1/C3 source slices produce inspectable evidence without semantic role assignment; Markdown fixture preserves syntax/source ranges.
- **Gate R1 — Reconstruction:** frozen Regression Assertions applicable to reconstruction pass for known cases; unresolved regions become explicit issues, never silent drops.
- **Gate C1 — Canonical:** known cases materialize to CBM v0.1 and pass `m2_poc_strict`; provenance traces selected objects to source.
- **Gate P1 — Reprocessing:** validation-only, local-reconstruction, and local-evidence-change scenarios prove dependency-driven reuse/invalidation.
- **Gate M2-CANDIDATE:** regression core is green; all non-quarantined Tier 1 compatibility claims are classified; candidate identity/configuration/claims are frozen.
- **Gate M2-HOLDOUT:** holdouts are revealed once against the frozen candidate. Failure marks that candidate failed; the same revealed holdout cannot become a blind pass after tuning.

## Definition of implementation completion

Implementation is complete only when the candidate satisfies the frozen M2 exit criteria and produces: EvidenceSnapshots, ReconstructionSnapshots, a frozen CanonicalRevision CBM v0.1, ValidationReports, ExecutionPlans/UsageRecords for required reprocessing scenarios, regression/corpus reports, candidate manifest, holdout conformance report, and promotion review.


## Spec coverage matrix

| Frozen design area | Implementation plan coverage |
|---|---|
| M2.1 boundary, inspectable intermediates, Tier 1/Tier 1.5 | Plans 01, 02, 06 |
| M2.2 E01–E10 SourceArtifact/Profile/Evidence, geometry, typography, overlays, confidence | Plans 01–02 |
| M2.3 R01–R13 normalization, reading order, blocks, classification, open state, structured content, issues | Plan 03 |
| M2.4 M01–M14 CanonicalDraft, mapping, SourceAnchor, fidelity, validation, coverage, freeze | Plan 04 |
| M2.5 P01–P16 fingerprints, cache, invalidation, retries, confidence/risk, human review, usage/cost, reprocessing | Plan 05 |
| M2.6 C01–C16 regression, support tiers, discovery, equivalence, candidate freeze, blind protocol, schema evolution | Plan 06 |
| CBM v0.1 S01–S56 physical enforcement | Plan 04 |
| Frozen Regression Assertions v1 | Plan 06 Task 1 |
| Frozen Holdouts v1 quarantine/reveal | Plan 01 Task 6; Plan 06 Tasks 4–6 |
| Compatibility Corpus v1 30/30 | Plan 06 Tasks 2–3 |

## Technology-baseline rationale

- Python 3.14 is selected because it is the current stable Python line and provides stdlib UUIDv7, useful for ordered operational event IDs.
- SQLAlchemy remains on stable 2.0.x rather than the 2.1 release-candidate line for the first M2 implementation.
- SQLite is sufficient for the single-node PoC metadata/DAG and keeps deployment simple; SQLAlchemy/Alembic preserve a migration path to PostgreSQL without changing domain contracts.
- Filesystem content-addressed blobs avoid prematurely selecting S3-compatible infrastructure while preserving the object-storage boundary.
- RFC 8785 gives a standard canonical JSON representation for deterministic hashing instead of inventing an ad hoc serializer.
- PyMuPDF is used for Tier 1 PDF evidence because the implementation needs text, geometry, fonts/glyph traces, images, and page rendering access in one deterministic adapter.
- No workflow engine, OCR service, LLM SDK, vector store, or web API is part of the first M2 implementation baseline. Their interfaces are added only after a demonstrated requirement.
