# Path: C:\\ProgramasGodMode\\DGM-MAT\\core\\runtime\\provider_freshness.py
"""Shared freshness rules for provider health across API and state exports."""

import time
from typing import Any, Dict, Optional

PROVIDER_OBSERVATION_STALE_AFTER_SECONDS = 300


def provider_freshness(
    provider: Dict[str, Any],
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """Annotate a provider record without promoting missing/stale evidence."""
    current_time = time.time() if now is None else now
    record = dict(provider)

    record_age = None
    snapshot_observed_at = record.get("snapshot_observed_at")
    if isinstance(snapshot_observed_at, (int, float)) and snapshot_observed_at > 0:
        record_age = max(0, int(current_time - snapshot_observed_at))

    health_observed_at = record.get("health_observed_at")
    reported_available = record.get("reported_available", record.get("available")) is True
    reported_healthy = record.get("reported_healthy", record.get("healthy")) is True
    reported_status = record.get("reported_status", record.get("status"))
    health_age = None
    if (
        record.get("availability_observed") is True
        and isinstance(health_observed_at, (int, float))
        and health_observed_at > 0
    ):
        health_age = max(0, int(current_time - health_observed_at))
        freshness_status = (
            "stale"
            if health_age > PROVIDER_OBSERVATION_STALE_AFTER_SECONDS
            else "fresh"
        )
    else:
        freshness_status = "unobserved"

    record["reported_available"] = reported_available
    record["reported_healthy"] = reported_healthy
    record["reported_status"] = reported_status
    record["available"] = reported_available and freshness_status == "fresh"
    record["healthy"] = reported_healthy and freshness_status == "fresh"
    record["freshness_status"] = freshness_status
    record["health_observation_age_seconds"] = health_age
    record["provider_record_age_seconds"] = record_age
    record["freshness_threshold_seconds"] = PROVIDER_OBSERVATION_STALE_AFTER_SECONDS

    if freshness_status == "stale":
        record["status"] = "stale"
    elif freshness_status == "unobserved" and reported_status in {"ok", "active", "degraded"}:
        record["status"] = "unknown"

    return record


def provider_collection_freshness(collection: Any, now: Optional[float] = None) -> Any:
    """Annotate provider collections while preserving dict/list shape and unknown values."""
    if isinstance(collection, dict):
        return {
            key: provider_freshness(value, now=now) if isinstance(value, dict) else value
            for key, value in collection.items()
        }
    if isinstance(collection, list):
        return [
            provider_freshness(value, now=now) if isinstance(value, dict) else value
            for value in collection
        ]
    return collection


def runtime_payload_freshness(
    payload: Dict[str, Any],
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """Apply provider freshness to every provider collection in a serialized runtime state."""
    result = dict(payload)
    if "providers" in result:
        result["providers"] = provider_collection_freshness(result["providers"], now=now)

    reality = result.get("reality")
    if isinstance(reality, dict) and "providers" in reality:
        fresh_reality = dict(reality)
        fresh_reality["providers"] = provider_collection_freshness(
            fresh_reality["providers"], now=now
        )
        result["reality"] = fresh_reality
    return result
