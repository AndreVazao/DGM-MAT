# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\security\\test_local_sessions.py
from core.api.local_sessions import LocalSessionManager


def test_token_is_random_and_only_valid_session_authenticates():
    manager = LocalSessionManager()
    token, principal = manager.create_session("desktop-client", {"read", "operator"})
    assert len(token) >= 40
    assert principal.subject == "desktop-client"
    assert manager.authenticate(token) == principal
    assert manager.authenticate("wrong-token") is None


def test_scope_is_required_when_requested():
    manager = LocalSessionManager()
    token, _ = manager.create_session("desktop", {"read"})
    assert manager.authenticate(token, required_scope="read") is not None
    assert manager.authenticate(token, required_scope="operator") is None


def test_revoke_invalidates_token():
    manager = LocalSessionManager()
    token, _ = manager.create_session("desktop", {"read"})
    assert manager.revoke(token)
    assert manager.authenticate(token) is None
    assert not manager.revoke(token)


def test_expired_sessions_are_removed():
    now = [1000.0]
    manager = LocalSessionManager(ttl_seconds=60, clock=lambda: now[0])
    token, _ = manager.create_session("desktop", {"read"})
    now[0] = 1060.0
    assert manager.authenticate(token) is None
    assert manager.active_count() == 0


def test_restart_equivalent_empty_manager_invalidates_sessions():
    first = LocalSessionManager()
    token, _ = first.create_session("desktop", {"read"})
    second = LocalSessionManager()
    assert second.authenticate(token) is None


def test_invalid_inputs_fail_closed():
    manager = LocalSessionManager()
    for bad_ttl in (0, 59, 86401, True, "300"):
        try:
            LocalSessionManager(ttl_seconds=bad_ttl)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid TTL accepted: {bad_ttl!r}")
    for subject, scopes in (("", {"read"}), ("desktop", set()), ("x" * 129, {"read"})):
        try:
            manager.create_session(subject, scopes)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid session request accepted")


def test_revoke_all_clears_sessions():
    manager = LocalSessionManager()
    manager.create_session("one", {"read"})
    manager.create_session("two", {"read"})
    assert manager.revoke_all() == 2
    assert manager.active_count() == 0
