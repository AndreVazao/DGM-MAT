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

    assert providers == [{
        "name": "source-only",
        "installed": True,
        "loaded": False,
        "healthy": False,
        "available": False,
        "availability_observed": False,
        "status": "unknown",
        "latency": 0,
    }]


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
