from dgm_contracts import Event

from core.agents.boundary import create_runtime_agents


def event():
    return Event(event_id="agent-test", event_type="test", source="test", target="agent", payload={})


def test_core_composition_uses_standalone_agents():
    agents = create_runtime_agents()
    assert set(agents) == {"repo", "provider", "autonomy"}
    assert agents["repo"].__class__.__module__.startswith("dgm_mat_agents")
    assert agents["provider"].__class__.__module__.startswith("dgm_mat_agents")
    assert agents["autonomy"].__class__.__module__.startswith("dgm_mat_agents")


def test_core_boundary_agents_handle_contract_event():
    agents = create_runtime_agents()
    agents["repo"].handle_event(event())
    assert agents["repo"].health == "healthy"


def test_frozen_agent_boundary_uses_bundled_package(monkeypatch):
    import sys
    import types
    import core.agents.boundary as boundary

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setitem(sys.modules, "dgm_mat_agents", types.ModuleType("dgm_mat_agents"))
    monkeypatch.setattr(
        boundary,
        "_agents_src",
        lambda: (_ for _ in ()).throw(AssertionError("frozen builds must not require a checkout")),
    )

    boundary._ensure_agents_importable()
