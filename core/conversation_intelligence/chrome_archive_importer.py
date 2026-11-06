from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .pipeline import ConversationIntelligencePipeline


class ChromeConversationArchiveImporter:
    """Import extension JSON files without modifying or deleting their downloads."""

    SUPPORTED_SCHEMAS = {
        "dgm-mat.chrome-conversation-inventory.v1",
        "dgm-mat.chrome-conversation-capture.v1",
    }

    def __init__(
        self,
        inbox_dir: str | Path | None = None,
        archive_dir: str | Path | None = None,
        pipeline: ConversationIntelligencePipeline | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.inbox_dir = Path(inbox_dir) if inbox_dir else Path.home() / "Downloads" / "DGM-MAT-Conversation-Archive"
        self.archive_dir = Path(archive_dir) if archive_dir else (
            project_root / "storage" / "runtime" / "conversation_archive" / "chrome-imports"
        )
        runtime = project_root / "storage" / "runtime" / "conversation_intelligence"
        self.pipeline = pipeline or ConversationIntelligencePipeline(
            progress_store_path=runtime / "progress.sqlite3",
            knowledge_store_path=runtime / "knowledge.sqlite3",
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _archive_copy(self, source: Path, digest: str) -> Path:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        target = self.archive_dir / source.name
        if target.exists() and self._sha256(target) != digest:
            target = self.archive_dir / f"{source.stem}-{digest[:12]}{source.suffix}"
        if not target.exists():
            shutil.copy2(source, target)
        if self._sha256(target) != digest:
            raise OSError(f"Archived copy SHA-256 mismatch: {target.name}")
        return target

    def import_inbox(self) -> dict[str, Any]:
        if not self.inbox_dir.exists():
            return {
                "status": "inbox_missing",
                "inbox": str(self.inbox_dir),
                "files_seen": 0,
                "files_imported": 0,
                "conversations_imported": 0,
                "messages_imported": 0,
                "files": [],
            }

        files: list[dict[str, Any]] = []
        conversation_count = 0
        message_count = 0
        candidates = sorted(self.inbox_dir.glob("*.json"), key=lambda path: path.name.casefold())
        for source in candidates:
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
                schema = payload.get("schema") if isinstance(payload, dict) else None
                if schema not in self.SUPPORTED_SCHEMAS:
                    files.append({
                        "file": source.name,
                        "status": "ignored_unsupported_schema",
                        "schema": schema,
                    })
                    continue

                digest = self._sha256(source)
                archived = self._archive_copy(source, digest)
                source_provider = (
                    "chrome-history"
                    if schema == "dgm-mat.chrome-conversation-inventory.v1"
                    else "chrome-extension"
                )
                audits = self.pipeline.ingest_file(archived, provider=source_provider)
                conversations = len(audits)
                messages = sum(len(audit.conversation.messages) for audit in audits)
                conversation_count += conversations
                message_count += messages
                files.append({
                    "file": source.name,
                    "archive_path": str(archived),
                    "sha256": digest,
                    "schema": schema,
                    "status": "imported",
                    "conversations": conversations,
                    "messages": messages,
                })
            except Exception as exc:
                files.append({
                    "file": source.name,
                    "status": "failed",
                    "error": type(exc).__name__,
                    "detail": str(exc)[:500],
                })

        imported_files = sum(item["status"] == "imported" for item in files)
        failed_files = sum(item["status"] == "failed" for item in files)
        return {
            "status": "completed" if failed_files == 0 else "partial",
            "inbox": str(self.inbox_dir),
            "archive": str(self.archive_dir),
            "files_seen": len(candidates),
            "files_imported": imported_files,
            "files_failed": failed_files,
            "conversations_imported": conversation_count,
            "messages_imported": message_count,
            "files": files,
        }
