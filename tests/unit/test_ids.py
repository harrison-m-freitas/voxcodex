import uuid

from voxcodex.ids import VOXCODEX_NAMESPACE, new_event_id, stable_uuid


def test_stable_uuid_is_deterministic_and_namespaced():
    first = stable_uuid(VOXCODEX_NAMESPACE, "document:alpha")
    second = stable_uuid(VOXCODEX_NAMESPACE, "document:alpha")
    different = stable_uuid(VOXCODEX_NAMESPACE, "document:beta")
    assert first == second
    assert first != different
    assert first.version == 5


def test_new_event_id_uses_uuid7(monkeypatch):
    expected = uuid.UUID("01890f58-e7b2-7cc3-98c4-dc0c0c07398f")
    monkeypatch.setattr(uuid, "uuid7", lambda: expected, raising=False)
    assert new_event_id() == expected
