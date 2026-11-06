from __future__ import annotations

from pathlib import Path
from typing import Any

from core.runtime.repository_root import resolve_repository_root
from core.storage.storage_manager import storage_manager

from .catalog import VaultCatalog


def bootstrap_vault(
    repository_path: str | Path | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    """Prepare the persistent Vault, import completed local history and snapshot DGM-MAT."""
    vault = VaultCatalog(vault_root or VaultCatalog.default_root())
    vault.register_known_projects()

    repository = Path(repository_path).expanduser().resolve() if repository_path else resolve_repository_root(__file__).resolve()
    existing = vault.get_project("dgm-mat")
    aliases = list(dict.fromkeys([
        *(existing["aliases"] if existing else []),
        "DGM-MAT",
        "DGM MAT",
        "DevOps God Mode",
        "Multi Agent Tool",
    ]))
    project = vault.register_project(
        "dgm-mat",
        existing["name"] if existing else "DGM-MAT",
        repository_path=repository,
        aliases=aliases,
    )

    progress_paths = [
        vault.root / "runtime" / "conversation_intelligence" / "progress.sqlite3",
        storage_manager.get_path("cognition") / "conversation_intelligence" / "progress.sqlite3",
        repository / "storage" / "runtime" / "conversation_intelligence" / "progress.sqlite3",
    ]
    progress = vault.sync_completed_progress(progress_paths)
    tree = vault.snapshot_repository(project["project_id"], repository)
    return {
        "status": "partial" if progress["failures"] else "completed",
        "vault_root": str(vault.root),
        "project": project,
        "progress_sync": progress,
        "repository_tree": tree,
        "summary": vault.summary(),
    }
