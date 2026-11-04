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


def test_governed_chat_uses_only_explicitly_enabled_free_provider(tmp_path, monkeypatch):
    from core.providers.base.provider_base import ProviderBase
    from core.provider_sync.provider_registry import ProviderRegistry

    class FakeFreeProvider(ProviderBase):
        requires_governed_request_id = True

        def __init__(self):
            super().__init__("nvidia_nim")
            self.config.update({"billing_mode": "free_tier", "cost_verified": True})
            self.capabilities["cost_profile"] = "free"
            self.health_metrics.update({
                "status": "unknown", "last_check": 0, "quota_used": 0, "quota_limit": 5,
            })
            self.calls = []
            self.health_calls = 0

        def check_health(self):
            self.health_calls += 1
            self.health_metrics.update({"status": "ok", "last_check": 1})
            return {"available": True}

        def reserve_free_quota(self, request_id):
            self.health_metrics["quota_used"] += 1
            self.calls.append({"reserved": request_id})
            return True

        async def chat(self, messages, **kwargs):
            self.calls.append({"messages": messages, "kwargs": kwargs})
            return "Resposta governada em Portugu?s."

    registry = ProviderRegistry()
    provider = FakeFreeProvider()
    registry.register("nvidia_nim", provider)
    monkeypatch.setattr("core.provider_sync.provider_registry.provider_registry", registry)
    monkeypatch.setattr("core.provider_sync.provider_registry.initialize_default_providers", lambda: None)
    monkeypatch.setenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", "1")
    monkeypatch.setenv("DGM_MOBILE_GOVERNED_PROVIDER", "nvidia_nim")
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")

    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Conversa governada")
    response = service.append_user_message(thread["id"], "Ol?, ajuda-me a organizar este projeto.")

    assert response["message"] == "Resposta governada em Portugu?s."
    assert provider.health_calls == 1
    assert len(provider.calls) == 2
    chat_call = provider.calls[1]
    assert chat_call["kwargs"].get("request_id", "").startswith("mobile-" + thread["id"])
    assert chat_call["messages"][0]["role"] == "system"
    assert chat_call["messages"][-1] == {
        "role": "user",
        "content": "Ol?, ajuda-me a organizar este projeto.",
    }


def test_governed_chat_never_sends_secret_like_conversation_content(tmp_path, monkeypatch):
    from core.providers.base.provider_base import ProviderBase
    from core.provider_sync.provider_registry import ProviderRegistry

    class FakeFreeProvider(ProviderBase):
        requires_governed_request_id = True

        def __init__(self):
            super().__init__("nvidia_nim")
            self.config.update({"billing_mode": "free_tier", "cost_verified": True})
            self.capabilities["cost_profile"] = "free"
            self.health_metrics.update({"status": "ok", "last_check": 1, "quota_used": 0, "quota_limit": 5})
            self.calls = 0

        def reserve_free_quota(self, request_id):
            self.calls += 1
            return True

        async def chat(self, messages, **kwargs):
            self.calls += 1
            return "unexpected"

    registry = ProviderRegistry()
    provider = FakeFreeProvider()
    registry.register("nvidia_nim", provider)
    monkeypatch.setattr("core.provider_sync.provider_registry.provider_registry", registry)
    monkeypatch.setattr("core.provider_sync.provider_registry.initialize_default_providers", lambda: None)
    monkeypatch.setenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", "1")
    monkeypatch.setenv("DGM_MOBILE_GOVERNED_PROVIDER", "nvidia_nim")
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")

    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("N?o enviar segredo")
    response = service.append_user_message(
        thread["id"],
        "O meu api_key=abcdef1234567890 deve ficar privado.",
    )

    assert response["message"]
    assert provider.calls == 0


def test_governed_chat_is_disabled_by_default_and_status_is_truthful(tmp_path, monkeypatch):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.delenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", raising=False)
    status = service.governed_chat_status()
    assert status["enabled"] is False
    assert status["available"] is False
    assert status["reason"] == "disabled_by_configuration"


def test_get_thread_appends_terminal_mission_update_once(tmp_path, monkeypatch):
    from types import SimpleNamespace

    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)
    thread = service.create_thread("Miss?o com seguimento")
    store.append_message(thread["id"], "user", "Lista os meus reposit?rios")
    store.append_message(
        thread["id"],
        "assistant",
        "Miss?o mission_1234abcd registada e em execu??o.",
        metadata={
            "mission_id": "mission_1234abcd",
            "mission_status": "RUNNING",
            "action_status": "RUNNING",
        },
    )
    mission = SimpleNamespace(
        mission_id="mission_1234abcd",
        status=SimpleNamespace(value="COMPLETED"),
        metadata={
            "action_id": 73,
            "result": {"summary": "Invent?rio de reposit?rios conclu?do."},
        },
        error=None,
    )
    fake_engine = SimpleNamespace(
        _reload_mission_checkpoint=lambda _mission_id: mission,
        action_queue=SimpleNamespace(get_action=lambda _action_id: {"status": "COMPLETED"}),
    )
    monkeypatch.setattr("core.mobile_runtime.service.mission_engine", fake_engine)

    first = service.get_thread(thread["id"])
    second = service.get_thread(thread["id"])

    assert len(first["messages"]) == 3
    assert "mission_1234abcd" in first["messages"][-1]["content"]
    assert "checkpoint persistido" in first["messages"][-1]["content"]
    assert "Invent?rio de reposit?rios conclu?do" in first["messages"][-1]["content"]
    assert first["messages"][-1]["metadata"]["mission_update_for"] == "mission_1234abcd"
    assert len(second["messages"]) == 3


def test_get_thread_never_uses_untrusted_mission_metadata_as_a_path(tmp_path, monkeypatch):
    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)
    thread = service.create_thread("Metadata inv?lida")
    store.append_message(
        thread["id"],
        "assistant",
        "Mensagem importada",
        metadata={
            "mission_id": "../../outside",
            "mission_status": "RUNNING",
            "action_status": None,
        },
    )
    called = []
    fake_engine = type(
        "FakeMissionEngine",
        (),
        {"_reload_mission_checkpoint": staticmethod(lambda mission_id: called.append(mission_id))},
    )()
    monkeypatch.setattr("core.mobile_runtime.service.mission_engine", fake_engine)

    result = service.get_thread(thread["id"])

    assert len(result["messages"]) == 1
    assert called == []


def test_short_continuation_reuses_previous_unsupported_goal_without_duplicate(tmp_path):
    class FakeHelp:
        def __init__(self):
            self.calls = []

        def enqueue(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return {"request_id": "help_same_1", "status": "PENDING", "duplicate": False}
            return {"request_id": "help_same_1", "status": "PENDING", "duplicate": True}

    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    helper = FakeHelp()
    service.auto_help_worker = helper
    thread = service.create_thread("Continuidade")
    goal = "Implementa uma nova funcionalidade no DGM-MAT"

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        first = service.append_user_message(thread["id"], goal)
        second = service.append_user_message(thread["id"], "Avanca com forca total")

    create_mission.assert_not_called()
    assert first["followup_mode"] is None
    assert second["followup_mode"] == "reuse"
    assert second["resolved_goal"] == goal
    assert helper.calls[0]["goal"] == goal
    assert helper.calls[1]["goal"] == goal
    assert "pedido anterior" in second["message"]


def test_short_continuation_does_not_duplicate_an_active_mission(tmp_path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Missao ativa")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_a1b2c3d4"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 41}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "QUEUED"},
        ):
            first = service.append_user_message(thread["id"], "Lista os repositorios")
            second = service.append_user_message(thread["id"], "Continua")

    assert create_mission.call_count == 1
    assert first["mission_id"] == "mission_a1b2c3d4"
    assert second["mission_id"] == "mission_a1b2c3d4"
    assert second["followup_mode"] == "active"
    assert "duplicada" in second["message"]


def test_short_continuation_after_terminal_mission_asks_for_next_objective(tmp_path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Missao terminada")
    store = service.store
    store.append_message(
        thread["id"],
        "user",
        "Lista os repositorios",
        metadata={
            "intent": {"intent": "status", "execution_candidate": False},
            "mission_decision": {"supported": True},
        },
    )
    store.append_message(
        thread["id"],
        "assistant",
        "Missao em execucao",
        metadata={
            "mission_id": "mission_1234abcd",
            "mission_status": "RUNNING",
            "action_status": "RUNNING",
        },
    )
    store.append_message(
        thread["id"],
        "assistant",
        "Missao concluida",
        metadata={
            "mission_update_for": "mission_1234abcd",
            "mission_status": "COMPLETED",
            "action_status": "COMPLETED",
        },
    )

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(thread["id"], "Continua")

    create_mission.assert_not_called()
    assert response["followup_mode"] == "clarify"
    assert response["mission_id"] is None
    assert "mission_1234abcd" in response["message"]
    assert "objetivo" in response["message"]


def test_short_continuation_without_prior_action_asks_what_to_resume(tmp_path):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    thread = service.create_thread("Sem contexto")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        response = service.append_user_message(thread["id"], "Ok irmao avanca")

    create_mission.assert_not_called()
    assert response["followup_mode"] == "clarify"
    assert "projeto ou objetivo" in response["message"]


def test_short_continuation_reuses_active_mission_without_duplicate(tmp_path, monkeypatch):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")
    thread = service.create_thread("Continuidade")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_1234abcd"
        create_mission.return_value.status.value = "QUEUED"
        create_mission.return_value.metadata = {"action_id": 41}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "QUEUED"},
        ):
            first = service.append_user_message(thread["id"], "Audita o repositorio DGM-MAT")

        assert first["mission_id"] == "mission_1234abcd"
        create_mission.assert_called_once()

        second = service.append_user_message(thread["id"], "Continua irmao")

    assert second["followup_mode"] == "active"
    assert second["mission_id"] == "mission_1234abcd"
    assert second["resolved_goal"] is None
    assert "mission_1234abcd" in second["message"] and "QUEUED" in second["message"]
    create_mission.assert_called_once()
    assert len(second["thread"]["messages"]) == 4


def test_short_continuation_without_prior_action_asks_for_context(tmp_path, monkeypatch):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")
    thread = service.create_thread("Continuidade sem contexto")

    response = service.append_user_message(thread["id"], "Avanca irmao")

    assert response["followup_mode"] == "clarify"
    assert response["mission_id"] is None
    assert "projeto ou objetivo que devo retomar" in response["message"]
    assert len(response["thread"]["messages"]) == 2


def test_short_continuation_after_terminal_mission_does_not_restart_it(tmp_path, monkeypatch):
    service = MobileConversationService(ConversationStore(tmp_path / "conversations.json"))
    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")
    thread = service.create_thread("Continuidade terminal")

    with patch("core.mobile_runtime.service.mission_engine.create_mission") as create_mission:
        create_mission.return_value.mission_id = "mission_1234abcd"
        create_mission.return_value.status.value = "COMPLETED"
        create_mission.return_value.metadata = {"action_id": 42}
        with patch(
            "core.mobile_runtime.service.mission_engine.action_queue.get_action",
            return_value={"status": "COMPLETED"},
        ):
            first = service.append_user_message(thread["id"], "Audita o reposit?rio DGM-MAT")

        second = service.append_user_message(thread["id"], "Continua")

    assert second["followup_mode"] == "clarify"
    assert second["mission_id"] is None
    assert "mission_1234abcd" in second["message"]
    create_mission.assert_called_once()
