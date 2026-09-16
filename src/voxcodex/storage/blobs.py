from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

from voxcodex.digests import sha256_bytes


class BlobIntegrityError(RuntimeError):
    """Raised when a stored blob no longer matches its content address."""


@dataclass(frozen=True, slots=True)
class BlobRef:
    sha256: str
    byte_size: int


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, ref: BlobRef) -> Path:
        return self.root / "sha256" / ref.sha256[:2] / ref.sha256[2:]

    def put_bytes(self, data: bytes) -> BlobRef:
        ref = BlobRef(sha256=sha256_bytes(data), byte_size=len(data))
        destination = self.path_for(ref)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            if destination.stat().st_size != ref.byte_size:
                raise BlobIntegrityError(
                    f"existing blob size mismatch for {ref.sha256}: "
                    f"expected {ref.byte_size}, got {destination.stat().st_size}"
                )
            return ref

        fd, temp_name = tempfile.mkstemp(prefix=".voxcodex-blob-", dir=destination.parent)
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, destination)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        return ref

    def read_bytes(self, ref: BlobRef) -> bytes:
        path = self.path_for(ref)
        data = path.read_bytes()
        if len(data) != ref.byte_size or sha256_bytes(data) != ref.sha256:
            raise BlobIntegrityError(f"blob integrity check failed for {ref.sha256}")
        return data

    def import_file(self, path: Path) -> BlobRef:
        return self.put_bytes(Path(path).read_bytes())
