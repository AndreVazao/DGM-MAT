"""Explicit host-configured registration for bounded read-only repository workers."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Mapping

from .python_source_analyst_worker import PythonSourceAnalystWorker
from .python_test_inventory_worker import PythonTestInventoryWorker
from .repository_cartographer_worker import RepositoryCartographerWorker
from .worker_runtime import WorkerRuntime


WORKSPACE_ROOT_ENV = "DGM_READ_ONLY_WORKSPACE_ROOT"
REPOSITORIES_ENV = "DGM_READ_ONLY_REPOSITORIES"
_REPOSITORY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _load_repository_allowlist(environ: Mapping[str, str]) -> tuple[Path, dict[str, Path]]:
    raw_root = environ.get(WORKSPACE_ROOT_ENV, "").strip()
    raw_repositories = environ.get(REPOSITORIES_ENV, "").strip()
    if not raw_root or not raw_repositories:
        raise ValueError("read_only_worker_configuration_missing")

    root = Path(raw_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("workspace_root_not_directory")

    try:
        config = json.loads(raw_repositories)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("repository_allowlist_json_invalid") from exc
    if not isinstance(config, dict) or not config:
        raise ValueError("repository_allowlist_must_be_nonempty_object")

    repositories: dict[str, Path] = {}
    for repository_id, relative_path in config.items():
        if not isinstance(repository_id, str) or not _REPOSITORY_ID.fullmatch(repository_id):
            raise ValueError("repository_id_invalid")
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("repository_path_must_be_relative_string")
        candidate = Path(relative_path)
        if candidate.is_absolute() or any(part in {"..", ""} for part in candidate.parts):
            raise ValueError("repository_path_must_stay_under_workspace_root")
        resolved = (root / candidate).resolve(strict=True)
        if not resolved.is_dir() or not resolved.is_relative_to(root):
            raise ValueError("repository_path_outside_workspace_root")
        repositories[repository_id] = resolved

    return root, repositories


def register_configured_readonly_workers(
    runtime: WorkerRuntime,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict:
    """Register the two read-only workers only when an operator supplies an allowlist.

    Configuration is host-owned environment state. Message payloads cannot add
    repositories, paths, permissions, or worker registrations.
    """
    source = os.environ if environ is None else environ
    try:
        root, repositories = _load_repository_allowlist(source)
    except (OSError, RuntimeError, ValueError) as exc:
        reason = str(exc) or "repository_configuration_unavailable"
        return {
            "status": "DISABLED",
            "reason": reason,
            "registered_agents": [],
            "repository_count": 0,
        }

    workers = (
        RepositoryCartographerWorker(allowed_root=root, repositories=repositories),
        PythonSourceAnalystWorker(allowed_root=root, repositories=repositories),
        PythonTestInventoryWorker(allowed_root=root, repositories=repositories),
    )
    registered: list[str] = []
    already_registered: list[str] = []
    for worker in workers:
        if runtime.has_handler(worker.agent_id):
            already_registered.append(worker.agent_id)
            continue
        runtime.register_handler(worker.agent_id, worker)
        registered.append(worker.agent_id)

    return {
        "status": "REGISTERED" if registered else "ALREADY_REGISTERED",
        "registered_agents": registered,
        "already_registered_agents": already_registered,
        "repository_count": len(repositories),
        "configuration_source": "operator_environment",
        "code_execution_enabled": False,
        "write_capability_enabled": False,
        "network_capability_enabled": False,
    }
