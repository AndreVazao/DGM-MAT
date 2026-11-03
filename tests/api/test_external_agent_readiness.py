from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import governance_api
from core.api.security_policy import SecurityScope, classify_route


def test_external_agent_readiness_route_is_operator_only():
    route = classify_route("/governance/agents/readiness", {"GET"})
    assert route is not None
    assert route.scope is SecurityScope.OPERATOR


def test_external_agent_readiness_endpoint_returns_probe_without_model_call(monkeypatch):
    payload = {
        "schema": "dgm-mat.external-agent-readiness.v1",
        "execution_ready": False,
        "policy": "FREE_ONLY_PAID_DENY",
        "provider_calls_performed": 0,
        "blockers": ["provider_zero_cost_not_verified"],
    }
    monkeypatch.setattr(governance_api, "get_external_agent_readiness", lambda: payload)
    app = FastAPI()
    app.include_router(governance_api.router)

    response = TestClient(app).get("/governance/agents/readiness")

    assert response.status_code == 200
    assert response.json() == payload
    assert response.json()["provider_calls_performed"] == 0
