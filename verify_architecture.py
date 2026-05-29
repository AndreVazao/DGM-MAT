import ast
import importlib
import re
from pathlib import Path


ROOT = Path(__file__).parent


def _status(name, ok, details=""):
    print(f"{name}_{'OK' if ok else 'FAILED'}" + (f": {details}" if details else ""))
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
        "core.providers.provider_registry",
        "core.provider_sync.provider_registry",
        "core.runtime.runtime_path_validator",
        "core.runtime.safe_action_queue",
        "core.api.runtime_api",
    }

    for file_path in _python_files("core"):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_import_module = (
                    isinstance(func, ast.Attribute)
                    and func.attr == "import_module"
                )
                is_dependency_loader = (
                    isinstance(func, ast.Attribute)
                    and func.attr == "validate_dependency"
                )
                if (is_import_module or is_dependency_loader) and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        modules.add(arg.value)

    missing = []
    for module_name in sorted(modules):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            missing.append(f"{module_name} ({exc})")

    return _status("IMPORTS", not missing, "; ".join(missing[:8]))


def _api_routes():
    from core.api.api_server import app

    routes = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            routes.add(path)
    return routes


def _cockpit_api_paths():
    paths = set()
    for file_path in _python_files("cockpit"):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in re.findall(r"[/]runtime[/a-zA-Z0-9_{}.-]*", text):
            clean = re.sub(r"[{}][^/]*[}]?", "", match)
            paths.add(clean.rstrip("/"))
    return paths


def check_api_contract():
    routes = _api_routes()
    cockpit_paths = _cockpit_api_paths()
    missing = sorted(path for path in cockpit_paths if path and path not in routes)
    required = {
        "/runtime/status",
        "/runtime/state",
        "/runtime/truth",
        "/runtime/providers",
        "/runtime/memory",
        "/runtime/memory/stats",
        "/runtime/governance",
        "/runtime/autonomy",
        "/runtime/queue",
        "/runtime/ws",
        "/ws",
    }
    missing_required = sorted(path for path in required if path not in routes)
    return _status("API_CONTRACT", not missing and not missing_required, str(missing + missing_required))


def check_providers():
    from core.runtime.reality_snapshot import RealitySnapshotService

    providers = RealitySnapshotService()._get_providers_status()
    ok = bool(providers) and all("name" in provider for provider in providers)
    return _status("PROVIDERS", ok, f"{len(providers)} providers visible")


def check_memory():
    from core.memory.memory_manager import memory_manager

    ok = hasattr(memory_manager, "store_memory") and hasattr(memory_manager, "search_memory")
    return _status("MEMORY", ok)


def check_queue():
    from core.runtime.safe_action_queue import SafeActionQueue

    queue = SafeActionQueue()
    health = queue.get_health()
    ok = "MISSION_EXECUTION" in health.get("handlers", []) or isinstance(health.get("handlers"), list)
    return _status("QUEUE", ok, str(health))


def check_cockpit():
    routes = _api_routes()
    ok = "/ws" in routes and "/runtime/providers" in routes and "/runtime/state" in routes
    return _status("COCKPIT", ok)


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
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
