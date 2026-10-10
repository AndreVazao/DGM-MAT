# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\organization\\test_human_intervention_queue.py
from datetime import datetime, timedelta, timezone

import pytest

from core.organization.human_intervention_queue import HumanInterventionQueue


def make_queue(tmp_path):
    return HumanInterventionQueue(tmp_path / "interventions.sqlite3")


def make_request(queue, **overrides):
    values = {
        "mission_id": "mission-1",
        "step_id": "browser-login-confirm",
        "reason": "Operator authentication is required",
        "instructions": "Complete sign-in manually in the legitimate browser session.",
        "risk": "MEDIUM",
    }
    values.update(overrides)
    return queue.create_request(**values)


def test_request_survives_store_recreation(tmp_path):
    queue = make_queue(tmp_path)
    created = make_request(queue)
    recovered = HumanInterventionQueue(tmp_path / "interventions.sqlite3").get_request(created["request_id"])
    assert recovered is not None
    assert recovered["status"] == "WAITING_FOR_USER"
    assert recovered["mission_id"] == "mission-1"
    assert recovered["step_id"] == "browser-login-confirm"


def test_only_one_active_request_per_mission_step(tmp_path):
    queue = make_queue(tmp_path)
    make_request(queue)
    with pytest.raises(ValueError, match="already exists"):
        make_request(queue)


def test_decision_is_bound_to_mission_and_step_and_single_use(tmp_path):
    queue = make_queue(tmp_path)
    request = make_request(queue)
    common = {
        "mission_id": request["mission_id"],
        "step_id": request["step_id"],
        "decision": "APPROVE",
        "actor_id": "paired-device-1",
    }
    assert not queue.submit_decision(request["request_id"], **{**common, "step_id": "other-step"})
    assert queue.submit_decision(request["request_id"], **common)
    assert not queue.submit_decision(request["request_id"], **common)
    assert queue.get_request(request["request_id"])["status"] == "RESPONSE_RECEIVED"


def test_expired_request_cannot_be_approved(tmp_path):
    queue = make_queue(tmp_path)
    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    request = make_request(queue, now=now, ttl_seconds=30)
    accepted = queue.submit_decision(
        request["request_id"],
        mission_id=request["mission_id"],
        step_id=request["step_id"],
        decision="APPROVE",
        actor_id="paired-device-1",
        now=now + timedelta(seconds=31),
    )
    assert not accepted
    assert queue.get_request(request["request_id"], now=now + timedelta(seconds=31))["status"] == "EXPIRED"


def test_decision_requires_verification_before_finalization(tmp_path):
    queue = make_queue(tmp_path)
    request = make_request(queue)
    assert queue.submit_decision(
        request["request_id"],
        mission_id=request["mission_id"],
        step_id=request["step_id"],
        decision="APPROVE",
        actor_id="paired-device-1",
    )
    assert not queue.finalize(request["request_id"], outcome="RESUMED")
    assert queue.mark_verifying(request["request_id"])
    assert not queue.mark_verifying(request["request_id"])
    assert queue.finalize(request["request_id"], outcome="RESUMED")
    assert queue.get_request(request["request_id"])["status"] == "RESUMED"


def test_secret_like_payload_fields_are_not_accepted_or_stored(tmp_path):
    queue = make_queue(tmp_path)
    with pytest.raises(TypeError):
        make_request(queue, password="must-not-be-stored")
    request = make_request(queue)
    assert "password" not in request
    assert "token" not in request


def test_validation_and_expiration_are_bounded(tmp_path):
    queue = make_queue(tmp_path)
    with pytest.raises(ValueError):
        make_request(queue, ttl_seconds=0)
    with pytest.raises(ValueError):
        make_request(queue, risk="UNBOUNDED")
    now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    request = make_request(queue, now=now, ttl_seconds=30)
    assert queue.expire_due(now=now + timedelta(seconds=31)) == 1
    assert queue.get_request(request["request_id"], now=now + timedelta(seconds=31))["status"] == "EXPIRED"
