from fastapi.routing import APIRoute
from starlette.routing import Mount, WebSocketRoute

from core.api.api_server import app
from core.api.security_policy import ROUTE_CLASSIFICATIONS, SecurityScope, bearer_matches, classify_request_path, classify_route


def test_all_registered_routes_are_classified():
    missing = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(route, APIRoute):
            result = classify_route(path, route.methods)
        elif isinstance(route, WebSocketRoute):
            result = classify_route(path, (), "websocket")
        elif isinstance(route, Mount):
            result = classify_route(path, (), "mount")
        else:
            continue
        if result is None:
            missing.append((path, type(route).__name__))
    assert not missing, f"Unclassified routes: {missing}"


def test_only_health_is_public():
    public = [item for item in ROUTE_CLASSIFICATIONS if item.scope is SecurityScope.PUBLIC_HEALTH]
    assert [(item.methods, item.path) for item in public] == [(("GET",), "/health")]


def test_sensitive_routes_are_not_public():
    for path, method in [
        ("/runtime/approvals/{request_id}", "POST"),
        ("/runtime/queue/actions/{action_id}/approve", "POST"),
        ("/runtime/queue/actions/{action_id}/reject", "POST"),
        ("/runtime/office/telemetry", "GET"),
        ("/runtime/workspace/scan", "GET"),
        ("/mobile/threads/{thread_id}/messages", "POST"),
        ("/governance/repair/self/apply", "POST"),
        ("/governance/commands/run", "POST"),
        ("/governance/commands/catalog", "GET"),
        ("/provider-execution/execute", "POST"),
    ]:
        item = classify_route(path, (method,))
        assert item is not None and item.scope is not SecurityScope.PUBLIC_HEALTH


def test_concrete_queue_decision_paths_resolve_to_operator_policy():
    approve = classify_request_path("/runtime/queue/actions/123/approve", "POST")
    reject = classify_request_path("/runtime/queue/actions/123/reject", "POST")

    assert approve is not None and approve.scope is SecurityScope.OPERATOR
    assert reject is not None and reject.scope is SecurityScope.OPERATOR


def test_governed_command_routes_are_operator_only():
    catalog = classify_route("/governance/commands/catalog", ("GET",))
    execute = classify_route("/governance/commands/run", ("POST",))
    assert catalog is not None and catalog.scope is SecurityScope.OPERATOR
    assert execute is not None and execute.scope is SecurityScope.OPERATOR


def test_bearer_matches_exact_configured_token():
    assert bearer_matches("Bearer abc123", "abc123")
    assert bearer_matches("bearer abc123", "abc123")
    assert not bearer_matches(None, "abc123")
    assert not bearer_matches("Basic abc123", "abc123")
    assert not bearer_matches("Bearer ", "abc123")
    assert not bearer_matches("Bearer abc123 extra", "abc123")
    assert not bearer_matches("Bearer abc123", None)
    assert not bearer_matches("Bearer abc123", "")
    assert not bearer_matches("Bearer  abc123", "abc123")
    assert not bearer_matches("Bearer abc123 ", "abc123")


def test_office_telemetry_is_read_only_local_client_scope():
    telemetry = classify_route("/runtime/office/telemetry", ("GET",))
    assert telemetry is not None
    assert telemetry.scope is SecurityScope.LOCAL_CLIENT


def test_exact_mission_detail_is_read_only_local_client_scope():
    detail = classify_route("/runtime/missions/{mission_id}", ("GET",))
    assert detail is not None
    assert detail.scope is SecurityScope.LOCAL_CLIENT
