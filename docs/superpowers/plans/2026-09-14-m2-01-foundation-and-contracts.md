# M2.1 Foundation and Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the executable M2 foundation: Python project, immutable artifact store, deterministic digests/IDs, physical domain contracts, transactional metadata DAG, CLI, and blind-holdout guard.

**Architecture:** Use canonical JSON artifacts in a content-addressed filesystem and keep operational indexes/dependency edges in SQLite through SQLAlchemy Core. Domain payloads are Pydantic frozen models; immutable payload IDs/digests are semantic, while execution events use UUIDv7.

**Tech Stack:** Python 3.14.x, uv 0.12.x, Pydantic 2.13.x, RFC 8785 (`rfc8785==0.1.4`), SQLAlchemy 2.0.x, Alembic 1.20.x, Typer 0.27.x, pytest 9.1.x, Hypothesis 6.168+.

**Spec:** `architecture/M2-DESIGN-V0.1.md` sections M2.1, M2.2 common contracts, M2.5 provenance authority corrections.

## Global Constraints

- Do not read quarantined source bytes: `CC-05`, `CC-07`, `CC-14`, `CC-18`.
- Domain models use `ConfigDict(frozen=True, extra="forbid")`.
- SHA-256 addresses immutable blobs. RFC 8785 canonical JSON is used for semantic JSON hashing.
- UUIDv7 is for operational event identity; deterministic UUIDv5 is used for stable in-snapshot object keys from explicit seeds.
- `ProcessingActivity` has no normative causal input/output ownership; `Derivation` owns causal refs.

---

### Task 1: Bootstrap the Python package and quality commands

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/voxcodex/__init__.py`
- Create: `src/voxcodex/cli.py`
- Create: `tests/unit/test_package_smoke.py`
- Create: `.gitignore`

**Interfaces:**
- Produces CLI entry point: `voxcodex = voxcodex.cli:app`.
- Produces package version constant: `voxcodex.__version__`.

- [ ] **Step 1: Write the failing smoke test**

```python
from voxcodex import __version__
from voxcodex.cli import app


def test_package_exports_version_and_cli():
    assert __version__ == "0.1.0"
    assert app.info.name == "voxcodex"
```

- [ ] **Step 2: Run the test and verify import failure**

Run: `uv run pytest tests/unit/test_package_smoke.py -v`
Expected: FAIL because `voxcodex` does not exist.

- [ ] **Step 3: Add project metadata and minimal implementation**

`.python-version` must contain `3.14.7`. `pyproject.toml` must declare Python `>=3.14,<3.15`, dependencies `pydantic>=2.13,<2.14`, `rfc8785==0.1.4`, `sqlalchemy>=2.0.52,<2.1`, `alembic>=1.20,<1.21`, `typer>=0.27,<0.28`, and dev dependencies `pytest>=9.1,<9.2`, `hypothesis>=6.168`.

```python
# src/voxcodex/__init__.py
__version__ = "0.1.0"
```

```python
# src/voxcodex/cli.py
import typer

app = typer.Typer(name="voxcodex", no_args_is_help=True)
```

- [ ] **Step 4: Lock and run the smoke test**

Run: `uv lock && uv run pytest tests/unit/test_package_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version uv.lock .gitignore src/voxcodex tests/unit/test_package_smoke.py
git commit -m "build: bootstrap voxcodex m2 package"
```

### Task 2: Implement canonical JSON, SHA-256 digests, and deterministic IDs

**Files:**
- Create: `src/voxcodex/digests.py`
- Create: `src/voxcodex/ids.py`
- Test: `tests/unit/test_digests.py`
- Test: `tests/unit/test_ids.py`

**Interfaces:**
- Produces: `canonical_json_bytes(value: object) -> bytes`.
- Produces: `sha256_bytes(data: bytes) -> str`.
- Produces: `semantic_digest(model: BaseModel, exclude: set[str] = frozenset()) -> str`.
- Produces: `stable_uuid(namespace: UUID, seed: str) -> UUID` and `new_event_id() -> UUID`.

- [ ] **Step 1: Write failing canonicalization tests**

```python
from voxcodex.digests import canonical_json_bytes, sha256_bytes


def test_canonical_json_ignores_mapping_order():
    assert canonical_json_bytes({"b": 2, "a": 1}) == canonical_json_bytes({"a": 1, "b": 2})


def test_sha256_is_lowercase_hex():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `uv run pytest tests/unit/test_digests.py tests/unit/test_ids.py -v`
Expected: FAIL because functions do not exist.

- [ ] **Step 3: Implement RFC 8785 canonicalization and IDs**

```python
# src/voxcodex/digests.py
import hashlib
import math
import rfc8785
from pydantic import BaseModel


def canonical_json_bytes(value: object) -> bytes:
    return rfc8785.dumps(value)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_digest(model: BaseModel, exclude: set[str] | frozenset[str] = frozenset()) -> str:
    payload = model.model_dump(mode="json", exclude=set(exclude), exclude_none=True)
    return sha256_bytes(canonical_json_bytes(payload))
```

```python
# src/voxcodex/ids.py
import uuid

VOXCODEX_NAMESPACE = uuid.UUID("66f24fa1-7695-5e5c-b6da-72d21d02ab35")


def stable_uuid(namespace: uuid.UUID, seed: str) -> uuid.UUID:
    return uuid.uuid5(namespace, seed)


def new_event_id() -> uuid.UUID:
    return uuid.uuid7()
```

- [ ] **Step 4: Add property test for canonical order**

```python
from hypothesis import given, strategies as st
from voxcodex.digests import canonical_json_bytes

@given(st.dictionaries(st.text(min_size=1), st.integers(), max_size=20))
def test_canonical_json_is_stable_for_reversed_items(mapping):
    reversed_mapping = dict(reversed(list(mapping.items())))
    assert canonical_json_bytes(mapping) == canonical_json_bytes(reversed_mapping)
```

Run: `uv run pytest tests/unit/test_digests.py tests/unit/test_ids.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/digests.py src/voxcodex/ids.py tests/unit/test_digests.py tests/unit/test_ids.py
git commit -m "feat: add deterministic digest and id primitives"
```

### Task 3: Implement immutable blob storage

**Files:**
- Create: `src/voxcodex/storage/blobs.py`
- Test: `tests/unit/storage/test_blobs.py`

**Interfaces:**
- Produces `BlobRef(sha256: str, byte_size: int)`.
- Produces `LocalBlobStore.put_bytes(data: bytes) -> BlobRef`.
- Produces `LocalBlobStore.read_bytes(ref: BlobRef) -> bytes`.
- Produces `LocalBlobStore.import_file(path: Path) -> BlobRef`.

- [ ] **Step 1: Write failing immutability/deduplication tests**

```python
from pathlib import Path
from voxcodex.storage.blobs import LocalBlobStore


def test_same_bytes_deduplicate(tmp_path: Path):
    store = LocalBlobStore(tmp_path / "blobs")
    a = store.put_bytes(b"same")
    b = store.put_bytes(b"same")
    assert a == b
    assert store.read_bytes(a) == b"same"
```

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/storage/test_blobs.py -v`
Expected: FAIL because storage implementation does not exist.

- [ ] **Step 3: Implement content-addressed paths**

Use `<root>/sha256/<first2>/<remaining62>`; write via temporary file + `os.replace`; if destination already exists, compare byte size and return the existing blob without rewriting it.

- [ ] **Step 4: Add corruption detection test and run suite**

The test must manually replace a blob with different bytes and assert `BlobIntegrityError` on read.

Run: `uv run pytest tests/unit/storage/test_blobs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/storage/blobs.py tests/unit/storage/test_blobs.py
git commit -m "feat: add immutable content addressed blob store"
```

### Task 4: Define physical common/source/processing contracts

**Files:**
- Create: `src/voxcodex/domain/common.py`
- Create: `src/voxcodex/domain/source.py`
- Create: `src/voxcodex/domain/processing.py`
- Test: `tests/unit/domain/test_common_contracts.py`
- Test: `tests/unit/domain/test_processing_authority.py`

**Interfaces:**
- Produces `ArtifactRef`, `Confidence`, `SourceArtifact`, `SourceProfile`, `ProcessorIdentity`, `ProcessingActivity`, `Derivation`, `UsageRecord`.
- `Derivation.input_refs/output_refs` are normative causal edges.

- [ ] **Step 1: Write failing authority test**

```python
from voxcodex.domain.processing import ProcessingActivity, Derivation


def test_processing_activity_does_not_own_causal_edges():
    assert "input_refs" not in ProcessingActivity.model_fields
    assert "output_refs" not in ProcessingActivity.model_fields
    assert "input_refs" in Derivation.model_fields
    assert "output_refs" in Derivation.model_fields
```

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/domain/test_common_contracts.py tests/unit/domain/test_processing_authority.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement frozen models**

All models inherit a shared `FrozenModel` configured with `ConfigDict(frozen=True, extra="forbid")`. `Confidence` fields are `value`, `scale`, `basis`, `producer_ref`, optional `calibration_ref`; no document-wide confidence field exists.

- [ ] **Step 4: Add JSON round-trip tests**

Serialize with `model_dump_json()`, validate back with `model_validate_json()`, and assert equality for each contract.

Run: `uv run pytest tests/unit/domain -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/domain tests/unit/domain
git commit -m "feat: add m2 source and provenance contracts"
```

### Task 5: Add SQLite metadata store and dependency DAG

**Files:**
- Create: `src/voxcodex/storage/schema.py`
- Create: `src/voxcodex/storage/metadata.py`
- Create: `src/voxcodex/storage/migrations/env.py`
- Create: `src/voxcodex/storage/migrations/versions/0001_m2_metadata.py`
- Test: `tests/integration/storage/test_metadata_store.py`

**Interfaces:**
- Produces `MetadataStore.register_artifact(record)`, `register_activity(activity)`, `register_derivation(derivation)`, `get_downstream(ref) -> set[ArtifactRef]`.
- Persists artifact metadata only; immutable payload bytes remain in BlobStore.

- [ ] **Step 1: Write failing transaction/DAG tests**

Create A, B, C artifacts and derivations `A -> B -> C`; assert downstream(A) is `{B, C}` and a failed transaction leaves no partial rows.

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/integration/storage/test_metadata_store.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement SQLAlchemy Core tables**

Tables: `artifacts`, `processing_activities`, `derivations`, `derivation_inputs`, `derivation_outputs`, `usage_records`. Use foreign keys and explicit transactions; use recursive traversal in Python over indexed edge queries for the first implementation.

- [ ] **Step 4: Apply migration to a temp database and rerun tests**

Run: `uv run alembic upgrade head && uv run pytest tests/integration/storage/test_metadata_store.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/storage tests/integration/storage
git commit -m "feat: add transactional metadata and dependency store"
```

### Task 6: Implement corpus quarantine enforcement before any adapter exists

**Files:**
- Create: `src/voxcodex/corpus/registry.py`
- Create: `src/voxcodex/corpus/holdouts.py`
- Test: `tests/unit/corpus/test_quarantine.py`
- Modify: `src/voxcodex/cli.py`

**Interfaces:**
- Produces `CorpusRegistry.load(path) -> CorpusRegistry`.
- Produces `HoldoutGuard.assert_allowed(case_id: str, operation: str) -> None`.
- All corpus-path access must flow through `HoldoutGuard` until candidate freeze.

- [ ] **Step 1: Write failing quarantine tests**

```python
import pytest
from voxcodex.corpus.holdouts import HoldoutGuard, QuarantinedCaseError


def test_holdout_guard_blocks_frozen_cases():
    guard = HoldoutGuard({"CC-05", "CC-07", "CC-14", "CC-18"}, revealed=False)
    with pytest.raises(QuarantinedCaseError):
        guard.assert_allowed("CC-14", "extract")
    guard.assert_allowed("CC-03", "extract")
```

- [ ] **Step 2: Run and verify failure**

Run: `uv run pytest tests/unit/corpus/test_quarantine.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement registry + guard and CLI `corpus status`**

`voxcodex corpus status --registry corpus/COMPATIBILITY-CORPUS-V1.json` prints total/acquired/quarantined counts without opening source files.

- [ ] **Step 4: Add an integration test that monkeypatches `Path.open`**

Attempting to resolve a quarantined source path through the corpus API must raise before `Path.open` is called.

Run: `uv run pytest tests/unit/corpus/test_quarantine.py tests/integration/corpus -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/voxcodex/corpus src/voxcodex/cli.py tests/unit/corpus tests/integration/corpus
git commit -m "feat: enforce m2 blind holdout quarantine"
```

### Task 7: Foundation gate

**Files:**
- Modify: `README.md`
- Create: `docs/development.md`

**Interfaces:**
- Produces repeatable commands for environment creation, tests, DB migration, and corpus status.

- [ ] **Step 1: Run complete foundation suite**

Run: `uv run pytest tests/unit tests/integration/storage tests/integration/corpus -v`
Expected: PASS with zero quarantined source reads.

- [ ] **Step 2: Run package/CLI smoke commands**

Run: `uv run voxcodex --help && uv run voxcodex corpus status --registry corpus/COMPATIBILITY-CORPUS-V1.json`
Expected: CLI exits 0; status reports 30 cases and 4 quarantined IDs without opening their sources.

- [ ] **Step 3: Document exact setup commands**

Include `uv sync`, `uv run alembic upgrade head`, `uv run pytest`, artifact-store location, and the quarantine rule.

- [ ] **Step 4: Run docs-referenced commands once more**

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/development.md
git commit -m "docs: document m2 development baseline"
```
