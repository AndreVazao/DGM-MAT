# Path: C:\ProgramasGodMode\DGM-MAT\tests\unit\test_provider_api_truth.py

from types import SimpleNamespace

from core.api import runtime_api


def test_provider_subsystem_summary_reports_empty_registry():
    summary = runtime_api._provider_subsystem_summary([], [])

    assert summary["state"] == "empty_registry"
    assert summary["registered_count"] == 0
    assert summary["registered_names"] == []
    assert summary["availability_observation_count"] == 0
    assert summary["reported_available_count"] == 0
    assert summary["availability_reported"] is False


def test_registered_provider_without_observation_does_not_infer_from_available_flag():
    summary = runtime_api._provider_subsystem_summary(
        ["example-provider"],
        [{"name": "example-provider", "status": "unknown", "available": True}],
    )

    assert summary["state"] == "registered_no_availability_reported"
    assert summary["registered_count"] == 1
    assert summary["availability_observation_count"] == 0
    assert summary["reported_available_count"] == 0
    assert summary["availability_reported"] is False


def test_reported_unavailable_provider_is_still_an_availability_observation():
    summary = runtime_api._provider_subsystem_summary(
        ["example-provider"],
        [{
            "name": "example-provider",
            "status": "error",
            "available": False,
            "availability_observed": True,
        }],
    )

    assert summary["state"] == "availability_reported"
    assert summary["availability_observation_count"] == 1
    assert summary["reported_available_count"] == 0
    assert summary["availability_reported"] is True


def test_provider_subsystem_summary_reports_explicit_available_provider():
    summary = runtime_api._provider_subsystem_summary(
        ["example-provider"],
        [{
            "name": "example-provider",
            "status": "ok",
            "available": True,
            "availability_observed": True,
        }],
    )

    assert summary["state"] == "availability_reported"
    assert summary["availability_observation_count"] == 1
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
    assert result["provider_subsystem"]["availability_observation_count"] == 0
    assert result["provider_subsystem"]["availability_reported"] is False
