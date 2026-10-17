from types import SimpleNamespace
from unittest.mock import patch

from core.bootstrap.runtime.bootstrap_engine import BootstrapEngine
from core.bootstrap.core.dependency_loader import DependencyLoader

def test_federation_is_skipped_by_default_for_local_only_runtime(monkeypatch):
    monkeypatch.delenv("DGM_FEDERATION_ENABLED", raising=False)
    engine = BootstrapEngine.__new__(BootstrapEngine)
    traces = []
    engine._trace = traces.append
    with patch.object(DependencyLoader, "validate_dependency") as validate:
        engine._prepare_federation()
    validate.assert_called_once_with("core.federation.federation_engine")
    assert traces[-1] == "FEDERATION_SKIPPED_LOCAL_ONLY"

def test_federation_can_be_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("DGM_FEDERATION_ENABLED", "1")
    engine = BootstrapEngine.__new__(BootstrapEngine)
    engine.context = SimpleNamespace(node_role="worker")
    traces = []
    engine._trace = traces.append
    local_node = SimpleNamespace(node_id="local-test-node", hostname="local-test-host")
    with patch.object(DependencyLoader, "validate_dependency"), patch("core.federation.node_identity.local_node", local_node), patch("core.federation.rendezvous_client.RendezvousClient") as client, patch("subprocess.check_output", side_effect=FileNotFoundError):
        client.return_value.register.return_value = None
        engine._prepare_federation()
    client.return_value.register.assert_called_once()
    assert traces[-1] == "RENDEZVOUS_REGISTERED"
