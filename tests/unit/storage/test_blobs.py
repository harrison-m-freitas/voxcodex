from pathlib import Path

import pytest

from voxcodex.storage.blobs import BlobIntegrityError, LocalBlobStore


def test_same_bytes_deduplicate(tmp_path: Path):
    store = LocalBlobStore(tmp_path / "blobs")
    a = store.put_bytes(b"same")
    blob_path = store.path_for(a)
    first_mtime = blob_path.stat().st_mtime_ns

    b = store.put_bytes(b"same")

    assert a == b
    assert store.read_bytes(a) == b"same"
    assert blob_path.stat().st_mtime_ns == first_mtime


def test_import_file_preserves_bytes(tmp_path: Path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"source bytes")
    store = LocalBlobStore(tmp_path / "blobs")

    ref = store.import_file(source)

    assert ref.byte_size == len(b"source bytes")
    assert store.read_bytes(ref) == b"source bytes"


def test_read_detects_corruption(tmp_path: Path):
    store = LocalBlobStore(tmp_path / "blobs")
    ref = store.put_bytes(b"correct")
    store.path_for(ref).write_bytes(b"corrupt")

    with pytest.raises(BlobIntegrityError):
        store.read_bytes(ref)


def test_read_digest_rehydrates_content_addressed_blob(tmp_path: Path):
    store = LocalBlobStore(tmp_path / "blobs")
    ref = store.put_bytes(b"partition payload")

    assert store.read_digest(ref.sha256) == b"partition payload"

    store.path_for(ref).write_bytes(b"tampered payload")
    with pytest.raises(BlobIntegrityError):
        store.read_digest(ref.sha256)
