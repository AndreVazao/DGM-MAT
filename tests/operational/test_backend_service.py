# Path: C:\\ProgramasGodMode\\DGM-MAT\\tests\\operational\\test_backend_service.py
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.autostart import backend_service
from core.runtime.runtime import repository_learning_autostart_enabled


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

def test_full_runtime_command_uses_headless_entrypoint():
    command = backend_service._command_for_mode("full", "127.0.0.1", 8181)
    assert command[-2:] == [str(backend_service.PROJECT_ROOT / "main.py"), "--headless"]


def test_full_runtime_is_loopback_only(capsys):
    assert backend_service.start("0.0.0.0", 8181, mode="full") == 2
    assert "loopback-only" in capsys.readouterr().out


def test_full_runtime_refuses_to_start_beside_api_only_process(capsys):
    with patch.object(backend_service, "_health", return_value=(True, "DGM-MAT API healthy")):
        with patch.object(backend_service, "_runtime_readiness", return_value=(False, "runtime status is starting")):
            with patch.object(backend_service.subprocess, "Popen") as popen:
                assert backend_service.start("127.0.0.1", 8181, mode="full") == 2
    popen.assert_not_called()
    assert "No second process was started" in capsys.readouterr().out


def test_full_runtime_command_prefers_installed_frozen_executable(monkeypatch, tmp_path):
    executable = tmp_path / "installed" / "DGM-MAT.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"frozen-runtime")
    monkeypatch.setattr(backend_service, "PROJECT_ROOT", tmp_path)

    assert backend_service._command_for_mode("full", "127.0.0.1", 8181) == [
        str(executable), "--headless"
    ]


def test_full_runtime_identity_accepts_only_installed_frozen_executable(monkeypatch, tmp_path):
    executable = tmp_path / "installed" / "DGM-MAT.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"frozen-runtime")
    monkeypatch.setattr(backend_service, "PROJECT_ROOT", tmp_path)
    process = MagicMock()
    process.is_running.return_value = True
    process.cmdline.return_value = [str(executable), "--headless"]
    process.exe.return_value = str(executable)

    with patch("psutil.Process", return_value=process):
        assert backend_service._pid_is_full_runtime(12345) is True

    process.exe.return_value = str(tmp_path / "other.exe")
    with patch("psutil.Process", return_value=process):
        assert backend_service._pid_is_full_runtime(12345) is False


def test_full_runtime_start_passes_repository_and_python_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(backend_service, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backend_service, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(backend_service, "LOG_FILE", tmp_path / "logs" / "backend-service.log")
    monkeypatch.setattr(backend_service, "_health", lambda *_args: (False, "not running"))
    monkeypatch.setattr(backend_service, "_read_state", lambda: None)
    monkeypatch.setattr(backend_service, "_runtime_readiness", lambda *_args: (True, "ready"))
    monkeypatch.setattr(backend_service, "_write_state", lambda _payload: None)
    process = MagicMock()
    process.pid = 12345
    process.poll.return_value = None

    with patch.object(backend_service.subprocess, "Popen", return_value=process) as popen:
        assert backend_service.start("127.0.0.1", 8181, mode="full") == 0

    child_env = popen.call_args.kwargs["env"]
    assert child_env["DGM_REPOSITORY_ROOT"] == str(tmp_path.resolve())
    assert Path(child_env["DGM_PYTHON_EXECUTABLE"]).is_file()


def test_full_runtime_defaults_to_bounded_read_only_repository_learning():
    environment = {}

    configured = backend_service._configure_runtime_environment(environment, "full")

    assert "DGM_REPOSITORY_LEARNING_ENABLED" not in configured
    assert configured["DGM_REPOSITORY_LEARNING_BATCH_SIZE"] == "2"
    assert configured["DGM_REPOSITORY_LEARNING_MAX_DEPTH"] == "6"
    assert configured["DGM_REPOSITORY_LEARNING_REFRESH_SECONDS"] == "1800"
    assert configured["DGM_REPOSITORY_LEARNING_COMMAND_TIMEOUT"] == "4"
    assert configured["DGM_AUTONOMY_HELP_ENABLED"] == "0"


def test_full_runtime_respects_explicit_operator_overrides():
    environment = {
        "DGM_REPOSITORY_LEARNING_ENABLED": "0",
        "DGM_REPOSITORY_LEARNING_BATCH_SIZE": "1",
        "DGM_AUTONOMY_HELP_ENABLED": "1",
    }

    configured = backend_service._configure_runtime_environment(environment, "full")

    assert configured["DGM_REPOSITORY_LEARNING_ENABLED"] == "0"
    assert configured["DGM_REPOSITORY_LEARNING_BATCH_SIZE"] == "1"
    assert configured["DGM_AUTONOMY_HELP_ENABLED"] == "1"


def test_api_only_mode_does_not_enable_repository_learning():
    environment = {}

    configured = backend_service._configure_runtime_environment(environment, "api")

    assert configured == {}


def test_start_refuses_second_process_when_existing_dgm_process_is_not_healthy(capsys):
    with patch.object(backend_service, "_health", return_value=(False, "not ready")):
        with patch.object(backend_service, "_find_existing_dgm_process", return_value=7552):
            with patch.object(backend_service.subprocess, "Popen") as popen:
                assert backend_service.start("127.0.0.1", 8181, mode="full") == 2
    popen.assert_not_called()
    output = capsys.readouterr().out
    assert "PID 7552 already exists" in output
    assert "no second instance was started" in output


def test_stop_terminates_verified_runtime_child_before_onefile_parent(tmp_path, capsys):
    events = []

    class FakeProcess:
        def __init__(self, pid, children=None):
            self.pid = pid
            self._children = children or []

        def children(self, recursive=True):
            return self._children

        def terminate(self):
            events.append(f"terminate:{self.pid}")

        def wait(self, timeout=None):
            events.append(f"wait:{self.pid}")

        def kill(self):
            events.append(f"kill:{self.pid}")

    child = FakeProcess(7020)
    parent = FakeProcess(11288, [child])

    class FakePsutil:
        class NoSuchProcess(Exception):
            pass
        class TimeoutExpired(Exception):
            pass
        Process = staticmethod(lambda pid: parent if pid == 11288 else child)
        @staticmethod
        def wait_procs(processes, timeout=None):
            return list(processes), []

    state_file = tmp_path / "backend_service.json"
    state_file.write_text('{"pid":11288,"mode":"full","host":"127.0.0.1","port":8181}', encoding="utf-8")
    with patch.object(backend_service, "STATE_FILE", state_file), \
         patch.object(backend_service, "_read_state", return_value={"pid":11288,"mode":"full","host":"127.0.0.1","port":8181}), \
         patch.object(backend_service, "_pid_is_full_runtime", return_value=True), \
         patch.object(backend_service, "_pid_is_dgm_process", return_value=True), \
         patch.object(backend_service, "_health", return_value=(False, "offline")), \
         patch.dict("sys.modules", {"psutil": FakePsutil}):
        assert backend_service.stop() == 0

    assert events.index("terminate:7020") < events.index("terminate:11288")
    assert not state_file.exists()
    assert "process tree rooted at PID 11288" in capsys.readouterr().out


def test_stop_recovers_orphaned_verified_listener_when_recorded_parent_is_gone(tmp_path, capsys):
    events = []

    class FakeProcess:
        pid = 7020
        def children(self, recursive=True):
            return []
        def terminate(self):
            events.append("terminate:7020")
        def wait(self, timeout=None):
            events.append("wait:7020")
        def kill(self):
            events.append("kill:7020")

    process = FakeProcess()

    class FakePsutil:
        class NoSuchProcess(Exception):
            pass
        class TimeoutExpired(Exception):
            pass
        Process = staticmethod(lambda _pid: process)
        @staticmethod
        def wait_procs(processes, timeout=None):
            return list(processes), []

    state_file = tmp_path / "backend_service.json"
    state_file.write_text('{"pid":11288,"mode":"full","host":"127.0.0.1","port":8181}', encoding="utf-8")
    with patch.object(backend_service, "STATE_FILE", state_file), \
         patch.object(backend_service, "_read_state", return_value={"pid":11288,"mode":"full","host":"127.0.0.1","port":8181}), \
         patch.object(backend_service, "_pid_is_full_runtime", return_value=False), \
         patch.object(backend_service, "_find_dgm_listener_pid", return_value=7020), \
         patch.object(backend_service, "_pid_is_dgm_process", return_value=True), \
         patch.object(backend_service, "_health", return_value=(False, "offline")), \
         patch.dict("sys.modules", {"psutil": FakePsutil}):
        assert backend_service.stop() == 0

    assert "terminate:7020" in events
    assert not state_file.exists()
    assert "process tree rooted at PID 7020" in capsys.readouterr().out


def test_full_runtime_service_manager_enables_learning_on_low_memory_hardware_by_default(monkeypatch):
    monkeypatch.delenv("DGM_REPOSITORY_LEARNING_ENABLED", raising=False)
    configured = backend_service._configure_runtime_environment({}, "full")

    assert "DGM_REPOSITORY_LEARNING_ENABLED" not in configured
    assert repository_learning_autostart_enabled(low_memory=True) is True
    assert repository_learning_autostart_enabled(low_memory=False) is True


def test_full_runtime_service_manager_preserves_explicit_learning_opt_in():
    configured = backend_service._configure_runtime_environment(
        {"DGM_REPOSITORY_LEARNING_ENABLED": "1"},
        "full",
    )
    assert configured["DGM_REPOSITORY_LEARNING_ENABLED"] == "1"


def test_api_only_mode_uses_managed_uvicorn_server_entrypoint():
    assert backend_service._command_for_mode("api", "127.0.0.1", 8181) == [
        backend_service.sys.executable,
        "-c",
        "from core.api.api_server import run_api; run_api()",
    ]
