from types import SimpleNamespace

from core.api import runtime_api


def test_provider_subsystem_summary_reports_empty_registry():
    summary = runtime_api._provider_subsystem_summary([], [])

    assert summary["state"] == "empty_registry"
    assert summary["registered_count"] == 0
    assert summary["registered_names"] == []
    assert summary["reported_available_count"] == 0
    assert summary["availability_reported"] is False


def test_provider_subsystem_summary_does_not_infer_availability_from_registration():
    summary = runtime_api._provider_subsystem_summary(
        ["example-provider"],
        [{"name": "example-provider", "status": "unknown", "available": False}],
    )

    assert summary["state"] == "registered_no_availability_reported"
    assert summary["registered_count"] == 1
    assert summary["availability_reported"] is False


def test_provider_subsystem_summary_reports_only_explicit_availability():
    summary = runtime_api._provider_subsystem_summary(
        ["example-provider"],
        [{"name": "example-provider", "status": "degraded", "available": True}],
    )

    assert summary["state"] == "availability_reported"
    assert summary["reported_available_count"] == 1
    assert summary["availability_reported"] is True


def test_providers_endpoint_success_is_not_provider_health(monkeypatch):
    monkeypatch.setattr(
        runtime_api.state_store,
        "get_snapshot",
        lambda: SimpleNamespace(providers={}),
    )
    monkeypatch.setattr(runtime_api.provider_registry, "list_providers", lambda: [])
    monkeypatch.setattr(
        runtime_api.RealitySnapshotService,
        "_get_providers_status",
        lambda self: [],
    )

    result = runtime_api.list_providers()

    assert result["status"] == "success"
    assert result["providers"] == []
    assert result["registered"] == []
    assert result["provider_subsystem"]["state"] == "empty_registry"
    assert result["provider_subsystem"]["availability_reported"] is False
