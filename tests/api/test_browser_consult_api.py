from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.api import browser_consult_api
from core.api.security_policy import SecurityScope, classify_request_path
from core.api.auth_middleware import LocalSessionAuthMiddleware, _required_scope
from core.api.local_auth_api import (
    EXTENSION_SESSION_SCOPES,
    extension_session_manager,
    session_manager,
)
from core.recovery.browser_consult_store import BrowserConsultStore


def make_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt,gemini,grok,claude,deepseek,qwen")
    store = BrowserConsultStore(tmp_path / "consult.sqlite3")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: store)
    monkeypatch.setattr(browser_consult_api, "_audit", lambda *args, **kwargs: None)
    app = FastAPI()

    @app.middleware("http")
    async def fake_local_session(request: Request, call_next):
        request.scope.setdefault("state", {})["dgm_principal"] = {
            "subject": "test-operator",
            "session_id": "test-extension-session",
            "scopes": ["operator", "browser-capture"],
        }
        return await call_next(request)

    app.include_router(browser_consult_api.router)
    return TestClient(app), store


def test_consult_routes_have_operator_and_extension_scopes():
    expected = (
        ("/recovery/browser-consult/status", "GET", SecurityScope.BROWSER_CONSULT_CONTROL),
        ("/recovery/browser-consult/peek", "GET", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/fresh-review/review_123", "GET", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/mission-context", "POST", SecurityScope.BROWSER_CONSULT_CONTROL),
        ("/recovery/browser-consult/preview", "POST", SecurityScope.BROWSER_CONSULT_CONTROL),
        ("/recovery/browser-consult/enqueue", "POST", SecurityScope.BROWSER_CONSULT_CONTROL),
        ("/recovery/browser-consult/approve/consultation_123", "POST", SecurityScope.BROWSER_CONSULT_CONTROL),
        ("/recovery/browser-consult/next", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/result", "POST", SecurityScope.BROWSER_CAPTURE),
        ("/recovery/browser-consult/block", "POST", SecurityScope.BROWSER_CAPTURE),
    )
    for path, method, scope in expected:
        route = classify_request_path(path, method)
        assert route is not None
        assert route.scope is scope



def test_paired_extension_gets_narrow_consult_control_scope_not_general_operator():
    assert EXTENSION_SESSION_SCOPES == frozenset({"browser-capture", "browser-consult-control"})
    assert "operator" not in EXTENSION_SESSION_SCOPES
    assert _required_scope(SecurityScope.BROWSER_CONSULT_CONTROL) == "browser-consult-control"
    assert _required_scope(SecurityScope.BROWSER_CAPTURE) == "browser-capture"
    assert _required_scope(SecurityScope.OPERATOR) == "operator"



def test_real_paired_extension_session_can_manage_consults_but_not_operator_routes(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt")
    store = BrowserConsultStore(tmp_path / "paired-extension.sqlite3")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: store)
    monkeypatch.setattr(browser_consult_api, "_audit", lambda *args, **kwargs: None)

    app = FastAPI()
    app.include_router(browser_consult_api.router)

    @app.get("/recovery/status")
    def operator_only_route():
        return {"ok": True}

    app.add_middleware(
        LocalSessionAuthMiddleware,
        routes=app.router.routes,
        session_manager=session_manager,
        additional_session_managers=(extension_session_manager,),
    )
    token, _principal = extension_session_manager.create_session(
        subject="dgm-mat-chrome-extension",
        scopes=set(EXTENSION_SESSION_SCOPES),
    )
    headers = {"Authorization": "Bearer " + token}
    client = TestClient(app)

    status = client.get("/recovery/browser-consult/status", headers=headers)
    assert status.status_code == 200

    preview = client.post("/recovery/browser-consult/preview", headers=headers, json={
        "goal": "Review a bounded consultation preview",
        "context": "No provider send should occur during preview.",
    })
    assert preview.status_code == 200
    assert preview.json()["prompt_sha256"]

    queued = client.post("/recovery/browser-consult/enqueue", headers=headers, json={
        "task_ref": "manual_extension_scope_test",
        "goal": "Review the least-privilege scope wiring",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
    })
    assert queued.status_code == 200
    consultation_id = queued.json()["consultation_ids"][0]

    approved = client.post(
        "/recovery/browser-consult/approve/" + consultation_id,
        headers=headers,
    )
    assert approved.status_code == 200

    general_operator = client.get("/recovery/status", headers=headers)
    assert general_operator.status_code == 403


def test_mission_context_preview_reads_durable_checkpoint_and_redacts_secrets(monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace

    fake_engine = SimpleNamespace(missions_path=tmp_path)
    monkeypatch.setattr(browser_consult_api, "_mission_engine", lambda: fake_engine)
    checkpoint = {
        "mission_id": "mission_1234abcd",
        "goal": "Review the DGM-MAT authentication boundary",
        "description": "Inspect the browser consultation API",
        "status": "RUNNING",
        "progress": 42,
        "created_at": "2026-11-09T18:00:00+00:00",
        "updated_at": "2026-11-09T18:10:00+00:00",
        "logs": ["Focused test failed: api_key=secret-value-123456"],
        "subtasks": [{
            "title": "Review API",
            "description": "Check route scopes and validation",
            "status": "completed",
        }],
        "artifacts": ["tests/api/test_browser_consult_api.py"],
        "metadata": {
            "branch": "feat/example",
            "repository_id": "DGM-MAT",
            "repository_path": "C:/Users/private/DGM-MAT",
            "api_key": "must-not-leak",
        },
    }
    (tmp_path / "mission_1234abcd.json").write_text(
        json.dumps(checkpoint), encoding="utf-8"
    )
    client, store = make_client(monkeypatch, tmp_path / "consult")
    response = client.post(
        "/recovery/browser-consult/mission-context",
        json={"mission_id": "mission_1234abcd"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mission_status"] == "RUNNING"
    assert "Review the DGM-MAT authentication boundary" == body["goal"]
    assert "Focused test failed" in body["context"]
    assert "feat/example" in body["context"]
    assert "secret-value-123456" not in body["context"]
    assert "must-not-leak" not in body["context"]
    assert "C:/Users/private" not in body["context"]
    assert body["prompt_redacted"] is True
    assert len(body["context_sha256"]) == 64
    assert body["provider_contacted"] is False
    assert body["requires_operator_preview_and_approval"] is True
    assert store.status()["counts"] == {}


def test_mission_context_preview_rejects_missing_or_malformed_checkpoint(monkeypatch, tmp_path):
    from types import SimpleNamespace

    fake_engine = SimpleNamespace(missions_path=tmp_path)
    monkeypatch.setattr(browser_consult_api, "_mission_engine", lambda: fake_engine)
    client, store = make_client(monkeypatch, tmp_path / "consult")
    missing = client.post(
        "/recovery/browser-consult/mission-context",
        json={"mission_id": "mission_1234abcd"},
    )
    malformed = client.post(
        "/recovery/browser-consult/mission-context",
        json={"mission_id": "not-a-mission"},
    )

    assert missing.status_code == 404
    assert malformed.status_code == 422
    assert store.status()["counts"] == {}


def test_preview_returns_exact_redacted_prompt_without_queueing(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-consult/preview", json={
        "goal": "Review the authentication boundary",
        "context": "api_key=secret-value-123456",
    })

    assert response.status_code == 200
    body = response.json()
    assert "TASK:" in body["prompt"]
    assert "[REDACTED_SECRET]" in body["prompt"]
    assert body["prompt_redacted"] is True
    assert len(body["prompt_sha256"]) == 64
    assert store.status()["counts"] == {}


def test_enqueue_rejects_content_changed_after_preview(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    draft = {
        "goal": "Review the authentication boundary",
        "context": "Only the API contract is relevant.",
    }
    preview = client.post("/recovery/browser-consult/preview", json=draft)
    assert preview.status_code == 200

    changed = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_preview_binding",
        "goal": draft["goal"],
        "context": "A different context was substituted.",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
        "preview_sha256": preview.json()["prompt_sha256"],
    })

    assert changed.status_code == 409
    assert store.status()["counts"] == {}


def test_enqueue_accepts_claude_provider(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission-claude-api",
        "goal": "Review a bounded provider integration change",
        "providers": ["claude"],
        "free_capacity_confirmed": True,
    })
    assert response.status_code == 200
    assert response.json()["provider_count"] == 1
    assert store.status()["counts"] == {"PENDING_APPROVAL": 1}


def test_enqueue_accepts_exact_preview_digest(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    draft = {
        "goal": "Review the authentication boundary",
        "context": "Only the API contract is relevant.",
    }
    preview = client.post("/recovery/browser-consult/preview", json=draft)
    assert preview.status_code == 200

    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_preview_bound",
        **draft,
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
        "preview_sha256": preview.json()["prompt_sha256"],
    })

    assert queued.status_code == 200
    assert queued.json()["status"] == "PENDING_APPROVAL"
    assert store.status()["counts"] == {"PENDING_APPROVAL": 1}


def test_consultation_requires_operator_approval_and_claim_token(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review this bounded technical question",
        "context": "Only use the minimal redacted context.",
        "providers": ["chatgpt", "deepseek"],
        "free_capacity_confirmed": True,
    })
    assert queued.status_code == 200
    body = queued.json()
    assert body["status"] == "PENDING_APPROVAL"
    assert body["approval_required"] is True
    consultation_id = body["consultation_ids"][0]

    empty = client.post("/recovery/browser-consult/next?provider=chatgpt", json={})
    assert empty.status_code == 200
    assert empty.json()["status"] == "queue_empty"

    approved = client.post("/recovery/browser-consult/approve/" + consultation_id)
    assert approved.status_code == 200
    claimed = client.post("/recovery/browser-consult/next?provider=chatgpt", json={})
    assert claimed.status_code == 200
    item = claimed.json()["next"]
    assert item["consultation_id"] == consultation_id
    assert len(item["claim_token"]) >= 32

    wrong = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": "x" * 40,
        "response_text": "This must not be stored.",
    })
    assert wrong.status_code == 409

    result = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": item["claim_token"],
        "response_text": "Independent opinion: verify the race condition with a test.",
    })
    assert result.status_code == 200
    assert result.json()["result_trusted"] is False
    assert store.status()["counts"]["COMPLETED"] == 1


def test_mission_consultation_result_is_attached_as_unverified_checkpoint_evidence(monkeypatch, tmp_path):
    from types import SimpleNamespace
    mission = SimpleNamespace(metadata={}, logs=[])
    saved = []
    fake_engine = SimpleNamespace(
        _reload_mission_checkpoint=lambda mission_id: mission if mission_id == "mission_1234abcd" else None,
        save_mission=lambda value: saved.append(value),
    )
    monkeypatch.setattr(browser_consult_api, "_mission_engine", lambda: fake_engine)
    client, store = make_client(monkeypatch, tmp_path)

    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review the mission plan",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
    })
    consultation_id = queued.json()["consultation_ids"][0]
    assert client.post("/recovery/browser-consult/approve/" + consultation_id).status_code == 200
    claimed = client.post("/recovery/browser-consult/next?provider=chatgpt", json={}).json()["next"]

    result = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": claimed["claim_token"],
        "response_text": "Proposal: add a regression test before changing the dispatch contract.",
    })

    assert result.status_code == 200
    assert result.json()["mission_updated"] is True
    assert mission.metadata["external_consultations"][0]["result_trusted"] is False
    assert mission.metadata["external_consultations"][0]["consultation_id"] == consultation_id
    assert mission.logs and "unverified proposal" in mission.logs[0]
    assert saved == [mission]


def test_consultation_requires_free_capacity_attestation(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_1234abcd",
        "goal": "Review a technical assumption",
        "providers": ["qwen"],
        "free_capacity_confirmed": False,
    })
    assert response.status_code == 400
    assert store.status()["counts"] == {}


def test_consultation_api_rejects_missing_principal(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_BROWSER_CONSULT_ENABLED", "1")
    monkeypatch.setenv("DGM_BROWSER_CONSULT_FREE_PROVIDERS", "chatgpt")
    monkeypatch.setattr(browser_consult_api, "_store", lambda: BrowserConsultStore(tmp_path / "consult.sqlite3"))
    app = FastAPI()
    app.include_router(browser_consult_api.router)
    response = TestClient(app).get("/recovery/browser-consult/status")
    assert response.status_code == 401


def test_browser_consult_result_is_appended_to_linked_mobile_thread(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    from core.api import mobile_bridge

    class FakeConversationStore:
        def __init__(self):
            self.messages = []

        def append_message(self, thread_id, role, content, *, metadata):
            self.messages.append((thread_id, role, content, metadata))

    fake_store = FakeConversationStore()
    monkeypatch.setattr(mobile_bridge, "service", type("FakeService", (), {"store": fake_store})())

    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mobile-thread:thread-123",
        "goal": "Review this mobile mission fallback",
        "providers": ["qwen"],
        "free_capacity_confirmed": True,
    })
    consultation_id = queued.json()["consultation_ids"][0]
    client.post("/recovery/browser-consult/approve/" + consultation_id)
    claimed = client.post("/recovery/browser-consult/next?provider=qwen", json={}).json()["next"]

    result = client.post("/recovery/browser-consult/result", json={
        "consultation_id": consultation_id,
        "claim_token": claimed["claim_token"],
        "response_text": "The independent review recommends a regression test.",
    })

    assert result.status_code == 200
    assert result.json()["conversation_updated"] is True
    assert fake_store.messages[0][0:2] == ("thread-123", "assistant")
    assert "QWEN (resposta externa não verificada)" in fake_store.messages[0][2]
    assert fake_store.messages[0][3]["result_trusted"] is False


def test_approval_fails_closed_when_audit_write_fails(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_audit_approval",
        "goal": "Review an approval audit failure",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
    })
    consultation_id = queued.json()["consultation_ids"][0]

    def fail_audit(*_args, **_kwargs):
        raise OSError("audit storage unavailable")

    monkeypatch.setattr(browser_consult_api, "_audit", fail_audit)
    response = client.post("/recovery/browser-consult/approve/" + consultation_id)

    assert response.status_code == 503
    assert store.status()["counts"] == {"PENDING_APPROVAL": 1}
    assert store.claim_next("chatgpt") is None


def test_prompt_is_blocked_when_release_audit_fails(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "mission_audit_release",
        "goal": "Review a prompt release audit failure",
        "providers": ["qwen"],
        "free_capacity_confirmed": True,
    })
    consultation_id = queued.json()["consultation_ids"][0]
    assert client.post("/recovery/browser-consult/approve/" + consultation_id).status_code == 200

    def fail_audit(*_args, **_kwargs):
        raise OSError("audit storage unavailable")

    monkeypatch.setattr(browser_consult_api, "_audit", fail_audit)
    response = client.post("/recovery/browser-consult/next?provider=qwen", json={})

    assert response.status_code == 503
    assert store.status()["counts"] == {"BLOCKED_INTERRUPTED": 1}
    assert store.claim_next("qwen") is None


def test_fresh_review_api_requires_both_providers_and_persists_resume(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    unsupported = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "egm-task:api-1",
        "goal": "Review the architecture.",
        "providers": ["grok"],
        "free_capacity_confirmed": True,
        "review_mode": "fresh_review",
        "review_id": "egm-review-api-1",
    })
    assert unsupported.status_code == 400
    incomplete = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "egm-task:api-1",
        "goal": "Review the architecture.",
        "providers": ["chatgpt"],
        "free_capacity_confirmed": True,
        "review_mode": "fresh_review",
        "review_id": "egm-review-api-1",
    })
    assert incomplete.status_code == 400

    queued = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "egm-task:api-1",
        "goal": "Review the architecture.",
        "providers": ["chatgpt", "gemini"],
        "free_capacity_confirmed": True,
        "review_mode": "fresh_review",
        "review_id": "egm-review-api-1",
    })
    assert queued.status_code == 200
    ids = dict(zip(["chatgpt", "gemini"], queued.json()["consultation_ids"]))

    peek = client.get("/recovery/browser-consult/peek?provider=chatgpt")
    assert peek.status_code == 200
    assert peek.json()["status"] == "queue_empty"
    assert store.status()["counts"]["PENDING_APPROVAL"] == 2

    for consultation_id in ids.values():
        assert client.post("/recovery/browser-consult/approve/" + consultation_id).status_code == 200
    for provider in ("chatgpt", "gemini"):
        peek = client.get("/recovery/browser-consult/peek?provider=" + provider)
        assert peek.json()["next"]["review_mode"] == "fresh_review"
        assert peek.json()["status"] == "pending"
    assert store.status()["counts"]["PENDING"] == 2

    evidence_by_provider = {
        "chatgpt": {
            "provider": "chatgpt",
            "source_id": "chatgpt-new-conversation",
            "initial_source_id": None,
            "initial_visible_message_count": 0,
            "privacy_mode": "chatgpt_temporary_unpersonalized",
            "privacy_mode_verified": True,
            "verification": "blank_page_then_new_conversation_id_and_stable_response",
        },
        "gemini": {
            "provider": "gemini",
            "source_id": "gemini-new-conversation",
            "initial_source_id": None,
            "initial_visible_message_count": 0,
            "privacy_mode": "gemini_temporary_chat",
            "privacy_mode_verified": True,
            "verification": "blank_page_then_new_conversation_id_and_stable_response",
        },
    }
    for provider in ("chatgpt", "gemini"):
        claimed = client.post("/recovery/browser-consult/next?provider=" + provider, json={}).json()["next"]
        result = client.post("/recovery/browser-consult/result", json={
            "consultation_id": ids[provider],
            "claim_token": claimed["claim_token"],
            "response_text": "Review findings from " + provider + ": add an explicit recovery test.",
            "evidence": evidence_by_provider[provider],
        })
        assert result.status_code == 200
        assert result.json()["independence_attested"] is False

    resumed = client.get("/recovery/browser-consult/fresh-review/egm-review-api-1")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "COMPLETED"
    assert resumed.json()["provider_count"] == 2
    assert resumed.json()["expected_provider_count"] == 2
    assert {item["provider"] for item in resumed.json()["consultations"]} == {"chatgpt", "gemini"}
    assert all(item["result_trusted"] is False for item in resumed.json()["consultations"])


def test_fresh_review_enqueue_rejects_missing_review_id(monkeypatch, tmp_path):
    client, store = make_client(monkeypatch, tmp_path)
    response = client.post("/recovery/browser-consult/enqueue", json={
        "task_ref": "egm-task:api-2",
        "goal": "Review the architecture.",
        "providers": ["chatgpt", "gemini"],
        "free_capacity_confirmed": True,
        "review_mode": "fresh_review",
    })
    assert response.status_code == 400
    assert store.status()["counts"] == {}
