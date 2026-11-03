from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.api import recovery_api
from core.api.security_policy import SecurityScope, classify_request_path


def test_local_ai_source_inventory_route_is_operator_only():
    route = classify_request_path("/recovery/local-ai-sources", "GET")
    assert route is not None
    assert route.scope is SecurityScope.OPERATOR


def test_local_ai_source_inventory_route_returns_metadata_only(monkeypatch):
    monkeypatch.setattr(
        recovery_api,
        "inventory_local_ai_sources",
        lambda *, limit: {
            "schema": "dgm-mat-ai-source-inventory.v1",
            "limit_seen": limit,
            "conversation_content_read": False,
            "cookies_or_tokens_read": False,
            "complete_conversation_inventory": False,
        },
    )
    app = FastAPI()
    app.include_router(recovery_api.router)
    response = TestClient(app).get("/recovery/local-ai-sources", params={"limit": 25})

    assert response.status_code == 200
    assert response.json()["limit_seen"] == 25
    assert response.json()["conversation_content_read"] is False
    assert response.json()["cookies_or_tokens_read"] is False
    assert response.json()["complete_conversation_inventory"] is False


def test_local_ai_source_inventory_route_bounds_limit(monkeypatch):
    monkeypatch.setattr(recovery_api, "inventory_local_ai_sources", lambda **kwargs: {})
    app = FastAPI()
    app.include_router(recovery_api.router)

    assert TestClient(app).get("/recovery/local-ai-sources", params={"limit": 0}).status_code == 422
    assert TestClient(app).get("/recovery/local-ai-sources", params={"limit": 501}).status_code == 422
