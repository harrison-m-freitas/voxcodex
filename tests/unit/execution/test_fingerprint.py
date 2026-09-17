from __future__ import annotations

from voxcodex.domain.processing import ProcessorIdentity
from voxcodex.execution.fingerprint import ActivityFingerprint


def _base() -> dict:
    return {
        "activity_type": "pdf_text_extraction",
        "processor": ProcessorIdentity(kind="python", name="pdf.extract", version="1.0.0"),
        "semantic_config_digest": "a" * 64,
        "input_digests": ("b" * 64, "c" * 64),
        "profile_versions": ("extraction-profile:0.1",),
        "schema_versions": ("evidence:0.1", "cbm:0.1"),
    }


def test_fingerprint_is_stable_sha256_for_identical_semantic_inputs():
    first = ActivityFingerprint.compute(**_base())
    second = ActivityFingerprint.compute(**_base())

    assert first == second
    assert len(first) == 64
    assert first == first.lower()


def test_semantic_input_digest_change_changes_fingerprint():
    base = _base()
    changed = {**base, "input_digests": ("b" * 64, "d" * 64)}

    assert ActivityFingerprint.compute(**base) != ActivityFingerprint.compute(**changed)


def test_processor_version_change_changes_fingerprint():
    base = _base()
    changed = {
        **base,
        "processor": ProcessorIdentity(kind="python", name="pdf.extract", version="1.0.1"),
    }

    assert ActivityFingerprint.compute(**base) != ActivityFingerprint.compute(**changed)


def test_semantic_config_change_changes_fingerprint():
    base = _base()
    changed = {**base, "semantic_config_digest": "e" * 64}

    assert ActivityFingerprint.compute(**base) != ActivityFingerprint.compute(**changed)


def test_schema_version_change_changes_fingerprint():
    base = _base()
    changed = {**base, "schema_versions": ("evidence:0.2", "cbm:0.1")}

    assert ActivityFingerprint.compute(**base) != ActivityFingerprint.compute(**changed)


def test_operational_log_level_is_excluded_from_fingerprint():
    base = _base()

    info = ActivityFingerprint.compute(
        **base,
        operational_config={"log_level": "INFO", "trace_sampling": 0.0},
    )
    debug = ActivityFingerprint.compute(
        **base,
        operational_config={"log_level": "DEBUG", "trace_sampling": 1.0},
    )

    assert info == debug


def test_unordered_input_set_is_normalized_but_ordered_inputs_preserve_order():
    base = _base()
    forward = ("b" * 64, "c" * 64)
    reversed_inputs = tuple(reversed(forward))

    unordered_a = ActivityFingerprint.compute(
        **{**base, "input_digests": forward},
        input_order_matters=False,
    )
    unordered_b = ActivityFingerprint.compute(
        **{**base, "input_digests": reversed_inputs},
        input_order_matters=False,
    )
    ordered_a = ActivityFingerprint.compute(
        **{**base, "input_digests": forward},
        input_order_matters=True,
    )
    ordered_b = ActivityFingerprint.compute(
        **{**base, "input_digests": reversed_inputs},
        input_order_matters=True,
    )

    assert unordered_a == unordered_b
    assert ordered_a != ordered_b
