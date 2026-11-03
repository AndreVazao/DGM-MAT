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
    assert result.requires_approval is True


def test_destructive_intent_requires_approval():
    result = IntentInterpreter().interpret("Apaga o repositório DGM-MAT-Cluster")
    assert result.requires_approval is True


def test_service_keeps_continuous_conversation(tmp_path: Path):
    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)
    thread = service.create_thread("Teste")
    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_test"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 17}
        with patch("core.mobile_runtime.service.mission_engine.action_queue.get_action", return_value={"status": "QUEUED"}):
            response = service.append_user_message(
                thread["id"],
                "Sincroniza GitHub worktree DGM-MAT",
            )
    assert response["intent"]["intent"] == "sync"
    assert response["mission_decision"]["intent"] == "repository_sync_worktree"
    assert response["mission_requires_approval"] is True
    assert response["action_status"] == "QUEUED"
    assert response["mission_id"] == "mission_test"
    assert "pendente de aprovação" in response["message"]
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



def test_read_only_repository_listing_creates_a_registered_mission(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Teste de listagem")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_readonly"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 18}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "APPROVED"},
        ):
            response = service.append_user_message(thread["id"], "Lista os repositórios")

    create_mission.assert_called_once()
    assert response["mission_decision"]["intent"] == "list_repositories"
    assert response["mission_decision"]["supported"] is True
    assert response["action_status"] == "APPROVED"
    assert response["mission_id"] == "mission_readonly"
    assert "allowlist" in response["message"]


def test_repository_audit_routes_to_read_only_local_research(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Auditoria local")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_audit"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 19}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "APPROVED"},
        ):
            response = service.append_user_message(
                thread["id"],
                "Audita o repositório DGM-MAT",
            )

    create_mission.assert_called_once()
    assert response["intent"]["intent"] == "audit"
    assert response["mission_decision"]["intent"] == "local_research"
    assert response["mission_requires_approval"] is False
    assert response["mission_id"] == "mission_audit"


def test_unsupported_implementation_does_not_create_or_queue_a_mission(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Implementação sem executor")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(
            thread["id"],
            "Implementa uma funcionalidade nova no DGM-MAT",
        )

    create_mission.assert_not_called()
    assert response["intent"]["intent"] == "implement"
    assert response["intent"]["requires_approval"] is True
    assert response["mission_decision"]["supported"] is False
    assert response["mission_id"] is None
    assert "não tem um executor registado" in response["message"]
    assert "Não foi criada missão" in response["message"]


def test_dgm_mat_status_routes_to_supported_read_only_system_summary(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Estado DGM-MAT")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_status"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 20}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "APPROVED"},
        ):
            response = service.append_user_message(thread["id"], "Estado do DGM-MAT")

    create_mission.assert_called_once()
    assert response["intent"]["intent"] == "status"
    assert response["mission_decision"]["intent"] == "system_summary"
    assert response["mission_id"] == "mission_status"


def test_mixed_audit_and_mutation_is_rejected_without_mission(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Pedido misto")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(
            thread["id"],
            "Audita o repositório DGM-MAT e corrige o cockpit",
        )

    create_mission.assert_not_called()
    assert response["mission_decision"]["supported"] is False
    assert response["mission_id"] is None
    assert response["intent"]["requires_approval"] is True



def test_external_research_is_not_claimed_as_executed_without_a_provider(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Pesquisa externa")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(
            thread["id"],
            "Pesquisa na internet sobre novos agentes gratuitos",
        )

    create_mission.assert_not_called()
    assert response["intent"]["intent"] == "research"
    assert response["mission_id"] is None
    assert "Não foi feita pesquisa externa" in response["message"]


def test_memory_request_does_not_claim_persistent_memory_write(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Memória")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(
            thread["id"],
            "Guarda isto na memória persistente",
        )

    create_mission.assert_not_called()
    assert response["intent"]["intent"] == "memory"
    assert response["mission_id"] is None
    assert "não foi promovida à memória persistente" in response["message"]


def test_unknown_status_request_does_not_claim_a_diagnostic_was_run(tmp_path: Path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Estado não suportado")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(thread["id"], "Estado do servidor remoto")

    create_mission.assert_not_called()
    assert response["intent"]["intent"] == "status"
    assert response["mission_id"] is None
    assert "Não foi executado nenhum comando" in response["message"]
