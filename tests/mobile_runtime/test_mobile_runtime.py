# Path: C:\ProgramasGodMode\DGM-MAT\tests\mobile_runtime\test_mobile_runtime.py
from pathlib import Path
from unittest.mock import patch

from core.mobile_runtime.intent import IntentInterpreter
from core.mobile_runtime.store import ConversationStore
from core.mobile_runtime.service import MobileConversationService


def test_thread_is_durable_and_renamable(tmp_path: Path):
    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)

    thread = service.create_thread("DGM-MAT")
    service.rename(thread["id"], "DGM-MAT — Cockpit")

    restored = ConversationStore(tmp_path / "conversations.json")
    loaded = restored.get_thread(thread["id"])

    assert loaded is not None
    assert loaded.title == "DGM-MAT — Cockpit"


def test_intent_preserves_execution_boundary():
    result = IntentInterpreter().interpret("Avança no DGM-MAT e corrige o cockpit")
    assert result.intent in {"implement", "repair"}
    assert result.execution_candidate is True
    assert result.requires_approval is False


def test_destructive_intent_requires_approval():
    result = IntentInterpreter().interpret("Apaga o repositório DGM-MAT-Cluster")
    assert result.requires_approval is True


def test_service_keeps_continuous_conversation(tmp_path: Path):
    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)
    thread = service.create_thread("Teste")
    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_test"
        response = service.append_user_message(thread["id"], "Sincroniza a memória")
    assert response["intent"]["intent"] == "sync"
    assert response["mission_id"] == "mission_test"
    assert len(response["thread"]["messages"]) == 2
