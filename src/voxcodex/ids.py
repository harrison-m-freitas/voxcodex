import uuid

VOXCODEX_NAMESPACE = uuid.UUID("66f24fa1-7695-5e5c-b6da-72d21d02ab35")


def stable_uuid(namespace: uuid.UUID, seed: str) -> uuid.UUID:
    return uuid.uuid5(namespace, seed)


def new_event_id() -> uuid.UUID:
    return uuid.uuid7()
