

def test_runtime_shutdown_route_is_operator_only():
    shutdown = classify_route("/runtime/shutdown", ("POST",))
    assert shutdown is not None
    assert shutdown.scope is SecurityScope.OPERATOR
    assert _required_scope(shutdown.scope) == "operator"
