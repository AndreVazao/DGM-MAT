from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.conversation_intelligence.progress_store import ConversationProgressStore
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
    project = vault.register_project(args.project_id, args.project_name, args.repository,
                                     [value.strip() for value in args.aliases.split(",") if value.strip()])
    if args.progress_db:
        progress_paths = [Path(value).expanduser() for value in args.progress_db]
    else:
        from core.storage.storage_manager import storage_manager
        progress_paths = [
            ROOT / "storage" / "runtime" / "conversation_intelligence" / "progress.sqlite3",
            storage_manager.get_path("cognition") / "conversation_intelligence" / "progress.sqlite3",
        ]
    unique_paths = list(dict.fromkeys(path.resolve() for path in progress_paths))
    records = []
    opened_databases = []
    for database_path in unique_paths:
        if not database_path.is_file():
            continue
        records.extend(ConversationProgressStore(database_path).list_conversations())
        opened_databases.append(str(database_path))
    synced = 0
    duplicates = 0
    skipped = 0
    failures: list[dict[str, str]] = []
    for row in records:
        if row.get("status") != "complete" or not isinstance(row.get("result"), dict):
            skipped += 1
            continue
        snapshot = row["result"]
        conversation = snapshot.get("conversation")
        if not isinstance(conversation, dict):
            skipped += 1
            continue
        provider = str(conversation.get("provider") or row.get("provider") or "unknown")
        if args.provider and provider.casefold() not in {item.casefold() for item in args.provider}:
            continue
        try:
            result = vault.archive_conversation(
                provider=provider,
                conversation_id=str(conversation.get("conversation_id") or row.get("conversation_id")),
                title=str(conversation.get("title") or row.get("title") or "Untitled"),
                url=conversation.get("url"),
                content=str(conversation.get("content") or ""),
                messages=conversation.get("messages") or [],
                completeness=str((conversation.get("metadata") or {}).get("completeness")
                                 or (conversation.get("metadata") or {}).get("capture_status") or "unknown"),
                assignment_evidence=["local completed progress-store record", "evidence-based project classifier"],
                metadata=conversation.get("metadata") or {},
                artifacts=snapshot.get("artifacts") or [],
            )
            duplicates += int(result["duplicate"])
            synced += int(not result["duplicate"])
        except Exception as exc:
            failures.append({"provider": provider, "conversation_id": str(row.get("conversation_id")),
                             "error": type(exc).__name__, "detail": str(exc)[:300]})

    tree = vault.snapshot_repository(project["project_id"], args.repository)
    report = {"status": "partial" if failures else "completed", "vault": vault.summary(),
              "progress_databases": opened_databases, "progress_records_seen": len(records), "conversations_archived": synced,
              "duplicates_detected": duplicates, "records_skipped": skipped,
              "failures": failures, "repository_tree": tree}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
