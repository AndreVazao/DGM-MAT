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


def test_frozen_agents_source_uses_pyinstaller_bundle(monkeypatch, tmp_path):
    import sys
    from core.agents.boundary import _agents_src, _ensure_agents_importable

    bundle = tmp_path / "_MEI"
    source = bundle / "DGM-MAT-Agents" / "src"
    source.mkdir(parents=True)
    monkeypatch.delenv("DGM_AGENTS_PATH", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(sys, "path", list(sys.path))

    assert _agents_src() == source
    _ensure_agents_importable()
    assert str(source) in sys.path
