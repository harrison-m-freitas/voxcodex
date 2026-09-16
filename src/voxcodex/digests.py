import hashlib

import rfc8785
from pydantic import BaseModel


def canonical_json_bytes(value: object) -> bytes:
    return rfc8785.dumps(value)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_digest(
    model: BaseModel,
    exclude: set[str] | frozenset[str] = frozenset(),
) -> str:
    payload = model.model_dump(mode="json", exclude=set(exclude), exclude_none=True)
    return sha256_bytes(canonical_json_bytes(payload))
