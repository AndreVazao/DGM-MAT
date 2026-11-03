from __future__ import annotations

from types import SimpleNamespace

from core.mobile_runtime.auto_help import AutoHelpStore, AutoHelpWorker
from core.mobile_runtime.service import MobileConversationService
from core.mobile_runtime.store import ConversationStore
from core.organization.dgm_hub_multichat_bridge import HubBridgeError, HubTaskResult


class FakeBridge:
    def __init__(self):
        self.calls = []

    def get_status(self):
        return {
            "providers": {
                "kilo": {"enabled": True, "ready": True},
                "llm7": {"enabled": True, "ready": True},
                "codex": {"enabled": True, "ready": True},
                "claude": {"enabled": True, "ready": True},
            }
        }

    def consult(self, *, goal, context, providers):
        self.calls.append({"goal": goal, "context": context, "providers": providers})
        return HubTaskResult(
            task_id="hub-task-1",
            conversation_id="dgm-mat-help-1",
            results={
                "kilo": {
                    "status": "ok",
                    "text": "Kilo: divide o problema em passos verificáveis.",
                    "model": "openrouter/free",
                },
                "llm7": {
                    "status": "ok",
                    "text": "LLM7: acrescenta testes de regressão.",
                    "model": "gpt-oss:20b",
                },
            },
        )


class FakeCollaborationStore:
    def __init__(self):
        self.created = []
        self.results = []
        self.paused = []

    def create_packet(self, **kwargs):
        collaboration_id = f"collab_{len(self.created) + 1}"
        self.created.append((collaboration_id, kwargs))
        return {"collaboration_id": collaboration_id}

    def get(self, collaboration_id):
        return SimpleNamespace(status=SimpleNamespace(value="RESULT_RECEIVED"))


class FakeEngine:
    def __init__(self):
        self.collaboration_store = FakeCollaborationStore()

    def record_specialist_result(self, collaboration_id, *, result, provenance):
        self.collaboration_store.results.append((collaboration_id, result, provenance))
        return {"status": "RESULT_RECEIVED", "review_required": True}

    def pause_specialist_collaboration(self, collaboration_id, *, reason):
        self.collaboration_store.paused.append((collaboration_id, reason))
        return {"status": "WAITING_FOR_FREE_CAPACITY"}


def test_auto_help_store_deduplicates_same_goal_across_threads(tmp_path):
    store = AutoHelpStore(tmp_path / "help.sqlite3")
    first = store.enqueue(
        thread_id="thread-a",
        goal="Implementa o painel de missões",
        reason="No registered executor",
        providers=["kilo", "llm7"],
    )
    second = store.enqueue(
        thread_id="thread-b",
        goal="  IMPLEMENTA   O PAINEL DE MISSÕES ",
        reason="Same work requested again",
        providers=["kilo", "llm7"],
    )

    assert first["status"] == "PENDING"
    assert second["duplicate"] is True
    assert second["request_id"] == first["request_id"]
    assert store.status()["counts"] == {"PENDING": 1}


def test_auto_help_blocks_secret_like_requests_before_persistence(tmp_path):
    store = AutoHelpStore(tmp_path / "help.sqlite3")
    result = store.enqueue(
        thread_id="thread-a",
        goal="Publica usando api_key=abcdef1234567890",
        reason="No executor",
        providers=["kilo", "llm7"],
    )
    assert result["status"] == "BLOCKED_SECRET_CONTENT"
    assert store.status()["counts"] == {}


def test_auto_help_calls_only_free_allowlisted_hub_providers_and_persists_untrusted_answers(tmp_path, monkeypatch):
    import core.mobile_runtime.auto_help as module

    monkeypatch.setattr(module, "append_command_audit", lambda **_kwargs: None)
    conversation_store = ConversationStore(tmp_path / "conversations.json")
    thread = conversation_store.create_thread("Blocked task")
    bridge = FakeBridge()
    engine = FakeEngine()
    worker = AutoHelpWorker(
        conversation_store=conversation_store,
        store=AutoHelpStore(tmp_path / "help.sqlite3"),
        bridge_factory=lambda: bridge,
        engine_factory=lambda: engine,
        enabled=True,
    )
    queued = worker.enqueue(
        thread_id=thread.id,
        goal="Implementa o painel de missões",
        reason="No registered executor",
    )

    assert queued["status"] == "PENDING"
    assert worker.run_once() is True
    assert worker.run_once() is False
    assert bridge.calls[0]["providers"] == ["kilo", "llm7"]
    assert len(engine.collaboration_store.results) == 2
    assert worker.store.status()["counts"] == {"COMPLETED": 1}

    updated = conversation_store.get_thread(thread.id)
    assert len(updated.messages) == 1
    assert "Kilo" in updated.messages[0].content
    assert "LLM7" in updated.messages[0].content
    assert updated.messages[0].metadata["result_trusted"] is False
    assert updated.messages[0].metadata["paid_fallback"] is False


def test_auto_help_does_not_retry_after_hub_failure(tmp_path, monkeypatch):
    import core.mobile_runtime.auto_help as module

    monkeypatch.setattr(module, "append_command_audit", lambda **_kwargs: None)

    class OfflineBridge:
        calls = 0

        def get_status(self):
            self.calls += 1
            raise HubBridgeError("Hub offline")

    bridge = OfflineBridge()
    conversations = ConversationStore(tmp_path / "conversations.json")
    thread = conversations.create_thread("Blocked")
    worker = AutoHelpWorker(
        conversation_store=conversations,
        store=AutoHelpStore(tmp_path / "help.sqlite3"),
        bridge_factory=lambda: bridge,
        engine_factory=FakeEngine,
        enabled=True,
    )
    worker.enqueue(thread_id=thread.id, goal="Implementa a funcionalidade X", reason="No executor")

    assert worker.run_once() is True
    assert worker.run_once() is False
    assert bridge.calls == 1
    assert worker.store.status()["counts"] == {"FAILED_NO_RETRY": 1}


def test_mobile_service_enqueues_consult_only_for_unsupported_actionable_requests(tmp_path):
    class FakeHelp:
        def __init__(self):
            self.calls = []

        def enqueue(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "request_id": "help_test_123",
                "status": "PENDING",
                "duplicate": False,
            }

    store = ConversationStore(tmp_path / "conversations.json")
    service = MobileConversationService(store)
    helper = FakeHelp()
    service.auto_help_worker = helper
    thread = service.create_thread("Implementação")

    response = service.append_user_message(
        thread["id"],
        "Implementa uma funcionalidade nova no DGM-MAT",
    )

    assert response["mission_id"] is None
    assert response["auto_help_request_id"] == "help_test_123"
    assert len(helper.calls) == 1
    assert "consulta gratuita" in response["message"]


def test_auto_help_never_replays_a_request_left_running_after_restart(tmp_path):
    path = tmp_path / "help.sqlite3"
    first = AutoHelpStore(path)
    queued = first.enqueue(
        thread_id="thread-a",
        goal="Implementa uma nova funcionalidade",
        reason="No executor",
        providers=["kilo", "llm7"],
    )
    claimed = first.claim_next()
    assert claimed["request_id"] == queued["request_id"]
    second = AutoHelpStore(path)
    assert second.status()["counts"] == {"BLOCKED_RESTART": 1}
    assert second.claim_next() is None


def test_auto_help_is_disabled_by_default_and_does_not_enqueue(tmp_path):
    conversations = ConversationStore(tmp_path / "conversations.json")
    thread = conversations.create_thread("Disabled")
    worker = AutoHelpWorker(
        conversation_store=conversations,
        store=AutoHelpStore(tmp_path / "help.sqlite3"),
        enabled=False,
    )
    result = worker.enqueue(
        thread_id=thread.id,
        goal="Implementa uma nova funcionalidade",
        reason="No executor",
    )
    assert result["status"] == "DISABLED"
    assert worker.store.status()["counts"] == {}
