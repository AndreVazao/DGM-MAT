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
