# Path: C:\ProgramasGodMode\DGM-MAT\tests\runtime\test_reality_snapshot.py

from types import SimpleNamespace

import pytest

from core.providers.base.provider_base import ProviderBase
from core.runtime import reality_snapshot as reality_snapshot_module
from core.runtime.reality_snapshot import RealitySnapshotService


def test_snapshot_structure():
    service = RealitySnapshotService(workspace_root="/tmp")
    data = service.snapshot()

    assert "timestamp" in data
    assert "machine" in data
    assert "runtime" in data
    assert "providers" in data
    assert "repos" in data
    assert "agents" in data
    assert "workspaces" in data
    assert "processes" in data
    assert "memory" in data


def test_snapshot_summary():
    service = RealitySnapshotService(workspace_root="/tmp")
    summary = service.snapshot_summary()

    assert "timestamp" in summary
    assert "total_repos" in summary
    assert "total_processes" in summary
    assert "active_providers" in summary
    assert "is_runtime_healthy" in summary


def test_unregistered_provider_source_does_not_report_availability(monkeypatch):
    service = RealitySnapshotService(workspace_root="/tmp")
    monkeypatch.setattr(service, "_scan_installed_providers", lambda: ["source-only"])
    monkeypatch.setattr(reality_snapshot_module.provider_registry, "list_providers", lambda: [])
    monkeypatch.setattr(reality_snapshot_module.provider_registry, "get_provider", lambda name: None)

    providers = service._get_providers_status()

    assert len(providers) == 1
    provider_status = providers[0]
    assert provider_status["name"] == "source-only"
    assert provider_status["installed"] is True
    assert provider_status["loaded"] is False
    assert provider_status["healthy"] is False
    assert provider_status["available"] is False
    assert provider_status["availability_observed"] is False
    assert provider_status["status"] == "unknown"
    assert provider_status["latency"] == 0
    assert provider_status["health_observed_at"] is None
    assert provider_status["snapshot_observed_at"] > 0


def test_provider_health_exception_is_reported_as_observed_error(monkeypatch):
    service = RealitySnapshotService(workspace_root="/tmp")
    provider = ProviderBase("broken-provider")

    def broken_check_health():
        raise RuntimeError("synthetic health-check failure")

    monkeypatch.setattr(provider, "check_health", broken_check_health)
    service.profile = SimpleNamespace(lazy_provider_health=False)
    monkeypatch.setattr(service, "_scan_installed_providers", lambda: [])
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "list_providers",
        lambda: ["broken-provider"],
    )
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "get_provider",
        lambda name: provider,
    )

    providers = service._get_providers_status()

    assert providers[0]["status"] == "error"
    assert providers[0]["healthy"] is False
    assert providers[0]["available"] is False
    assert providers[0]["availability_observed"] is True
    assert provider.health_metrics["status"] == "error"
    assert provider.health_metrics["last_check"] > 0


def test_base_provider_check_does_not_become_observed_availability(monkeypatch):
    service = RealitySnapshotService(workspace_root="/tmp")
    provider = ProviderBase("registered-unknown")
    service.profile = SimpleNamespace(lazy_provider_health=False)
    monkeypatch.setattr(service, "_scan_installed_providers", lambda: [])
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "list_providers",
        lambda: ["registered-unknown"],
    )
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "get_provider",
        lambda name: provider,
    )

    providers = service._get_providers_status()

    assert providers[0]["status"] == "unknown"
    assert providers[0]["healthy"] is False
    assert providers[0]["available"] is False
    assert providers[0]["availability_observed"] is False
    assert provider.health_metrics["last_check"] == 0
    assert provider.health_metrics["last_check_attempt"] > 0



def test_lazy_provider_health_preserves_existing_observation_without_new_probe(monkeypatch):
    import time

    service = RealitySnapshotService(workspace_root="/tmp")
    provider = ProviderBase("ollama")
    observed_at = time.time()
    provider.health_metrics["status"] = "ok"
    provider.health_metrics["last_check"] = observed_at
    provider.health_metrics["latency"] = [12.0]
    service.profile = SimpleNamespace(lazy_provider_health=True)

    monkeypatch.setattr(service, "_scan_installed_providers", lambda: ["ollama"])
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "list_providers",
        lambda: ["ollama"],
    )
    monkeypatch.setattr(
        reality_snapshot_module.provider_registry,
        "get_provider",
        lambda name: provider,
    )
    monkeypatch.setattr(
        provider,
        "check_health",
        lambda: pytest.fail("lazy mode must not start a new provider health probe"),
    )

    records = service._get_providers_status()

    assert len(records) == 1
    assert records[0]["name"] == "ollama"
    assert records[0]["status"] == "ok"
    assert records[0]["availability_observed"] is True
    assert records[0]["available"] is True
    assert records[0]["healthy"] is True
    assert records[0]["health_observed_at"] == observed_at
    assert records[0]["latency"] == 12.0

def test_installed_provider_scan_detects_local_adapter_and_legacy_package(tmp_path):
    providers_dir = tmp_path / "core" / "providers"
    local_dir = providers_dir / "local"
    legacy_dir = providers_dir / "legacy"
    local_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)
    (local_dir / "ollama_adapter.py").write_text("# local adapter\n", encoding="utf-8")
    (legacy_dir / "legacy_provider.py").write_text("# legacy provider\n", encoding="utf-8")

    service = RealitySnapshotService(workspace_root=str(tmp_path))
    service.base_dir = tmp_path

    assert service._scan_installed_providers() == ["legacy", "ollama"]
