from __future__ import annotations

import pytest

from cockpit.mission_status_client import fetch_mission_checkpoint


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
        "http://127.0.0.1:8181/runtime",
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
        "http://127.0.0.1:8181/runtime",
        "mission_b55c3887",
        request=lambda *args, **kwargs: Response(404),
    )
    assert result is None


def test_mission_status_rejects_mismatched_checkpoint():
    with pytest.raises(ValueError, match="checkpoint de missão inválido"):
        fetch_mission_checkpoint(
            "http://127.0.0.1:8181/runtime",
            "mission_b55c3887",
            request=lambda *args, **kwargs: Response(
                200, {"mission_id": "mission_ffffffff", "status": "COMPLETED"}
            ),
        )


def test_mission_status_surfaces_http_error_without_claiming_failure():
    with pytest.raises(RuntimeError, match="HTTP 503"):
        fetch_mission_checkpoint(
            "http://127.0.0.1:8181/runtime",
            "mission_b55c3887",
            request=lambda *args, **kwargs: Response(503),
        )
