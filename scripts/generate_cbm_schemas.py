from __future__ import annotations

from pathlib import Path

from voxcodex.digests import canonical_json_bytes
from voxcodex.domain.cbm.schema import schema_snapshots


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "schemas" / "cbm" / "0.1"
    root.mkdir(parents=True, exist_ok=True)
    for filename, schema in schema_snapshots().items():
        (root / filename).write_bytes(canonical_json_bytes(schema) + b"\n")


if __name__ == "__main__":
    main()
