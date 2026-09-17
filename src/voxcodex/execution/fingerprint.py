from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.processing import ProcessorIdentity


class ActivityFingerprint:
    """Deterministic identity for the semantic work of a processing activity.

    Operational settings are accepted so callers can keep one configuration
    surface, but are intentionally excluded from the fingerprint payload.
    """

    @staticmethod
    def compute(
        activity_type: str,
        processor: ProcessorIdentity,
        semantic_config_digest: str,
        input_digests: Sequence[str],
        profile_versions: Sequence[str],
        schema_versions: Sequence[str],
        *,
        input_order_matters: bool = True,
        operational_config: Mapping[str, Any] | None = None,
    ) -> str:
        del operational_config

        normalized_inputs = (
            tuple(input_digests)
            if input_order_matters
            else tuple(sorted(input_digests))
        )
        payload = {
            "activity_type": activity_type,
            "processor": processor.model_dump(mode="json"),
            "semantic_config_digest": semantic_config_digest,
            "input_digests": normalized_inputs,
            "input_order_matters": input_order_matters,
            "profile_versions": tuple(sorted(profile_versions)),
            "schema_versions": tuple(sorted(schema_versions)),
        }
        return sha256_bytes(canonical_json_bytes(payload))
