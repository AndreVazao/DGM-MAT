# Path: C:\ProgramasGodMode\DGM-MAT\tests\runtime\test_provider_state_reconciliation.py

from core.api import runtime_api
from core.runtime.runtime_state_store import RuntimeTruthState, StateEvents, StateReducer


def test_provider_reconciliation_removes_entries_missing_from_latest_snapshot():
    initial = RuntimeTruthState(
        timestamp=1,
        providers={
            "removed-provider": {"name": "removed-provider", "available": True},
            "retained-provider": {"name": "retained-provider", "available": False},
        },
    )

    result = StateReducer.reduce(
        initial,
        StateEvents.PROVIDERS_RECONCILED,
        {
            "providers": [{"name": "retained-provider", "available": True}],
            "observed_at": 123.0,
        },
    )

    assert set(result.providers) == {"retained-provider"}
    assert result.providers["retained-provider"]["available"] is True
    assert result.reality["providers_observed_at"] == 123.0
    assert result.reality["providers_observation_count"] == 1
    assert "removed-provider" not in result.providers


def test_empty_provider_reconciliation_clears_previous_provider_cache():
    initial = RuntimeTruthState(
        timestamp=1,
        providers={"old-provider": {"name": "old-provider", "available": True}},
    )

    result = StateReducer.reduce(
        initial,
        StateEvents.PROVIDERS_RECONCILED,
        {"providers": [], "observed_at": 456.0},
    )

    assert result.providers == {}
    assert result.reality["providers_observation_count"] == 0


def test_reconciliation_ignores_records_without_valid_names():
    initial = RuntimeTruthState(timestamp=1, providers={})

    result = StateReducer.reduce(
        initial,
        StateEvents.PROVIDERS_RECONCILED,
        {
            "providers": [
                {"name": "valid-provider"},
                {"name": ""},
                {"available": True},
                None,
            ],
            "observed_at": 1.0,
        },
    )

    assert set(result.providers) == {"valid-provider"}


def test_provider_freshness_keeps_recent_observed_availability():
    record = runtime_api._provider_freshness(
        {
            "name": "fresh-provider",
            "status": "ok",
            "healthy": True,
            "available": True,
            "availability_observed": True,
            "health_observed_at": 970.0,
            "snapshot_observed_at": 975.0,
        },
        now=1000.0,
    )

    assert record["freshness_status"] == "fresh"
    assert record["health_observation_age_seconds"] == 30
    assert record["provider_record_age_seconds"] == 25
    assert record["reported_available"] is True
    assert record["available"] is True
    assert record["status"] == "ok"
    assert record["healthy"] is True
    assert record["reported_status"] == "ok"


def test_provider_freshness_marks_old_observation_stale_and_blocks_current_availability():
    record = runtime_api._provider_freshness(
        {
            "name": "stale-provider",
            "status": "ok",
            "healthy": True,
            "available": True,
            "availability_observed": True,
            "health_observed_at": 600.0,
            "snapshot_observed_at": 950.0,
        },
        now=1000.0,
    )

    assert record["freshness_status"] == "stale"
    assert record["health_observation_age_seconds"] == 400
    assert record["reported_available"] is True
    assert record["available"] is False
    assert record["reported_healthy"] is True
    assert record["healthy"] is False
    assert record["reported_status"] == "ok"
    assert record["status"] == "stale"


def test_provider_freshness_does_not_promote_unobserved_available_flag():
    record = runtime_api._provider_freshness(
        {
            "name": "unobserved-provider",
            "status": "ok",
            "healthy": True,
            "available": True,
            "availability_observed": False,
            "health_observed_at": None,
            "snapshot_observed_at": 990.0,
        },
        now=1000.0,
    )

    assert record["freshness_status"] == "unobserved"
    assert record["health_observation_age_seconds"] is None
    assert record["available"] is False
    assert record["healthy"] is False
    assert record["reported_status"] == "ok"
    assert record["status"] == "unknown"


def test_provider_summary_counts_stale_observations_but_not_as_available():
    summary = runtime_api._provider_subsystem_summary(
        ["stale-provider"],
        [{
            "name": "stale-provider",
            "available": False,
            "reported_available": True,
            "availability_observed": True,
            "freshness_status": "stale",
        }],
    )

    assert summary["state"] == "stale_availability_observations"
    assert summary["availability_observation_count"] == 1
    assert summary["stale_observation_count"] == 1
    assert summary["reported_available_count"] == 0
    assert summary["availability_reported"] is True


def test_providers_endpoint_exposes_stale_cached_health_as_unavailable(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        runtime_api.state_store,
        "get_snapshot",
        lambda: SimpleNamespace(providers={
            "stale-provider": {
                "name": "stale-provider",
                "available": True,
                "availability_observed": True,
                "health_observed_at": 600.0,
                "snapshot_observed_at": 950.0,
            },
        }),
    )
    monkeypatch.setattr(
        runtime_api.provider_registry,
        "list_providers",
        lambda: ["stale-provider"],
    )

    result = runtime_api.list_providers()
    provider = result["providers"][0]

    assert result["status"] == "success"
    assert provider["freshness_status"] == "stale"
    assert provider["reported_available"] is True
    assert provider["available"] is False
    assert result["provider_subsystem"]["state"] == "stale_availability_observations"
    assert result["provider_subsystem"]["reported_available_count"] == 0


def test_runtime_state_serialization_applies_freshness_to_all_provider_exports(monkeypatch):
    from core.runtime import provider_freshness

    monkeypatch.setattr(provider_freshness.time, "time", lambda: 1000.0)
    stale_record = {
        "name": "stale-provider",
        "available": True,
        "availability_observed": True,
        "health_observed_at": 600.0,
        "snapshot_observed_at": 950.0,
    }
    state = RuntimeTruthState(
        timestamp=1.0,
        providers={"stale-provider": dict(stale_record)},
        reality={"providers": [dict(stale_record)], "providers_observed_at": 950.0},
    )
    monkeypatch.setattr(runtime_api.state_store, "get_snapshot", lambda: state)

    payload = runtime_api.state_store.to_dict()

    state_record = payload["providers"]["stale-provider"]
    reality_record = payload["reality"]["providers"][0]
    for record in (state_record, reality_record):
        assert record["freshness_status"] == "stale"
        assert record["reported_available"] is True
        assert record["available"] is False


def test_runtime_reality_endpoint_returns_freshness_aware_serialized_state(monkeypatch):
    monkeypatch.setattr(
        runtime_api.state_store,
        "to_dict",
        lambda: {
            "reality": {
                "providers": [{
                    "name": "stale-provider",
                    "available": False,
                    "reported_available": True,
                    "freshness_status": "stale",
                    "availability_observed": True,
                    "health_observed_at": 600.0,
                    "snapshot_observed_at": 950.0,
                }]
            }
        },
    )

    reality = runtime_api.get_runtime_reality()
    provider = reality["providers"][0]

    assert provider["freshness_status"] == "stale"
    assert provider["reported_available"] is True
    assert provider["available"] is False
