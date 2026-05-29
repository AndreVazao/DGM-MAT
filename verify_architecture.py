import ast
import importlib
import re
import os
from pathlib import Path

ROOT = Path(__file__).parent

def _status(name, ok, details=""):
    status_str = "OK" if ok else "FAILED"
    print(f"{name}_{status_str}")
    return ok

def _python_files(*folders):
    files = []
    for folder in folders:
        base = ROOT / folder
        if base.exists():
            files.extend(base.rglob("*.py"))
    return files

def check_imports():
    modules = {
        "core.memory.memory_manager",
        "core.provider_sync.provider_registry",
        "core.providers.provider_registry",
        "core.runtime.runtime_path_validator",
        "core.runtime.safe_action_queue",
        "core.api.runtime_api",
        "core.realtime.realtime_broadcast",
        "core.observability.logger"
    }

    missing = []
    for module_name in sorted(modules):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            if module_name != "PySide6": missing.append(f"{module_name} ({exc})")

    return _status("IMPORTS", not missing, "; ".join(missing[:8]))

def _api_routes():
    try:
        from core.api.api_server import app
        routes = set()
        for route in app.routes:
            path = getattr(route, "path", None)
            if path:
                routes.add(path)
        return routes
    except Exception:
        return set()

def _cockpit_api_paths():
    paths = set()
    for file_path in _python_files("cockpit"):
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for match in re.findall(r"[/]runtime[/a-zA-Z0-9_{}.-]*", text):
                clean = re.sub(r"[{}][^/]*[}]?", "", match)
                paths.add(clean.rstrip("/"))
        except Exception:
            continue
    return paths

def check_api_contract():
    routes = _api_routes()
    if not routes:
        return _status("API_CONTRACT", False, "Could not load API routes")

    cockpit_paths = _cockpit_api_paths()
    missing = sorted(path for path in cockpit_paths if path and path not in routes and path != '/runtime')

    required = {
        "/runtime/status",
        "/runtime/state",
        "/runtime/truth",
        "/runtime/providers",
        "/runtime/ws",
        "/ws",
    }
    missing_required = sorted(path for path in required if path not in routes)
    return _status("API_CONTRACT", not missing and not missing_required, str(missing + missing_required))

def check_providers():
    try:
        from core.runtime.reality_snapshot import RealitySnapshotService
        providers = RealitySnapshotService()._get_providers_status()
        ok = bool(providers)
        return _status("PROVIDERS", ok)
    except Exception:
        return _status("PROVIDERS", False)

def check_memory():
    try:
        from core.memory.memory_manager import memory_manager
        ok = hasattr(memory_manager, "store_memory") and hasattr(memory_manager, "search_memory")
        return _status("MEMORY", ok)
    except Exception:
        return _status("MEMORY", False)

def check_queue():
    try:
        from core.runtime.safe_action_queue import SafeActionQueue
        queue = SafeActionQueue()
        health = queue.get_health()
        ok = isinstance(health.get("handlers"), list)
        return _status("QUEUE", ok)
    except Exception:
        return _status("QUEUE", False)

def check_cockpit():
    try:
        from core.runtime.runtime_state_store import state_store
        state = state_store.to_dict()
        required_keys = ["system_state", "boot_phase", "node_status"]
        schema_ok = all(k in state for k in required_keys)

        # Check for hydration endpoint
        routes = _api_routes()
        hydration_ok = "/runtime/truth" in routes

        return _status("COCKPIT", schema_ok and hydration_ok)
    except Exception:
        return _status("COCKPIT", False)

def main():
    checks = [
        check_imports,
        check_api_contract,
        check_providers,
        check_memory,
        check_queue,
        check_cockpit,
    ]
    results = [check() for check in checks]
    # No SystemExit(1) to avoid breaking the sandbox flow if some non-critical fails,
    # but the requirement says "must output", so we just print.
    # The user instruction didn't specify exit code but standard is 0/1.
    raise SystemExit(0 if all(results) else 1)

if __name__ == "__main__":
    main()
