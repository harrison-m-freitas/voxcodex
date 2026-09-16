from voxcodex.domain.processing import Derivation, ProcessingActivity


def test_processing_activity_does_not_own_causal_edges():
    assert "input_refs" not in ProcessingActivity.model_fields
    assert "output_refs" not in ProcessingActivity.model_fields
    assert "input_refs" in Derivation.model_fields
    assert "output_refs" in Derivation.model_fields
