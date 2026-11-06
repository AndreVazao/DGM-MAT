from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.vault import VaultCatalog


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy completed DGM-MAT conversation knowledge into the persistent local Vault and snapshot a repository tree."
    )
    parser.add_argument("--vault", default=os.environ.get("DGM_VAULT_PATH") or str(VaultCatalog.default_root()),
                        help="Persistent Vault root; defaults to DGM_VAULT_PATH")
    parser.add_argument("--progress-db", action="append", default=[],
                        help="Progress SQLite database; repeat for multiple stores. If omitted, known runtime stores are discovered.")
    parser.add_argument("--repository", default=str(ROOT), help="Repository root to inventory")
    parser.add_argument("--project-id", default="dgm-mat")
    parser.add_argument("--project-name", default="DGM-MAT")
    parser.add_argument("--aliases", default="DGM-MAT,DGM MAT,AndreOS")
    parser.add_argument("--provider", action="append", default=[], help="Limit sync to provider; may be repeated")
    args = parser.parse_args()
    if not args.vault:
        parser.error("A persistent Vault root could not be resolved")

    vault = VaultCatalog(args.vault)
    vault.register_known_projects()
    existing_project = vault.get_project(args.project_id)
    aliases = list(dict.fromkeys([
        *(existing_project["aliases"] if existing_project else []),
        *[value.strip() for value in args.aliases.split(",") if value.strip()],
    ]))
    project = vault.register_project(
        args.project_id, args.project_name, args.repository, aliases
    )
    if args.progress_db:
        progress_paths = [Path(value).expanduser() for value in args.progress_db]
    else:
        from core.storage.storage_manager import storage_manager
        progress_paths = [
            vault.root / "runtime" / "conversation_intelligence" / "progress.sqlite3",
            storage_manager.get_path("cognition") / "conversation_intelligence" / "progress.sqlite3",
            ROOT / "storage" / "runtime" / "conversation_intelligence" / "progress.sqlite3",
        ]
    sync_report = vault.sync_completed_progress(progress_paths, providers=args.provider)
    tree = vault.snapshot_repository(project["project_id"], args.repository)
    report = {
        "status": "partial" if sync_report["failures"] else "completed",
        "vault": vault.summary(),
        **sync_report,
        "repository_tree": tree,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if sync_report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
