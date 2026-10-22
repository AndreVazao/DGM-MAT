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


def test_local_llm_defaults_to_manual_and_never_starts_ollama_implicitly(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import sys

    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.delenv("DGM_MOBILE_LOCAL_LLM", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "psutil",
        SimpleNamespace(virtual_memory=lambda: SimpleNamespace(available=2_000_000_000)),
    )
    monkeypatch.setattr(service, "_select_installed_model", lambda intent: "qwen2.5:1.5b")
    monkeypatch.setattr(service, "_ollama_available", lambda: False)
    with patch.object(service, "_start_ollama") as start_ollama:
        answer = service._try_local_llm(
            SimpleNamespace(messages=[], project=None, repository=None),
            SimpleNamespace(intent="chat"),
        )

    assert answer is None
    start_ollama.assert_not_called()


def test_local_llm_auto_start_requires_explicit_opt_in(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import sys

    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "auto")
    monkeypatch.setitem(
        sys.modules,
        "psutil",
        SimpleNamespace(virtual_memory=lambda: SimpleNamespace(available=2_000_000_000)),
    )
    monkeypatch.setattr(service, "_select_installed_model", lambda intent: "qwen2.5:1.5b")
    with patch.object(service, "_ollama_available", side_effect=[False, False]):
        with patch.object(service, "_start_ollama") as start_ollama:
            answer = service._try_local_llm(
                SimpleNamespace(messages=[], project=None, repository=None),
                SimpleNamespace(intent="chat"),
            )

    assert answer is None
    start_ollama.assert_called_once()


def test_pc_cockpit_e2e_ping_stays_chat_only_and_survives_store_reload(tmp_path: Path, monkeypatch):
    store_path = tmp_path / "conversations.json"
    service = MobileConversationService(ConversationStore(store_path))
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")
    thread = service.create_thread("Diagnóstico E2E DGM-MAT")
    marker = "DGM_E2E_SAFE_PING_391"
    ping = f"Ping local do cockpit DGM-MAT. Devolve apenas a sequência {marker}."

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(thread["id"], ping)

    create_mission.assert_not_called()
    assert response["intent"]["intent"] == "chat"
    assert response["mission_id"] is None
    assert response["message"].strip()

    restored = ConversationStore(store_path).get_thread(thread["id"])
    assert restored is not None
    assert len(restored.messages) == 2
    assert restored.messages[0].role == "user"
    assert marker in restored.messages[0].content
    assert restored.messages[1].role == "assistant"
    assert restored.messages[1].content.strip() == response["message"].strip()
