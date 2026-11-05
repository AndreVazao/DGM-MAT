import builtins

from core.runtime.runtime import Runtime


def test_api_import_failure_marks_runtime_degraded(monkeypatch):
    runtime = Runtime.__new__(Runtime)
    runtime.is_degraded = False
    original_import = builtins.__import__

    def fail_api_import(name, *args, **kwargs):
        if name == "core.api.api_server":
            raise ModuleNotFoundError("dgm_mat_connectors is unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_api_import)

    runtime.start_api()

    assert runtime.is_degraded is True
