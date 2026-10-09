from fastapi.routing import APIRoute
from starlette.routing import Mount, WebSocketRoute
from core.api.api_server import app
from core.api.security_policy import ROUTE_CLASSIFICATIONS, SecurityScope, bearer_matches, classify_route


def test_all_registered_routes_are_classified():
    missing = []
    for route in app.routes:
        path = getattr(route, 'path', None)
        if isinstance(route, APIRoute):
            result = classify_route(path, route.methods)
        elif isinstance(route, WebSocketRoute):
            result = classify_route(path, (), 'websocket')
        elif isinstance(route, Mount):
            result = classify_route(path, (), 'mount')
        else:
            continue
        if result is None:
            missing.append((path, type(route).__name__))
    assert not missing, f'Unclassified routes: {missing}'


def test_only_health_is_public():
    public = [item for item in ROUTE_CLASSIFICATIONS if item.scope is SecurityScope.PUBLIC_HEALTH]
    assert [(item.methods, item.path) for item in public] == [(('GET',), '/health')]


def test_sensitive_routes_are_not_public():
    for path, method in [('/runtime/approvals/{request_id}', 'POST'), ('/runtime/workspace/scan', 'GET'), ('/mobile/threads/{thread_id}/messages', 'POST'), ('/governance/repair/self/apply', 'POST'), ('/provider-execution/execute', 'POST')]:
        item = classify_route(path, (method,))
        assert item is not None and item.scope is not SecurityScope.PUBLIC_HEALTH


def test_bearer_matches_exact_configured_token():
    assert bearer_matches('Bearer abc123', 'abc123')
    assert bearer_matches('bearer abc123', 'abc123')
    assert not bearer_matches(None, 'abc123')
    assert not bearer_matches('Basic abc123', 'abc123')
    assert not bearer_matches('Bearer ', 'abc123')
    assert not bearer_matches('Bearer abc123 extra', 'abc123')
    assert not bearer_matches('Bearer abc123', None)
    assert not bearer_matches('Bearer abc123', '')
    assert not bearer_matches('Bearer  abc123', 'abc123')
    assert not bearer_matches('Bearer abc123 ', 'abc123')
