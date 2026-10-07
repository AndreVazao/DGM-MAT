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
