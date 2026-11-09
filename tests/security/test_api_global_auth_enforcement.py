import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.api.api_server import app
from core.api.local_auth_api import session_manager
from core.operations.command_executor import CommandExecutor


@pytest.fixture
def client():
    session_manager.revoke_all()
    with TestClient(app, base_url="http://127.0.0.1:8181", client=("127.0.0.1", 45678)) as value:
        yield value
    session_manager.revoke_all()


def _session(scopes=None):
    return session_manager.create_session(
        "security-test-client",
        scopes or {"local-client", "operator"},
    )[0]


def test_health_is_the_only_public_http_route(client):
    assert client.get("/health").status_code == 200
    response = client.get("/runtime/truth")
    assert response.status_code == 401
    assert "access_token" not in response.text


def test_valid_session_allows_local_read_and_operator_action_route(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/runtime/truth", headers=headers).status_code == 200
    response = client.post("/runtime/missions", headers=headers, json={})
    assert response.status_code == 422


def test_blank_or_whitespace_mission_goal_is_rejected(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}

    for goal in ("", "   "):
        response = client.post(
            "/runtime/missions",
            headers=headers,
            json={"goal": goal, "description": "must not create"},
        )
        assert response.status_code == 422


def test_expired_or_revoked_session_is_rejected(client):
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/runtime/truth", headers=headers).status_code == 200
    assert session_manager.revoke(token)
    assert client.get("/runtime/truth", headers=headers).status_code == 401


def test_insufficient_scope_is_rejected(client):
    token = _session({"local-client"})
    response = client.post(
        "/runtime/missions",
        headers={"Authorization": f"Bearer {token}"},
        json={"goal": "test", "description": "must not create"},
    )
    assert response.status_code in {400, 403}


def test_governed_command_routes_require_operator_session(client):
    assert client.get("/governance/commands/catalog").status_code == 401
    assert client.post(
        "/governance/commands/run",
        json={"command_id": "system.summary"},
    ).status_code == 401

    read_only_token = _session({"local-client"})
    read_only_headers = {"Authorization": f"Bearer {read_only_token}"}
    assert client.get(
        "/governance/commands/catalog", headers=read_only_headers
    ).status_code == 403
    assert client.post(
        "/governance/commands/run",
        headers=read_only_headers,
        json={"command_id": "not-allowed"},
    ).status_code == 403


def test_operator_session_can_read_catalog_and_invalid_command_is_denied(client, tmp_path, monkeypatch):
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    token = _session()
    headers = {"Authorization": f"Bearer {token}"}
    catalog = client.get("/governance/commands/catalog", headers=headers)
    assert catalog.status_code == 200
    assert catalog.json()["arbitrary_shell"] is False

    response = client.post(
        "/governance/commands/run",
        headers=headers,
        json={"command_id": "powershell.raw", "target_path": "C:/"},
    )
    assert response.status_code == 400
    audit_lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2


def test_command_is_not_run_when_audit_storage_is_unavailable(client, tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("file blocks directory", encoding="utf-8")
    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(blocker / "audit.jsonl"))
    monkeypatch.setattr(
        CommandExecutor,
        "execute",
        lambda *args, **kwargs: pytest.fail("executor must not run without a persisted request audit"),
    )
    token = _session()
    response = client.post(
        "/governance/commands/run",
        headers={"Authorization": f"Bearer {token}"},
        json={"command_id": "system.summary"},
    )
    assert response.status_code == 503
    assert "execution refused" in response.text


def test_websocket_requires_session_header(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws"):
            pass
    assert exc.value.code == 1008


def test_authenticated_websocket_accepts_session_header(client):
    token = _session()
    with client.websocket_connect(
        "/ws",
        headers={"Authorization": f"Bearer {token}"},
    ) as websocket:
        websocket.close()


def test_cors_is_not_wildcard_and_rejects_untrusted_preflight(client):
    response = client.options(
        "/runtime/truth",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code in {400, 403}

def test_queue_decision_routes_require_operator_session(client):
    assert client.post("/runtime/queue/actions/999999/approve").status_code == 401
    assert client.post(
        "/runtime/queue/actions/999999/reject",
        json={"reason": "reject for security test"},
    ).status_code == 401

    read_only_token = _session({"local-client"})
    headers = {"Authorization": f"Bearer {read_only_token}"}
    assert client.post(
        "/runtime/queue/actions/999999/approve", headers=headers
    ).status_code == 403
    assert client.post(
        "/runtime/queue/actions/999999/reject",
        headers=headers,
        json={"reason": "reject for security test"},
    ).status_code == 403



def test_office_telemetry_requires_authenticated_local_session(client):
    assert client.get("/runtime/office/telemetry").status_code == 401



def test_external_agent_readiness_requires_operator_session(client, monkeypatch):
    from core.api import governance_api

    payload = {
        "schema": "dgm-mat.external-agent-readiness.v1",
        "execution_ready": False,
        "policy": "FREE_ONLY_PAID_DENY",
        "provider_calls_performed": 0,
        "blockers": ["provider_zero_cost_not_verified"],
    }
    monkeypatch.setattr(governance_api, "get_external_agent_readiness", lambda: payload)

    assert client.get("/governance/agents/readiness").status_code == 401

    read_only_token = _session({"local-client"})
    assert client.get(
        "/governance/agents/readiness",
        headers={"Authorization": f"Bearer {read_only_token}"},
    ).status_code == 403

    operator_token = _session({"local-client", "operator"})
    response = client.get(
        "/governance/agents/readiness",
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert response.status_code == 200
    assert response.json()["execution_ready"] is False
    assert response.json()["provider_calls_performed"] == 0



def test_dgm_hub_agent_routes_require_operator_session(client, monkeypatch):
    from core.api import dgm_hub_agents_api

    class FakeBridge:
        def get_status(self):
            return {"hub": "online", "providers": {}}

    monkeypatch.setattr(dgm_hub_agents_api, "_bridge", lambda: FakeBridge())

    assert client.get("/governance/agents/hub/status").status_code == 401
    assert client.post(
        "/governance/agents/hub/consult",
        json={
            "goal": "Review a small integration",
            "providers": ["codex"],
            "free_capacity_confirmed": True,
        },
    ).status_code == 401

    read_only_token = _session({"local-client"})
    read_only_headers = {"Authorization": f"Bearer {read_only_token}"}
    assert client.get(
        "/governance/agents/hub/status", headers=read_only_headers
    ).status_code == 403
    assert client.post(
        "/governance/agents/hub/consult",
        headers=read_only_headers,
        json={
            "goal": "Review a small integration",
            "providers": ["codex"],
            "free_capacity_confirmed": True,
        },
    ).status_code == 403

    operator_token = _session({"local-client", "operator"})
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    assert client.get(
        "/governance/agents/hub/status", headers=operator_headers
    ).status_code == 200


def test_operator_can_consult_hub_agents_and_request_is_audited(client, monkeypatch, tmp_path):
    from core.api import dgm_hub_agents_api
    from core.organization.dgm_hub_multichat_bridge import HubTaskResult
    from core.organization.specialist_collaboration import SpecialistCollaborationStore

    monkeypatch.setenv("DGM_COMMAND_AUDIT_PATH", str(tmp_path / "provider-audit.jsonl"))

    class FakeBridge:
        def consult(self, **kwargs):
            return HubTaskResult(
                task_id="auth-audit-task",
                conversation_id="auth-audit-conversation",
                results={
                    "llm7": {
                        "provider": "llm7",
                        "status": "ok",
                        "text": "A bounded test consultation result.",
                        "model": "gpt-oss:20b",
                        "duration_seconds": 0.5,
                        "truncated": False,
                    }
                },
            )

    store = SpecialistCollaborationStore(tmp_path / "collaborations")

    class FakeEngine:
        collaboration_store = store

        def record_specialist_result(self, collaboration_id, *, result, provenance):
            packet = store.record_result(collaboration_id, result=result, provenance=provenance)
            return {
                "collaboration_id": collaboration_id,
                "status": packet.status.value,
                "review_required": True,
            }

        def pause_specialist_collaboration(self, collaboration_id, *, reason):
            packet = store.mark_waiting_for_free_capacity(collaboration_id, reason=reason)
            return {"collaboration_id": collaboration_id, "status": packet.status.value}

    monkeypatch.setattr(dgm_hub_agents_api, "_bridge", lambda: FakeBridge())
    monkeypatch.setattr(dgm_hub_agents_api, "_mission_engine", lambda: FakeEngine())

    token = _session({"local-client", "operator"})
    response = client.post(
        "/governance/agents/hub/consult",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "goal": "Check operator-authenticated Hub consultation.",
            "providers": ["llm7"],
            "free_capacity_confirmed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["providers"][0]["result_trusted"] is False
    audit = [
        json.loads(line)
        for line in (tmp_path / "provider-audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in audit] == ["command.requested", "command.completed"]
    assert all(event["session_id"] for event in audit)
    assert audit[0]["command_id"] == "dgm_hub.consult.free_only:llm7"


def test_mobile_pairing_and_chat_history_work_without_general_operator_authority(client, tmp_path, monkeypatch):
    from core.api import local_auth_api, mobile_bridge
    from core.mobile_runtime.store import ConversationStore

    monkeypatch.setenv("DGM_MOBILE_LOCAL_LLM", "off")
    monkeypatch.setenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", "0")
    monkeypatch.setattr(local_auth_api, "_attempts", {})
    monkeypatch.setattr(
        mobile_bridge.service,
        "store",
        ConversationStore(tmp_path / "mobile-conversations.json"),
    )
    origin = "http://127.0.0.1:8181"
    headers = {"Origin": origin}

    pairing_code = client.get("/auth/pairing-code", headers=headers)
    assert pairing_code.status_code == 200
    code = pairing_code.json()["pairing_code"]

    paired = client.post(
        "/auth/pair",
        headers=headers,
        json={"code": code, "client_id": "dgm-mat-mobile-android"},
    )
    assert paired.status_code == 201
    token = paired.json()["access_token"]
    assert set(paired.json()["scopes"]) == {
        "local-client", "mobile-read", "mobile-chat", "mobile-maintenance"
    }
    mobile_headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/mobile/threads",
        headers=mobile_headers,
        json={"title": "Histórico de integração"},
    )
    assert created.status_code == 200
    thread_id = created.json()["id"]

    posted = client.post(
        f"/mobile/threads/{thread_id}/messages",
        headers=mobile_headers,
        json={"content": "Olá, esta é uma mensagem de teste guardada no histórico."},
    )
    assert posted.status_code == 200
    assert posted.json()["thread"]["id"] == thread_id
    assert isinstance(posted.json()["message"], str) and posted.json()["message"].strip()
    assert any(item["role"] == "assistant" for item in posted.json()["thread"]["messages"])

    searched = client.get(
        "/mobile/threads/search",
        headers=mobile_headers,
        params={"q": "mensagem", "limit": 10},
    )
    assert searched.status_code == 200
    assert searched.json()["results"][0]["thread_id"] == thread_id

    recovery_search = client.get(
        "/recovery/search",
        headers=mobile_headers,
        params={"q": "conversa", "limit": 10},
    )
    assert recovery_search.status_code == 200
    assert isinstance(recovery_search.json()["results"], list)

    assert client.get("/mobile/threads", headers=mobile_headers).status_code == 200
    assert client.get("/governance/commands/catalog", headers=mobile_headers).status_code == 403
    assert client.post(
        "/runtime/missions",
        headers=mobile_headers,
        json={"goal": "must not be authorized"},
    ).status_code == 403
