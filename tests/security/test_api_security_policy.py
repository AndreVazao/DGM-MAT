from fastapi.routing import APIRoute
from starlette.routing import Mount, WebSocketRoute

from core.api.api_server import app
from core.api.security_policy import ROUTE_CLASSIFICATIONS, SecurityScope, bearer_matches, classify_request_path, classify_route
from core.api.api_server import _mobile_ui_directory, _pc_cockpit_directory


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
        ("/governance/agents/hub/consult", "POST"),
        ("/governance/agents/hub/status", "GET"),
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


def test_pc_cockpit_mount_is_optional_and_uses_an_explicit_valid_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("DGM_PC_COCKPIT_PATH", str(tmp_path))
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    (tmp_path / "app.js").write_text("/* test */", encoding="utf-8")
    (tmp_path / "styles.css").write_text("/* test */", encoding="utf-8")

    assert _pc_cockpit_directory() == tmp_path

    (tmp_path / "styles.css").unlink()
    assert _pc_cockpit_directory() is None


def test_pc_cockpit_static_mount_is_classified_as_local_static_client():
    cockpit = classify_route("/cockpit", (), "mount")
    assert cockpit is not None
    assert cockpit.scope is SecurityScope.LOCAL_STATIC_CLIENT
    assert cockpit.scope is not SecurityScope.PUBLIC_HEALTH


def test_legacy_mobile_ui_setting_does_not_mount_the_pc_cockpit_twice(monkeypatch, tmp_path):
    pc_dir = tmp_path / "DGM-Cockpit-Frontend"
    pc_dir.mkdir()
    (pc_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    (pc_dir / "app.js").write_text("/* test */", encoding="utf-8")
    (pc_dir / "styles.css").write_text("/* test */", encoding="utf-8")
    monkeypatch.setenv("DGM_MOBILE_UI_PATH", str(pc_dir))
    monkeypatch.setenv("DGM_PC_COCKPIT_PATH", str(pc_dir))

    # A mobile PWA may still be returned from the independent fallback directory,
    # but the PC cockpit itself must never be selected for /app.
    assert _mobile_ui_directory() != pc_dir



def test_dgm_hub_agent_routes_are_operator_only():
    status = classify_route("/governance/agents/hub/status", ("GET",))
    consult = classify_route("/governance/agents/hub/consult", ("POST",))
    assert status is not None and status.scope is SecurityScope.OPERATOR
    assert consult is not None and consult.scope is SecurityScope.OPERATOR

def test_dgm_hub_meeting_observer_routes_are_operator_only():
    routes = [
        ("/governance/agents/hub/observer/status", "GET"),
        ("/governance/agents/hub/observer/capture", "POST"),
        ("/governance/agents/hub/observer/start", "POST"),
        ("/governance/agents/hub/observer/stop", "POST"),
        ("/governance/agents/hub/meetings", "GET"),
        ("/governance/agents/hub/meetings/{conversation_id}", "GET"),
        ("/governance/agents/hub/meetings/{conversation_id}/proposals", "POST"),
        ("/governance/agents/hub/meetings/{conversation_id}/decision", "POST"),
    ]
    for path, method in routes:
        result = classify_route(path, (method,))
        assert result is not None and result.scope is SecurityScope.OPERATOR, path


def test_repository_learning_and_mission_page_scopes_are_bounded():
    learning_status = classify_route("/runtime/repository-learning", ("GET",))
    learning_tree = classify_route("/runtime/repository-learning/tree", ("GET",))
    learning_start = classify_route("/runtime/repository-learning/start", ("POST",))
    learning_stop = classify_route("/runtime/repository-learning/stop", ("POST",))
    mission_page = classify_route("/runtime/missions/page", ("GET",))

    assert learning_status is not None and learning_status.scope is SecurityScope.LOCAL_CLIENT
    assert learning_tree is not None and learning_tree.scope is SecurityScope.LOCAL_CLIENT
    assert learning_start is not None and learning_start.scope is SecurityScope.OPERATOR
    assert learning_stop is not None and learning_stop.scope is SecurityScope.OPERATOR
    assert mission_page is not None and mission_page.scope is SecurityScope.LOCAL_CLIENT


def test_auto_help_status_is_local_client_and_controls_are_operator_only():
    status = classify_route("/runtime/auto-help", ("GET",))
    start = classify_route("/runtime/auto-help/start", ("POST",))
    stop = classify_route("/runtime/auto-help/stop", ("POST",))
    assert status is not None and status.scope is SecurityScope.LOCAL_CLIENT
    assert start is not None and start.scope is SecurityScope.OPERATOR
    assert stop is not None and stop.scope is SecurityScope.OPERATOR


def test_mobile_pairing_routes_use_separate_least_privilege_scopes():
    from core.api.auth_middleware import _required_scope

    expected = {
        ("/mobile/threads/search", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/recovery/search", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/recovery/sources/{provider}/{source_id}/messages", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/runtime/workspace/scan", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/runtime/approvals", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/runtime/queue", "GET"): (SecurityScope.MOBILE_READ, "mobile-read"),
        ("/mobile/threads", "POST"): (SecurityScope.MOBILE_CHAT, "mobile-chat"),
        ("/mobile/threads/{thread_id}/messages", "POST"): (SecurityScope.MOBILE_CHAT, "mobile-chat"),
        ("/mobile/usb-recovery/repair", "POST"): (SecurityScope.MOBILE_MAINTENANCE, "mobile-maintenance"),
    }
    for (path, method), (scope, token_scope) in expected.items():
        classification = classify_route(path, (method,))
        assert classification is not None
        assert classification.scope is scope
        assert _required_scope(scope) == token_scope


def test_mobile_session_scopes_do_not_replace_general_operator_scope():
    from core.api.auth_middleware import _required_scope

    mobile_scopes = {"local-client", "mobile-read", "mobile-chat", "mobile-maintenance"}
    assert "operator" not in mobile_scopes
    assert _required_scope(SecurityScope.OPERATOR) == "operator"
    assert _required_scope(SecurityScope.MOBILE_CHAT) == "mobile-chat"


def test_organization_task_command_result_and_approval_routes_are_scoped():
    from core.api.auth_middleware import _required_scope

    expected = {
        ("/runtime/organization/tasks", "POST"): (SecurityScope.OPERATOR, "operator"),
        ("/runtime/organization/tasks/{task_id}", "GET"): (SecurityScope.LOCAL_CLIENT, "local-client"),
        ("/runtime/organization/tasks/{task_id}/approval", "POST"): (SecurityScope.OPERATOR, "operator"),
        ("/runtime/organization/tasks/{task_id}/decision", "POST"): (SecurityScope.OPERATOR, "operator"),
    }
    for (path, method), (scope, token_scope) in expected.items():
        classification = classify_route(path, (method,))
        assert classification is not None
        assert classification.scope is scope
        assert _required_scope(scope) == token_scope
