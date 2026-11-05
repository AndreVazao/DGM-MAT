from __future__ import annotations

import pytest
import requests

from cockpit.mission_status_client import (
    fetch_mission_checkpoint,
    submit_mission_once,
    wait_for_mission_checkpoint,
)


class Response:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


def test_mission_status_uses_single_durable_checkpoint():
    calls = []

    def request(method, suffix, **kwargs):
        calls.append((method, suffix, kwargs))
        return Response(200, {
            "mission_id": "mission_b55c3887",
            "status": "QUEUED",
            "progress": 0,
            "action_id": 42,
            "action_status": "QUEUED",
        })

    result = fetch_mission_checkpoint(
        "mission_b55c3887",
        request=request,
    )

    assert result["mission_id"] == "mission_b55c3887"
    assert calls == [(
        "GET",
        "/missions/mission_b55c3887",
        {"timeout": (2, 8)},
    )]


def test_mission_status_returns_none_for_not_yet_visible_checkpoint():
    result = fetch_mission_checkpoint(
        "mission_b55c3887",
        request=lambda *args, **kwargs: Response(404),
    )
    assert result is None


def test_mission_status_rejects_mismatched_checkpoint():
    with pytest.raises(ValueError, match="checkpoint de missão inválido"):
        fetch_mission_checkpoint(
            "mission_b55c3887",
            request=lambda *args, **kwargs: Response(
                200, {"mission_id": "mission_ffffffff", "status": "COMPLETED"}
            ),
        )


def test_mission_status_surfaces_http_error_without_claiming_failure():
    with pytest.raises(RuntimeError, match="HTTP 503"):
        fetch_mission_checkpoint(
            "mission_b55c3887",
            request=lambda *args, **kwargs: Response(503),
        )


def test_two_status_timeouts_retry_get_without_resubmitting_mission():
    calls = []
    get_count = 0

    def request(method, suffix, **kwargs):
        nonlocal get_count
        calls.append((method, suffix))
        if method == "POST":
            return Response(201, {
                "status": "success",
                "mission_id": "mission_b55c3887",
                "mission_status": "QUEUED",
            })
        get_count += 1
        if get_count <= 2:
            raise requests.Timeout("temporary status read timeout")
        return Response(200, {
            "mission_id": "mission_b55c3887",
            "status": "FAILED",
            "action_status": "FAILED",
            "error": "Repository scan failed safely",
        })

    created = submit_mission_once(request, "faz uma pesquisa nas repos Barbuidos")
    mission = wait_for_mission_checkpoint(
        created["mission_id"],
        lambda mission_id: fetch_mission_checkpoint(
            mission_id,
            request=request,
        ),
        timeout_seconds=5,
        poll_interval=0,
        sleep=lambda _seconds: None,
    )

    assert mission["status"] == "FAILED"
    assert calls.count(("POST", "/missions")) == 1
    assert calls.count(("GET", "/missions/mission_b55c3887")) == 3


def test_status_poll_stops_at_queued_action_waiting_for_operator():
    mission = wait_for_mission_checkpoint(
        "mission_b55c3887",
        lambda _mission_id: {
            "mission_id": "mission_b55c3887",
            "status": "QUEUED",
            "action_status": "QUEUED",
            "action_id": 42,
        },
        timeout_seconds=1,
        poll_interval=0,
        sleep=lambda _seconds: None,
    )
    assert mission["action_id"] == 42
