# M2 Holdout Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and freeze a production M2 holdout executor that composes Evidence → Reconstruction → CBM Materialization → Validation, binds that implementation into candidate V2, and reaches the irreversible reveal boundary without accessing any real holdout SourceArtifact.

**Architecture:** Add a preflight layer that validates candidate/reveal/frozen-scope integrity before source I/O, a deterministic production reconstruction stage over existing adapters and reconstruction primitives, and a single `M2PipelineProcessor` that emits auditable result classifications and run reports. Candidate V2 adds a semantic implementation-tree digest so post-freeze code drift is detectable; V1 remains immutable historical evidence.

**Tech Stack:** Python 3.14.7, uv 0.12.13, pytest 9.x, Pydantic 2.x, Typer 0.27.x, PyMuPDF, markdown-it-py, SQLAlchemy, RFC 8785 canonical JSON.

**Spec:** `docs/superpowers/specs/2026-09-17-m2-holdout-executor-design.md`

## Global Constraints

- `CC-05`, `CC-07`, `CC-14`, and `CC-18` remain **FROZEN / UNREVEALED / untouched** throughout Tasks 1–7.
- Do not open, unpack, parse, render, re-hash, inspect, or resolve any real holdout `source/` path before explicit reveal.
- Tests before reveal use only synthetic PDF/Markdown/ZIP fixtures plus already-public frozen metadata.
- `M2-IMPLEMENTATION-CANDIDATE-V1.json` and digest `666271411488ab2563263efda93a8aa5d182396098eac92e8a356aa69dbfacf9` remain unchanged as historical pre-reveal evidence.
- Replacement candidate is `M2-IMPLEMENTATION-CANDIDATE-V2.json` with candidate id `m2-implementation-candidate-v2`.
- The exact irreversible acknowledgement remains `REVEAL_M2_HOLDOUTS_V1`.
- No holdout-specific heuristic, assertion relaxation, support-tier downgrade, or CBM v0.1 mutation is permitted.
- `PASS` requires complete execution, strict ValidationPolicy PASS, frozen CanonicalRevision, and no significant suspected loss.
- CI must verify candidate V2 after freeze; it must not regenerate V2 or silently fall back to V1.

---

## File Structure

- `src/voxcodex/corpus/candidate.py` — candidate V1/V2 model, semantic implementation-tree digest, freeze/verify logic.
- `src/voxcodex/config/m2-pipeline-v0.1.json` — frozen semantic wiring/profile configuration for the production pipeline.
- `src/voxcodex/corpus/holdout_execution.py` — frozen-scope parsing, reveal/candidate preflight, run-report models.
- `src/voxcodex/reconstruction/production.py` — deterministic Evidence → ReconstructionUnit production stage.
- `src/voxcodex/corpus/m2_pipeline.py` — production orchestration from selected SourceArtifact scope through validation/classification.
- `src/voxcodex/materialization/builder.py` — attach source anchors supplied by the pipeline while preserving existing builder semantics.
- `src/voxcodex/materialization/mappings.py` — register `document.root` as the canonical root mapping.
- `src/voxcodex/cli.py` — `candidate freeze --candidate-id` and `corpus run-holdouts`.
- `tests/unit/corpus/test_candidate_v2.py` — candidate V2 identity/drift tests.
- `tests/unit/corpus/test_holdout_execution.py` — scope/preflight safety tests.
- `tests/unit/reconstruction/test_production.py` — production reconstruction behavior over synthetic Evidence.
- `tests/integration/corpus/test_m2_pipeline_processor.py` — synthetic PDF/Markdown/ZIP end-to-end processor tests.
- `tests/integration/cli/test_holdout_run_cli.py` — CLI preflight/report tests.
- `planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json` — final green pre-freeze evidence for V2.
- `planning/M2-HOLDOUT-EXECUTOR-GATE.md` — pre-reveal gate evidence and protocol status.
- `M2-IMPLEMENTATION-CANDIDATE-V2.json` — immutable replacement candidate, created only after all pre-reveal gates are green.
- `.github/workflows/m2-plan02-ci.yml` — pre-freeze generation followed by post-freeze V2 verification.

---

### Task 1: Harden Candidate V2 Identity

**Files:**
- Modify: `src/voxcodex/corpus/candidate.py`
- Modify: `src/voxcodex/cli.py`
- Create: `tests/unit/corpus/test_candidate_v2.py`
- Modify: `tests/integration/cli/test_candidate_cli.py`

**Interfaces:**
- Produces: `implementation_tree_digest(repo_root: Path) -> str`
- Produces: optional `ImplementationCandidateManifest.implementation_tree_digest: str | None`
- Produces: `build_repository_candidate(..., candidate_id: str = "m2-implementation-candidate-v1")`
- Produces: CLI option `candidate freeze --candidate-id <id>`
- Consumes later: candidate V2 preflight and CI verification.

- [ ] **Step 1: Write failing tests for semantic implementation-tree binding**

Create `tests/unit/corpus/test_candidate_v2.py`:

```python
from pathlib import Path

import pytest

from voxcodex.corpus.candidate import (
    CandidateReadinessError,
    ImplementationCandidateManifest,
    implementation_tree_digest,
)


def test_implementation_tree_digest_changes_when_semantic_source_changes(tmp_path: Path) -> None:
    (tmp_path / "src/voxcodex").mkdir(parents=True)
    (tmp_path / "src/voxcodex/a.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("lock-v1\n", encoding="utf-8")

    first = implementation_tree_digest(tmp_path)
    (tmp_path / "src/voxcodex/a.py").write_text("VALUE = 2\n", encoding="utf-8")
    second = implementation_tree_digest(tmp_path)

    assert first != second


def test_candidate_v2_requires_implementation_tree_digest() -> None:
    data = {
        "candidate_id": "m2-implementation-candidate-v2",
        "git_commit_sha": "a" * 40,
        "uv_lock_sha256": "b" * 64,
        "python_version": "3.14.7",
        "uv_version": "0.12.13",
        "processor_versions": {"pipeline": "1"},
        "semantic_config_digests": {"pipeline": "c" * 64},
        "validation_policy_digest": "d" * 64,
        "regression_assertion_manifest_digest": "e" * 64,
        "corpus_freeze_manifest_digest": "f" * 64,
        "holdout_freeze_manifest_digest": "1" * 64,
        "regression_report_digest": "2" * 64,
        "capability_claims": ("Tier 1 PDF and Markdown",),
        "known_classifications": (),
        "regression_status": "PASS",
        "selective_reprocessing_status": "PASS",
        "holdouts_withheld": ("CC-05", "CC-07", "CC-14", "CC-18"),
    }
    manifest = ImplementationCandidateManifest(**data)

    with pytest.raises(CandidateReadinessError, match="implementation_tree_digest"):
        from voxcodex.corpus.candidate import _assert_ready
        _assert_ready(manifest)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
uv run pytest tests/unit/corpus/test_candidate_v2.py -v
```

Expected: FAIL because `implementation_tree_digest` and the V2 readiness rule do not exist.

- [ ] **Step 3: Implement deterministic tree digest and V2 readiness**

In `src/voxcodex/corpus/candidate.py`, add:

```python
SEMANTIC_TREE_ROOTS = (
    Path("src/voxcodex"),
    Path("pyproject.toml"),
    Path("uv.lock"),
)


def implementation_tree_digest(repo_root: Path) -> str:
    entries: list[dict[str, str]] = []
    for root in SEMANTIC_TREE_ROOTS:
        absolute = repo_root / root
        if absolute.is_dir():
            files = sorted(
                path for path in absolute.rglob("*")
                if path.is_file() and path.suffix in {".py", ".json"}
            )
        else:
            files = [absolute]
        for path in files:
            if not path.is_file():
                raise CandidateReadinessError(f"semantic implementation input missing: {path}")
            entries.append({
                "path": path.relative_to(repo_root).as_posix(),
                "sha256": sha256_bytes(path.read_bytes()),
            })
    return sha256_bytes(canonical_json_bytes(entries))
```

Add to `ImplementationCandidateManifest`:

```python
implementation_tree_digest: str | None = None
```

Extend readiness:

```python
if manifest.candidate_id == "m2-implementation-candidate-v2" and not manifest.implementation_tree_digest:
    errors.append("implementation_tree_digest")
```

Extend `build_repository_candidate` with `candidate_id` and set the tree digest only for V2:

```python
implementation_digest = (
    implementation_tree_digest(repo_root)
    if candidate_id == "m2-implementation-candidate-v2"
    else None
)
```

Do not alter serialization of historical V1: `exclude_none=True` must keep V1 byte semantics unchanged.

- [ ] **Step 4: Add CLI candidate-id coverage**

Modify `candidate_freeze`:

```python
candidate_id: str = typer.Option(
    "m2-implementation-candidate-v1",
    "--candidate-id",
)
```

Pass `candidate_id=candidate_id` into `build_repository_candidate`.

Add an integration assertion that `--candidate-id m2-implementation-candidate-v2` writes `implementation_tree_digest`.

- [ ] **Step 5: Run candidate tests and existing candidate verification**

Run:

```bash
uv run pytest   tests/unit/corpus/test_candidate.py   tests/unit/corpus/test_candidate_v2.py   tests/integration/cli/test_candidate_cli.py -v
```

Expected: PASS. Historical V1 verification remains green.

- [ ] **Step 6: Commit**

```bash
git add src/voxcodex/corpus/candidate.py src/voxcodex/cli.py   tests/unit/corpus/test_candidate_v2.py tests/integration/cli/test_candidate_cli.py
git commit -m "feat: bind candidate v2 to semantic implementation tree"
```

---

### Task 2: Add Frozen Holdout Scope and Preflight

**Files:**
- Create: `src/voxcodex/corpus/holdout_execution.py`
- Create: `tests/unit/corpus/test_holdout_execution.py`

**Interfaces:**
- Consumes: `load_frozen_candidate()`, `verify_repository_candidate()`, canonical SHA-256 helpers.
- Produces: `HoldoutExecutionSpec`
- Produces: `HoldoutRevealRecord`
- Produces: `load_holdout_execution_specs(selection_manifest: Path, candidate_digest: str, holdout_freeze_digest: str) -> tuple[HoldoutExecutionSpec, ...]`
- Produces: `verify_holdout_preflight(...) -> HoldoutExecutionSpec`
- Consumed by: Task 4 processor and Task 5 CLI.

- [ ] **Step 1: Write RED tests for scope conversion and no-I/O preflight**

Create tests including:

```python
def test_pdf_scope_converts_frozen_one_based_pages_to_zero_based_indexes(tmp_path: Path) -> None:
    specs = load_holdout_execution_specs(
        _selection_manifest(tmp_path, pages=(57, 58)),
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
    )
    assert specs[0].selected_page_indexes == (56, 57)


def test_markdown_zip_scope_keeps_exact_frozen_member_path(tmp_path: Path) -> None:
    specs = load_holdout_execution_specs(
        _selection_manifest(tmp_path, zip_member="book-main/src/ch15-01-box.md"),
        candidate_digest="a" * 64,
        holdout_freeze_digest="b" * 64,
    )
    assert specs[0].zip_member_path == "book-main/src/ch15-01-box.md"


def test_preflight_rejects_missing_reveal_before_source_resolution(tmp_path: Path) -> None:
    sentinel = tmp_path / "corpus/compatibility/CC-SYN/source/secret.pdf"
    with pytest.raises(HoldoutPreflightError, match="reveal"):
        verify_holdout_preflight(
            repo_root=tmp_path,
            candidate_path=_candidate_v2(tmp_path),
            regression_report_path=_report(tmp_path),
            selection_manifest_path=_selection_manifest(tmp_path),
            holdout_freeze_manifest_path=_freeze_manifest(tmp_path),
            reveal_record_path=tmp_path / "missing-reveal.json",
            corpus_case_id="CC-SYN",
        )
    assert not sentinel.exists()
```

Also cover candidate-digest mismatch, holdout-freeze mismatch, reveal-version mismatch, unknown case, and scope mismatch.

- [ ] **Step 2: Run RED**

```bash
uv run pytest tests/unit/corpus/test_holdout_execution.py -v
```

Expected: import/function failures.

- [ ] **Step 3: Implement immutable execution/preflight models**

Create:

```python
class HoldoutExecutionSpec(FrozenModel):
    holdout_id: str
    corpus_case_id: str
    support_tier: str
    format: str
    source_relative_path: str
    source_sha256: str
    candidate_digest: str
    holdout_freeze_digest: str
    selected_page_indexes: tuple[int, ...] = ()
    zip_member_path: str | None = None
    zip_member_sha256: str | None = None
    zip_member_byte_size: int | None = None


class HoldoutRevealRecord(FrozenModel):
    candidate_digest: str
    holdout_manifest_digest: str
    revealed_at: str
    actor: str
    context: str
    reveal_version: str
```

Parse only committed metadata; do not resolve `source_relative_path`.

- [ ] **Step 4: Implement ordered preflight**

Preflight order must be:

```python
frozen_candidate, frozen_digest = load_frozen_candidate(candidate_path)
verify_repository_candidate(
    repo_root=repo_root,
    candidate_path=candidate_path,
    regression_report_path=regression_report_path,
)
holdout_bytes = holdout_freeze_manifest_path.read_bytes()
assert sha256_bytes(holdout_bytes) == frozen_candidate.holdout_freeze_manifest_digest
reveal = HoldoutRevealRecord.model_validate_json(reveal_record_path.read_bytes())
assert reveal.candidate_digest == frozen_digest
assert reveal.holdout_manifest_digest == sha256_bytes(holdout_bytes)
assert reveal.reveal_version == "M2_HOLDOUTS_V1"
specs = load_holdout_execution_specs(...)
return exact_requested_spec
```

Any failure raises `HoldoutPreflightError` before a source path is returned to the caller.

- [ ] **Step 5: Run GREEN and quarantine regression**

```bash
uv run pytest   tests/unit/corpus/test_holdout_execution.py   tests/integration/corpus/test_quarantine_before_io.py   tests/unit/corpus/test_holdout_reveal.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/voxcodex/corpus/holdout_execution.py tests/unit/corpus/test_holdout_execution.py
git commit -m "feat: add frozen holdout execution preflight"
```

---

### Task 3: Build the Production Reconstruction Stage

**Files:**
- Create: `src/voxcodex/config/m2-pipeline-v0.1.json`
- Create: `src/voxcodex/reconstruction/production.py`
- Modify: `src/voxcodex/materialization/mappings.py`
- Create: `tests/unit/reconstruction/test_production.py`
- Modify: `tests/unit/materialization/test_builder.py` if root mapping assertions belong there.

**Interfaces:**
- Produces: `production_reconstruction_profile() -> ReconstructionProfile`
- Produces: `ProductionEvidenceStage(evidence_units: tuple[EvidenceUnit, ...])`
- Produces: stage `run(context, units) -> StageResult`
- Produces mapping: `document.root -> node_class="root"`
- Consumed by: `M2PipelineProcessor`.

- [ ] **Step 1: Freeze semantic wiring configuration**

Create `src/voxcodex/config/m2-pipeline-v0.1.json`:

```json
{
  "schema": "voxcodex.m2_pipeline_config.v1",
  "version": "0.1.0",
  "pdf": {
    "glyph_runs": true
  },
  "reconstruction": {
    "baseline_tolerance": 0.02,
    "max_inline_gap": 0.08,
    "region_x_tolerance": 0.08,
    "layout_dehyphenation": false,
    "classification_resolve_threshold": 0.8,
    "heading_min_relative_font_size": 1.2,
    "running_header_min_recurrence": 3,
    "speaker_cue_max_chars": 32,
    "table_axis_tolerance": 0.04
  },
  "markdown_roles": {
    "heading_open": "text.heading",
    "paragraph_open": "text.paragraph",
    "fence": "technical.code_block",
    "bullet_list_open": "text.list",
    "ordered_list_open": "text.list",
    "list_item_open": "text.list_item"
  },
  "fallback_role": "text.paragraph",
  "formula_requires_math_glyph_shape": true
}
```

This file is semantic input and will be included by Task 1's implementation-tree digest and by the candidate semantic config digest map.

- [ ] **Step 2: Write RED unit tests**

Cover:

```python
def test_markdown_stage_maps_heading_paragraph_and_fence_without_source_literals():
    result = _stage(
        syntax("heading_open", "# Heading\n"),
        syntax("paragraph_open", "Body text.\n"),
        syntax("fence", "```sh\necho hi\n```\n"),
    )
    assert [u.properties["resolved_role"] for u in result.units[1:]] == [
        "text.heading", "text.paragraph", "technical.code_block"
    ]


def test_pdf_stage_has_one_root_and_preserves_evidence_refs():
    result = _stage(pdf_span("Alpha", x0=.1, y0=.1, x1=.4, y1=.12))
    assert result.units[0].properties["resolved_role"] == "document.root"
    assert result.units[1].parent_ref == result.units[0].id
    assert result.units[1].evidence_refs


def test_formula_requires_math_shape_not_geometry_alone():
    result = _stage(
        pdf_span("ordinary prose", x0=.1, y0=.1, x1=.4, y1=.12),
        pdf_span("next line", x0=.1, y0=.2, x1=.4, y1=.22),
    )
    assert "structured.formula" not in {
        u.properties.get("resolved_role") for u in result.units
    }
```

Also test figure assets become `structured.figure` and terminal detection uses existing `detect_terminal_candidate` without exact command literals.

- [ ] **Step 3: Run RED**

```bash
uv run pytest tests/unit/reconstruction/test_production.py -v
```

Expected: module/function missing.

- [ ] **Step 4: Register canonical root role**

In `RoleMappingRegistry.v01_defaults()`, add:

```python
mappings.append(
    RoleMapping(
        reconstruction_role="document.root",
        node_class="root",
        cbm_role="document.root",
    )
)
```

Keep all existing role mappings unchanged.

- [ ] **Step 5: Implement deterministic production stage**

Core structure:

```python
class ProductionEvidenceStage:
    name = "m2-production-structure"
    version = "0.1.0"

    def __init__(
        self,
        evidence_units: tuple[EvidenceUnit, ...],
        profile: ReconstructionProfile,
    ) -> None:
        self.evidence_units = evidence_units
        self.profile = profile

    def run(
        self,
        context: ReconstructionContext,
        units: tuple[ReconstructionUnit, ...],
    ) -> StageResult:
        root = _root_unit(context, self.evidence_units)
        if any(unit.evidence_class == "syntax_unit" for unit in self.evidence_units):
            children, issues = _markdown_units(context, root, self.evidence_units)
        else:
            children, issues = _pdf_units(context, root, self.evidence_units, self.profile)
        return StageResult(units=(root, *children), issues=issues)
```

Rules are format-generic and configuration-driven:

- Markdown uses `native_payload["token_type"]`; ignore duplicate `inline` tokens when a mapped block token already covers the same source range.
- PDF groups positioned spans using existing `group_visual_regions()` / `group_visual_lines()`.
- Run terminal/table detection per visual region, not across the whole document.
- Run formula detection only on glyph evidence and accept a formula only when `"math_glyph_shape" in candidate.detection_basis`.
- Build figure candidates from positioned asset evidence.
- Mark detector-consumed evidence refs so fallback paragraph blocks do not duplicate them.
- Remaining visual lines use `classify_block()`; if no registered resolved role is above threshold, use `text.paragraph`.
- Every produced unit has stable order, parent_ref, evidence refs, and provenance_ref.
- Root uses the first source-significant evidence ref for source accountability.

Structured candidates are serialized into `unit.properties` under exact keys `table_candidate`, `formula_candidate`, or `figure_candidate`.

- [ ] **Step 6: Run production + existing reconstruction tests**

```bash
uv run pytest   tests/unit/reconstruction/test_production.py   tests/unit/reconstruction   tests/regression/test_structured_reconstruction.py   tests/regression/test_cross_page_reconstruction.py -v
```

Expected: new tests PASS; existing tests unchanged.

- [ ] **Step 7: Commit**

```bash
git add src/voxcodex/config/m2-pipeline-v0.1.json   src/voxcodex/reconstruction/production.py   src/voxcodex/materialization/mappings.py   tests/unit/reconstruction/test_production.py
git commit -m "feat: add production m2 reconstruction stage"
```

---

### Task 4: Implement M2PipelineProcessor End to End

**Files:**
- Create: `src/voxcodex/corpus/m2_pipeline.py`
- Modify: `src/voxcodex/materialization/builder.py`
- Create: `tests/integration/corpus/test_m2_pipeline_processor.py`

**Interfaces:**
- Consumes: `HoldoutExecutionSpec`, `ProductionEvidenceStage`, existing PDF/Markdown adapters, `ReconstructionEngine`, `build_canonical_draft`, `validate_revision`, `freeze_revision`.
- Produces: `M2PipelineProcessor(work_root: Path)`
- Produces: `M2PipelineProcessor.process(spec: HoldoutExecutionSpec, source_path: Path) -> HoldoutCaseRun`
- Produces: `HoldoutCaseRun` with explicit stage refs, validation result, accountability, and `ResultClass`.

- [ ] **Step 1: Write synthetic end-to-end RED tests**

Create a tiny PDF with PyMuPDF and Markdown fixtures in `tmp_path`.

```python
def test_synthetic_pdf_runs_evidence_reconstruction_materialization_validation(tmp_path: Path):
    source = _make_pdf(tmp_path / "sample.pdf", ["Heading", "Body paragraph"])
    spec = _pdf_spec(source, page_indexes=(0,))
    result = M2PipelineProcessor(tmp_path / "work").process(spec, source)

    assert result.result_class == "PASS"
    assert result.evidence_snapshot_ref
    assert result.reconstruction_snapshot_ref
    assert result.canonical_revision_ref
    assert result.validation_result == "PASS"
    assert result.frozen_revision_digest


def test_synthetic_markdown_runs_same_orchestration_surface(tmp_path: Path):
    source = tmp_path / "sample.md"
    source.write_text("# Heading\n\nBody.\n", encoding="utf-8")
    result = M2PipelineProcessor(tmp_path / "work").process(_md_spec(source), source)
    assert result.result_class == "PASS"
    assert result.canonical_revision_ref


def test_zip_member_is_exact_and_member_digest_is_verified(tmp_path: Path):
    archive = _make_zip(
        tmp_path / "book.zip",
        {"book/src/a.md": "# A\n", "book/src/b.md": "# B\n"},
    )
    spec = _zip_spec(archive, member="book/src/b.md")
    result = M2PipelineProcessor(tmp_path / "work").process(spec, archive)
    assert result.result_class == "PASS"
    assert result.selected_scope["zip_member_path"] == "book/src/b.md"
```

Also add tests:
- container SHA mismatch → `PROCESSING_FAILURE`;
- member SHA mismatch → `PROCESSING_FAILURE`;
- materialization issue → `MODEL_GAP` + schema-evolution observation;
- validation FAIL → `MODEL_FAILURE`;
- significant unused Evidence → not PASS;
- identical input/config → identical semantic output digests.

- [ ] **Step 2: Run RED**

```bash
uv run pytest tests/integration/corpus/test_m2_pipeline_processor.py -v
```

Expected: missing processor.

- [ ] **Step 3: Extend builder to accept source anchors without changing existing callers**

Change signature:

```python
def build_canonical_draft(
    *,
    reconstruction_snapshot_digest: str,
    units: tuple[ReconstructionUnit, ...],
    target_context: CanonicalTargetContext,
    role_mappings: RoleMappingRegistry,
    source_anchor_refs_by_unit: Mapping[str, tuple[str, ...]] | None = None,
) -> CanonicalDraft:
```

When constructing each node:

```python
source_anchor_refs=(
    source_anchor_refs_by_unit.get(unit.id, ())
    if source_anchor_refs_by_unit is not None
    else ()
),
```

Existing tests must remain byte/semantic compatible when the new argument is omitted.

- [ ] **Step 4: Implement exact-source preparation**

In `m2_pipeline.py`:

```python
def _verify_source(spec: HoldoutExecutionSpec, source_path: Path) -> bytes:
    data = source_path.read_bytes()
    if sha256_bytes(data) != spec.source_sha256:
        raise SourceIdentityError("source digest does not match frozen holdout identity")
    return data
```

For ZIP:

```python
with ZipFile(source_path) as archive:
    member_bytes = archive.read(spec.zip_member_path)
if sha256_bytes(member_bytes) != spec.zip_member_sha256:
    raise SourceIdentityError("selected Markdown member digest mismatch")
if len(member_bytes) != spec.zip_member_byte_size:
    raise SourceIdentityError("selected Markdown member byte size mismatch")
```

Do not discover or choose another member.

- [ ] **Step 5: Implement Evidence and Reconstruction**

Use one content-addressed `LocalBlobStore` under the processor work root.

PDF:

```python
profile = ExtractionProfile(
    id="extraction-profile:m2-pipeline:pdf:v0.1",
    adapter="pdf",
    adapter_version=PdfAdapter.adapter_version,
    options={"glyph_runs": True},
)
snapshot = adapter.extract(source, source_path, profile, page_indexes=spec.selected_page_indexes)
```

Markdown uses `MarkdownAdapter` over the exact file/member.

Load all EvidenceUnits from produced partitions, then:

```python
stage = ProductionEvidenceStage(evidence_units, production_reconstruction_profile())
engine = ReconstructionEngine(
    stages=(stage,),
    blob_store=blob_store,
    metadata_store=metadata_store,
)
reconstruction = engine.assemble(
    snapshot,
    reconstruction_profile_ref="reconstruction-profile:m2-production:v0.1",
)
payload = engine.load_snapshot_payload(reconstruction)
```

- [ ] **Step 6: Materialize source anchors and structured payloads**

For each `ReconstructionUnit.evidence_refs`, look up the exact EvidenceUnit and build `AnchorEvidence` from its frozen source locator/geometry.

Use:

```python
anchors = build_source_anchors(node_ref, tuple(anchor_inputs))
source_anchor_refs_by_unit[unit.id] = tuple(anchor.id for anchor in anchors)
```

Materialize structured payloads from the serialized candidates in unit properties:

```python
table = TableCandidate.model_validate(unit.properties["table_candidate"])
table_payload = materialize_table_payload(table, content_refs_by_evidence={})
formula = FormulaCandidate.model_validate(unit.properties["formula_candidate"])
formula_payload = materialize_formula_payload(formula)
```

Figures remain canonical asset nodes in v0.1; do not invent a new payload model.

- [ ] **Step 7: Build deterministic CanonicalRevision and validate/freeze**

Create deterministic registry refs from `shard_registry_objects()` and canonical JSON digests. Build a `CanonicalRevision` in `validated` lifecycle with:

- schema_version `"0.1"`;
- root_node_ref from the unique root;
- source_mapping_manifest_ref derived from anchors;
- provenance_manifest_ref derived from node provenance;
- structured payload registry ref derived from table/formula payloads.

Construct evidence accountability:

```python
EvidenceAccountability(
    evidence_ref=unit.id,
    significance=_significance(unit),
    classification=_classification(unit, canonicalized_evidence_ids),
    canonical_ref=canonical_ref_by_evidence.get(unit.id),
)
```

Rules:

- `physical_page` and layout-only `region` → `non_significant/intentionally_noncanonical`;
- source text/syntax/assets → significant;
- duplicate glyph evidence not selected for formula → `non_significant/intentionally_noncanonical`;
- significant evidence used by a materialized node → `canonicalized`;
- significant evidence not represented → `suspected_loss`.

Validate with `m2_poc_strict()`. Only `ValidationReport.result == "PASS"` may call `freeze_revision()`.

- [ ] **Step 8: Implement explicit result classification**

Order:

```python
if source_or_runtime_failure:
    result_class = "PROCESSING_FAILURE"
elif draft.issues:
    result_class = "MODEL_GAP"
elif any(significant suspected_loss):
    result_class = "MODEL_FAILURE"
elif validation_report.result != "PASS":
    result_class = "MODEL_FAILURE"
else:
    result_class = "PASS"
```

`PASS_WITH_EXTENSION` is emitted only when an explicitly recorded allowed extension exists; do not emit it by default.

A `MODEL_GAP` creates `SchemaEvolutionObservation` and does not change CBM v0.1.

- [ ] **Step 9: Run GREEN plus materialization/validation regression**

```bash
uv run pytest   tests/integration/corpus/test_m2_pipeline_processor.py   tests/unit/materialization   tests/unit/validation   tests/regression/test_materialization_known_cases.py -v
```

Expected: PASS except existing local-corpus skips.

- [ ] **Step 10: Commit**

```bash
git add src/voxcodex/corpus/m2_pipeline.py   src/voxcodex/materialization/builder.py   tests/integration/corpus/test_m2_pipeline_processor.py
git commit -m "feat: add end-to-end m2 pipeline processor"
```

---

### Task 5: Add Auditable `corpus run-holdouts` CLI

**Files:**
- Modify: `src/voxcodex/corpus/holdout_execution.py`
- Modify: `src/voxcodex/cli.py`
- Create: `tests/integration/cli/test_holdout_run_cli.py`

**Interfaces:**
- Consumes: `verify_holdout_preflight()`, `M2PipelineProcessor.process()`.
- Produces: `HoldoutRunReport`
- Produces CLI: `voxcodex corpus run-holdouts`
- Output is exclusive-create JSON and cannot overwrite prior blind evidence.

- [ ] **Step 1: Write RED CLI tests with synthetic repository**

```python
def test_run_holdouts_fails_before_source_io_without_reveal(tmp_path: Path):
    repo = _synthetic_repo(tmp_path, with_reveal=False)
    result = runner.invoke(app, _run_holdouts_args(repo))
    assert result.exit_code != 0
    assert "reveal" in result.output
    assert repo.source_open_count == 0


def test_run_holdouts_writes_auditable_report_for_synthetic_holdouts(tmp_path: Path):
    repo = _synthetic_repo(tmp_path, with_reveal=True)
    result = runner.invoke(app, _run_holdouts_args(repo))
    assert result.exit_code == 0, result.output
    report = json.loads((repo.root / "blind-report.json").read_text())
    assert report["candidate_id"] == "m2-implementation-candidate-v2"
    assert report["cases"][0]["result_class"] == "PASS"


def test_run_holdouts_refuses_to_overwrite_existing_report(tmp_path: Path):
    repo = _synthetic_repo(tmp_path, with_reveal=True)
    (repo.root / "blind-report.json").write_text("{}\n")
    result = runner.invoke(app, _run_holdouts_args(repo))
    assert result.exit_code != 0
    assert "already exists" in result.output
```

- [ ] **Step 2: Run RED**

```bash
uv run pytest tests/integration/cli/test_holdout_run_cli.py -v
```

Expected: command missing.

- [ ] **Step 3: Implement immutable report models**

Add:

```python
class HoldoutCaseReport(FrozenModel):
    holdout_id: str
    corpus_case_id: str
    selected_scope: dict[str, object]
    source_digest_verified: bool
    evidence_snapshot_ref: str | None = None
    evidence_snapshot_digest: str | None = None
    reconstruction_snapshot_ref: str | None = None
    reconstruction_snapshot_digest: str | None = None
    canonical_revision_ref: str | None = None
    frozen_revision_digest: str | None = None
    validation_report_ref: str | None = None
    validation_result: str | None = None
    evidence_accountability: tuple[EvidenceAccountability, ...] = ()
    result_class: ResultClass
    diagnostic: str
    evolution_observation: SchemaEvolutionObservation | None = None


class HoldoutRunReport(FrozenModel):
    candidate_id: str
    candidate_digest: str
    holdout_freeze_digest: str
    reveal_version: str
    cases: tuple[HoldoutCaseReport, ...]
```

- [ ] **Step 4: Implement CLI with preflight before every source path resolution**

CLI signature:

```text
voxcodex corpus run-holdouts
  --repo-root .
  --candidate M2-IMPLEMENTATION-CANDIDATE-V2.json
  --regression-report planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json
  --selection-manifest corpus/manifests/M2-BLIND-HOLDOUT-SELECTION-V1.json
  --holdout-manifest M2-HOLDOUT-V1-FREEZE-MANIFEST.json
  --reveal-record M2-HOLDOUT-REVEAL-V1.json
  --registry corpus/COMPATIBILITY-CORPUS-V1.json
  --output planning/M2-HOLDOUT-RUN-V1.json
```

For each frozen holdout:

```python
spec = verify_holdout_preflight(...)
source_path = repo_root / spec.source_relative_path
case_run = processor.process(spec, source_path)
```

The path is not read before `verify_holdout_preflight` returns.

Write output with `Path.open("x")`.

- [ ] **Step 5: Run GREEN and all CLI tests**

```bash
uv run pytest tests/integration/cli -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/voxcodex/corpus/holdout_execution.py src/voxcodex/cli.py   tests/integration/cli/test_holdout_run_cli.py
git commit -m "feat: add auditable blind holdout runner cli"
```

---

### Task 6: Run the Complete Pre-Freeze Regression Gate

**Files:**
- Modify: `src/voxcodex/corpus/candidate.py`
- Create: `planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json`
- Create: `planning/M2-HOLDOUT-EXECUTOR-GATE.md`
- Modify: `.github/workflows/m2-plan02-ci.yml`

**Interfaces:**
- Candidate semantic configs now include `m2_pipeline`.
- Candidate processors now include `m2_pipeline_processor` and `production_reconstruction_stage`.
- CI generates V2 only while V2 file is absent.

- [ ] **Step 1: Bind the pipeline config and processor versions**

In `build_repository_candidate`, add:

```python
semantic_config_digests["m2_pipeline"] = _file_digest(
    repo_root / "src/voxcodex/config/m2-pipeline-v0.1.json"
)
processor_versions.update({
    "production_reconstruction_stage": "0.1.0",
    "m2_pipeline_processor": "0.1.0",
})
```

These values are frozen into V2.

- [ ] **Step 2: Extend CI pre-freeze gate**

The corpus gate must include:

```bash
uv run pytest   tests/unit/corpus/test_candidate_v2.py   tests/unit/corpus/test_holdout_execution.py   tests/unit/corpus/test_holdout_reveal.py   tests/unit/reconstruction/test_production.py   tests/integration/corpus/test_m2_pipeline_processor.py   tests/integration/cli/test_holdout_run_cli.py   tests/corpus   tests/regression/test_frozen_assertions.py -v
```

Do not invoke real `holdouts reveal` or `corpus run-holdouts`.

- [ ] **Step 3: Run the full repository workflow**

Required green gates:

```text
Plan 01
Evidence implementation
Evidence CLI
quarantine regression
Reconstruction implementation
Reconstruction plan gate
CBM contracts
Materialization / Validation
Canonical implementation
canonical trace
Execution
Corpus / candidate / holdout executor
```

Existing local physical-corpus skips remain explicit and are not counted as physical PASS.

- [ ] **Step 4: Write V2 pre-freeze report from actual green run IDs**

`planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json` must include:

```json
{
  "status": "PASS_WITH_LOCAL_CORPUS_WAIVER",
  "selective_reprocessing_status": "PASS",
  "holdout_executor_status": "PASS_SYNTHETIC_ONLY",
  "real_holdout_sources_accessed": false,
  "holdouts_withheld": ["CC-05", "CC-07", "CC-14", "CC-18"],
  "candidate_target": "m2-implementation-candidate-v2",
  "evidence_runs": {}
}
```

Populate `evidence_runs` with the actual workflow run IDs from this task, not planned values.

- [ ] **Step 5: Write gate document**

`planning/M2-HOLDOUT-EXECUTOR-GATE.md` must state:

- production executor exists;
- synthetic PDF, Markdown and Markdown-ZIP are green;
- V1 is superseded pre-reveal but immutable;
- four real holdouts remain untouched;
- next candidate is V2;
- no blind result exists yet;
- reveal remains irreversible and pending.

- [ ] **Step 6: Commit pre-freeze evidence**

```bash
git add src/voxcodex/corpus/candidate.py .github/workflows/m2-plan02-ci.yml   planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json   planning/M2-HOLDOUT-EXECUTOR-GATE.md
git commit -m "chore: close m2 holdout executor prefreeze gate"
```

- [ ] **Step 7: Run CI once more on the exact pre-freeze commit**

Expected: full SUCCESS. Record this commit SHA as the V2 implementation SHA.

---

### Task 7: Freeze Candidate V2 and Convert CI to Verify-Only

**Files:**
- Create: `M2-IMPLEMENTATION-CANDIDATE-V2.json`
- Modify: `.github/workflows/m2-plan02-ci.yml`
- Modify: `planning/M2-HOLDOUT-EXECUTOR-GATE.md`
- Test: existing candidate/reveal/preflight suites.

**Interfaces:**
- Produces immutable candidate id `m2-implementation-candidate-v2`.
- Produces a new candidate digest bound to the final pre-freeze implementation SHA and semantic implementation-tree digest.
- CI thereafter requires V2 and only verifies it.

- [ ] **Step 1: Generate candidate V2 from the exact green pre-freeze commit**

Run in CI or equivalent reproducible environment:

```bash
uv run voxcodex candidate freeze   --repo-root .   --regression-report planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json   --git-commit-sha "$PREFREEZE_SHA"   --candidate-id m2-implementation-candidate-v2   --output /tmp/M2-IMPLEMENTATION-CANDIDATE-V2.json
```

Capture the exact generated bytes and candidate digest.

- [ ] **Step 2: Verify candidate contains every required binding**

Assert:

```python
payload["candidate_id"] == "m2-implementation-candidate-v2"
payload["git_commit_sha"] == PREFREEZE_SHA
payload["implementation_tree_digest"]
payload["semantic_config_digests"]["m2_pipeline"]
payload["processor_versions"]["m2_pipeline_processor"] == "0.1.0"
payload["processor_versions"]["production_reconstruction_stage"] == "0.1.0"
payload["holdouts_withheld"] == ["CC-05", "CC-07", "CC-14", "CC-18"]
```

- [ ] **Step 3: Commit the exact generated candidate without regenerating**

```bash
git add M2-IMPLEMENTATION-CANDIDATE-V2.json
git commit -m "release: freeze m2 implementation candidate v2"
```

Do not modify V1.

- [ ] **Step 4: Change CI from generation fallback to mandatory V2 verification**

Final workflow step:

```bash
test -f M2-IMPLEMENTATION-CANDIDATE-V2.json
uv run voxcodex candidate verify   --repo-root .   --regression-report planning/M2-PREFREEZE-REGRESSION-REPORT-V2.json   --candidate M2-IMPLEMENTATION-CANDIDATE-V2.json
```

There is no generation branch and no V1 fallback.

- [ ] **Step 5: Run final pre-reveal CI**

Run all workflow gates. Expected: SUCCESS and candidate verification prints the exact V2 digest and frozen implementation SHA.

- [ ] **Step 6: Update gate document with final V2 identity**

Record:

- V2 candidate digest;
- V2 implementation SHA;
- candidate-file commit SHA;
- final verification workflow run ID;
- `real_holdout_sources_accessed: false`;
- reveal state: `FROZEN_UNREVEALED`.

- [ ] **Step 7: Commit final pre-reveal gate**

```bash
git add .github/workflows/m2-plan02-ci.yml planning/M2-HOLDOUT-EXECUTOR-GATE.md
git commit -m "ci: lock m2 blind evaluation to candidate v2"
```

- [ ] **Step 8: Verify once more and stop**

Run:

```bash
uv run pytest   tests/unit/corpus/test_holdout_reveal.py   tests/unit/corpus/test_holdout_execution.py   tests/integration/cli/test_holdout_run_cli.py   tests/integration/cli/test_candidate_cli.py -v
```

Then the full GitHub workflow.

Expected final state:

```text
candidate V2: FROZEN / VERIFIED
holdout reveal record: ABSENT
CC-05: FROZEN / UNREVEALED
CC-07: FROZEN / UNREVEALED
CC-14: FROZEN / UNREVEALED
CC-18: FROZEN / UNREVEALED
next irreversible action: REVEAL_M2_HOLDOUTS_V1
```

Do **not** perform the reveal in this task.
