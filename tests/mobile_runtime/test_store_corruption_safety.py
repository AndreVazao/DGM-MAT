from pathlib import Path

import pytest

from core.mobile_runtime.store import ConversationStore


def test_invalid_json_blocks_writes_and_preserves_original_file(tmp_path: Path):
    store_path = tmp_path / "mobile_conversations.json"
    original = b'{"threads": ['
    store_path.write_bytes(original)

    store = ConversationStore(store_path)

    with pytest.raises(RuntimeError, match="preserve the original file"):
        store.create_thread("Must not overwrite recovery source")

    assert store_path.read_bytes() == original


def test_invalid_thread_record_blocks_writes_and_preserves_original_file(tmp_path: Path):
    store_path = tmp_path / "mobile_conversations.json"
    original = b'{"threads": [{"messages": "not-a-list"}]}'
    store_path.write_bytes(original)

    store = ConversationStore(store_path)

    with pytest.raises(RuntimeError, match="preserve the original file"):
        store.create_thread("Must not overwrite malformed record")

    assert store_path.read_bytes() == original


def test_missing_threads_collection_blocks_writes_and_preserves_original_file(tmp_path: Path):
    store_path = tmp_path / "mobile_conversations.json"
    original = b'{"schema": "dgm-mat.mobile-conversations.v1"}'
    store_path.write_bytes(original)

    store = ConversationStore(store_path)

    with pytest.raises(RuntimeError, match="preserve the original file"):
        store.create_thread("Must not overwrite incomplete store")

    assert store_path.read_bytes() == original


@pytest.mark.parametrize(
    ("operation", "mutate"),
    [
        pytest.param(
            "create_thread",
            lambda store, thread_id: store.create_thread("Must not appear"),
            id="create_thread",
        ),
        pytest.param(
            "append_message",
            lambda store, thread_id: store.append_message(thread_id, "user", "Must not append"),
            id="append_message",
        ),
        pytest.param(
            "rename",
            lambda store, thread_id: store.rename(thread_id, "Must not rename"),
            id="rename",
        ),
        pytest.param(
            "set_status",
            lambda store, thread_id: store.set_status(thread_id, "archived"),
            id="set_status",
        ),
        pytest.param(
            "update_context",
            lambda store, thread_id: store.update_context(
                thread_id,
                project="Must not change",
                repository="must-not-change/repo",
                context={"attempted": True},
            ),
            id="update_context",
        ),
    ],
)
def test_mutations_fail_before_changing_memory_or_disk(
    tmp_path: Path, operation: str, mutate
):
    store_path = tmp_path / "mobile_conversations.json"
    store = ConversationStore(store_path)
    thread = store.create_thread("Existing conversation")
    store.append_message(thread.id, "user", "Existing message")

    original = store_path.read_bytes()
    before = {item.id: item.to_dict() for item in store.list_threads()}
    store._load_error = "simulated invalid load"

    with pytest.raises(RuntimeError, match="preserve the original file"):
        mutate(store, thread.id)

    assert store_path.read_bytes() == original, operation
    assert {item.id: item.to_dict() for item in store.list_threads()} == before, operation
