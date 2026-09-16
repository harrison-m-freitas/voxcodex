# M2.2 Source Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement immutable SourceProfile/EvidenceSnapshot generation for Tier 1 textual PDFs and Markdown while preserving physical/syntactic evidence without assigning canonical document semantics.

**Architecture:** Adapters emit format-neutral EvidenceUnits wrapped in immutable partition artifacts, plus native payloads when needed. PDF uses PyMuPDF for page/text/glyph/layout/image evidence; Markdown uses markdown-it-py tokens plus exact character/byte ranges. Evidence is partitioned so page/file outputs can be reused independently.

**Tech Stack:** Foundation stack plus PyMuPDF 1.28.x and markdown-it-py 4.2.x.

**Spec:** `architecture/M2-DESIGN-V0.1.md` M2.2 (E01–E10).

## Global Constraints

- Evidence records observation/syntax, not canonical roles such as paragraph, heading, speech, table, or formula.
- `text_layer_present` does not imply authoritative text.
- Preserve native geometry and normalized geometry where available.
- Evidence confidence qualifies extraction/observation only.
- No OCR in M2 Tier 1 evidence implementation.
- Quarantined cases cannot be used by adapter tests.

---

### Task 1: Define Evidence physical models and partition manifest

**Files:**
- Create: `src/voxcodex/domain/evidence.py`
- Test: `tests/unit/domain/test_evidence_contracts.py`

**Interfaces:**
- Produces `EvidenceClass`, `NativeGeometry`, `NormalizedGeometry`, `EvidenceUnit`, `EvidencePartition`, `EvidenceSnapshot`, `ExtractionProfile`.
- `EvidenceSnapshot.partition_refs` references immutable partition artifacts.

- [ ] **Step 1: Write failing contract tests**

Assert `EvidenceUnit` accepts classes `physical_page`, `region`, `line`, `text_span`, `glyph_run`, `asset`, `syntax_unit`, rejects `paragraph`, and has no canonical `role` field.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/domain/test_evidence_contracts.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement frozen evidence models**

Use `source_locator`, optional `surface`, `presentation`, `native_payload`, optional `confidence_ref`, and `provenance_ref` exactly as separate fields; normalized geometry values are finite floats in `[0,1]`.

- [ ] **Step 4: Add invalid-geometry property tests**

Hypothesis generates NaN/Inf/out-of-range normalized coordinates and validation must reject them.

Run: `uv run pytest tests/unit/domain/test_evidence_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/domain/evidence.py tests/unit/domain/test_evidence_contracts.py
git commit -m "feat: define source evidence contracts"
```

### Task 2: Define adapter protocol and SourceProfile inspection

**Files:**
- Create: `src/voxcodex/adapters/base.py`
- Create: `src/voxcodex/adapters/pdf.py`
- Create: `src/voxcodex/adapters/markdown.py`
- Test: `tests/unit/adapters/test_profiles.py`

**Interfaces:**
- Produces protocol `SourceAdapter.inspect(source: SourceArtifact, bytes_path: Path) -> SourceProfile`.
- Produces `PdfAdapter` and `MarkdownAdapter` profile inspection.

- [ ] **Step 1: Write failing synthetic profile tests**

Generate a 2-page PDF with PyMuPDF containing one text page and one image-only page; assert `page_count=2`, `text_layer_present=True`, and mixed coverage characteristics. Create UTF-8 Markdown and assert encoding/heading/code-fence hints.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/adapters/test_profiles.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement inspection without deep semantic extraction**

PDF inspection may count text characters/images/fonts/rotations per page. Markdown inspection may detect encoding, line endings, and syntax feature presence. `recommended_routes` is operational only.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/adapters/test_profiles.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/adapters tests/unit/adapters/test_profiles.py
git commit -m "feat: add source profile inspection"
```

### Task 3: Implement PDF Evidence extraction by page

**Files:**
- Modify: `src/voxcodex/adapters/pdf.py`
- Test: `tests/integration/adapters/test_pdf_evidence.py`
- Create: `tests/fixtures/pdf_factory.py`

**Interfaces:**
- Produces `PdfAdapter.extract(source, path, profile, page_indexes: Sequence[int] | None) -> EvidenceSnapshot`.
- Each physical PDF page becomes one immutable `EvidencePartition` artifact.

- [ ] **Step 1: Write failing PDF evidence test**

Synthetic PDF must include bold text, normal text, two columns, an embedded image, and superscript-positioned glyphs. Assert source text, font/presentation, geometry, image asset, and glyph-run evidence are preserved; assert no `text.paragraph` or `text.heading` role appears.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/adapters/test_pdf_evidence.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement extraction**

Use PyMuPDF `page.get_text("dict")`/raw structures for spans and `page.get_texttrace()` only when glyph-level evidence is requested by extraction profile. Preserve native PDF coordinates and compute normalized boxes from page dimensions. Embedded images become asset evidence with extracted bytes stored in BlobStore.

- [ ] **Step 4: Add deterministic snapshot test**

Extract the same PDF twice with identical profile and assert equal partition semantic digests and equal snapshot semantic digest; activity IDs may differ. Then extract with a second valid profile and assert both immutable EvidenceSnapshots coexist without overwriting one another.

Run: `uv run pytest tests/integration/adapters/test_pdf_evidence.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/adapters/pdf.py tests/integration/adapters/test_pdf_evidence.py tests/fixtures/pdf_factory.py
git commit -m "feat: extract inspectable pdf evidence"
```

### Task 4: Implement Markdown Evidence with exact source ranges

**Files:**
- Modify: `src/voxcodex/adapters/markdown.py`
- Test: `tests/integration/adapters/test_markdown_evidence.py`

**Interfaces:**
- Produces syntax-unit EvidenceUnits with raw source range, token type, delimiter/native payload, and surface text.

- [ ] **Step 1: Write failing source-preservation test**

Input:

````markdown
## Prólogo

*O ar está pesado.*

```python
print("x")
```
````

Assert heading syntax, emphasis syntax, code fence, exact original source slices, and no `narrative.prologue` role.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/adapters/test_markdown_evidence.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement markdown-it-py token extraction plus source mapper**

Build line-offset indexes from original bytes/text so token map line ranges resolve back to raw source. Preserve delimiters in `native_payload` when the parser exposes them; otherwise preserve the complete raw slice.

- [ ] **Step 4: Add CRLF/LF equivalence-with-distinct-evidence test**

Two files with identical rendered semantics but different line endings must yield different raw source digests while both parse to compatible syntax evidence.

Run: `uv run pytest tests/integration/adapters/test_markdown_evidence.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/adapters/markdown.py tests/integration/adapters/test_markdown_evidence.py
git commit -m "feat: extract markdown syntax evidence"
```

### Task 5: Add ingestion/evidence CLI and safe regression-slice smoke tests

**Files:**
- Modify: `src/voxcodex/cli.py`
- Create: `tests/integration/cli/test_evidence_cli.py`
- Create: `tests/regression/test_evidence_known_slices.py`

**Interfaces:**
- CLI: `voxcodex ingest PATH`.
- CLI: `voxcodex evidence build SOURCE_ID --adapter pdf|markdown --scope ...`.
- CLI: `voxcodex evidence show SNAPSHOT_ID`.

- [ ] **Step 1: Write failing CLI tests using synthetic sources**

Assert ingest returns a source ID and evidence build prints snapshot digest and partition count.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/cli/test_evidence_cli.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement CLI commands through application services**

CLI must never read corpus source paths directly; corpus case resolution routes through `HoldoutGuard`.

- [ ] **Step 4: Add regression evidence checks for non-holdout historical cases**

Use F1/W1/C1/C3 known slices to assert text/presentation/geometry/assets required by frozen assertions are physically available. Do not assert reconstruction roles here.

Run: `uv run pytest tests/regression/test_evidence_known_slices.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/cli.py tests/integration/cli tests/regression/test_evidence_known_slices.py
git commit -m "feat: expose tier1 evidence pipeline"
```

### Task 6: Evidence gate

**Files:**
- Create: `planning/M2-IMPLEMENTATION-EVIDENCE-GATE.md`

**Interfaces:**
- Produces recorded commands/digests for the Evidence gate without opening holdouts.

- [ ] **Step 1: Run unit/integration/regression evidence suite**

Run: `uv run pytest tests/unit/domain/test_evidence_contracts.py tests/unit/adapters tests/integration/adapters tests/regression/test_evidence_known_slices.py -v`
Expected: PASS.

- [ ] **Step 2: Run quarantine regression**

Run: `uv run pytest tests/unit/corpus/test_quarantine.py tests/integration/corpus -v`
Expected: PASS.

- [ ] **Step 3: Record versions and snapshot digests in the gate report**

Record Python, PyMuPDF, markdown-it-py versions and semantic digests from the known-slice run; do not record holdout source content or derived output.

- [ ] **Step 4: Commit**

```bash
git add planning/M2-IMPLEMENTATION-EVIDENCE-GATE.md
git commit -m "docs: record m2 evidence implementation gate"
```
