# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\operational\\test_backend_service.py
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from scripts.autostart import backend_service


def _urlopen_context(payload: dict):
    response = MagicMock()
    response.status = 200
    response.read.return_value = json.dumps(payload).encode()
    context = MagicMock()
    context.__enter__.return_value = response
    return context


def test_backend_service_defaults_to_loopback_only():
    assert backend_service.DEFAULT_HOST == "127.0.0.1"
    assert backend_service._health_url("127.0.0.1", 8181) == "http://127.0.0.1:8181/health"


def test_health_accepts_only_dgm_mat_identity():
    with patch.object(backend_service, "urlopen", return_value=_urlopen_context({"status": "healthy", "service": "dgm-mat"})):
        assert backend_service._health("127.0.0.1", 8181) == (True, "DGM-MAT API healthy")

    with patch.object(backend_service, "urlopen", return_value=_urlopen_context({"status": "healthy", "service": "other"})):
        healthy, reason = backend_service._health("127.0.0.1", 8181)
    assert healthy is False
    assert "did not identify DGM-MAT" in reason


def test_start_is_idempotent_when_api_is_already_healthy(capsys):
    with patch.object(backend_service, "_health", return_value=(True, "DGM-MAT API healthy")):
        with patch.object(backend_service.subprocess, "Popen") as popen:
            assert backend_service.start("127.0.0.1", 8181) == 0
    popen.assert_not_called()
    assert "ALREADY_RUNNING" in capsys.readouterr().out


def test_process_identity_fails_closed_for_unknown_pid():
    with patch.dict("sys.modules", {"psutil": None}):
        assert backend_service._pid_is_dgm_api(987654321) is False
