"""Bounded read-only repository inventory worker for the internal organization.

The worker accepts only a typed inventory request for a repository ID already
allowlisted by the host. It never accepts a filesystem path from the message,
reads source contents, executes commands, writes files, or contacts providers.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Mapping

from core.repository_intelligence.snapshot import (
    RepositorySnapshotError,
    build_inventory,
)
from .models import Message


class RepositoryCartographerWorker:
    """Perform one bounded, read-only inventory for an explicitly allowed repo."""

    agent_id = "agent:repository-cartographer"
    _REQUEST_KEYS = {"schema_version", "operation", "repository_id"}
    _REPOSITORY_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")

    def __init__(
        self,
        *,
        allowed_root: str | Path,
        repositories: Mapping[str, str | Path],
        allowed_senders: tuple[str, ...] = ("agent:hq-orchestrator",),
        max_depth: int = 8,
        max_entries: int = 1000,
        sample_limit: int = 50,
    ) -> None:
        self.allowed_root = Path(allowed_root).expanduser().resolve(strict=True)
        if not self.allowed_root.is_dir():
            raise ValueError("allowed_root must be an existing directory")
        if not 0 <= max_depth <= 20:
            raise ValueError("max_depth must be between 0 and 20")
        if not 1 <= max_entries <= 5000:
            raise ValueError("max_entries must be between 1 and 5000")
        if not 0 <= sample_limit <= 100:
            raise ValueError("sample_limit must be between 0 and 100")
        if not repositories:
            raise ValueError("at least one repository must be allowlisted")

        resolved: dict[str, Path] = {}
        for repository_id, raw_path in repositories.items():
            if not isinstance(repository_id, str) or not self._REPOSITORY_ID.fullmatch(repository_id):
                raise ValueError("repository IDs must be stable safe identifiers")
            repository_root = Path(raw_path).expanduser().resolve(strict=True)
            if not repository_root.is_dir():
                raise ValueError(f"allowlisted repository is not a directory: {repository_id}")
            if not repository_root.is_relative_to(self.allowed_root):
                raise ValueError(f"repository is outside allowed_root: {repository_id}")
            if repository_id in resolved:
                raise ValueError(f"duplicate repository ID: {repository_id}")
            resolved[repository_id] = repository_root

        if not allowed_senders or any(not isinstance(item, str) or not item.strip() for item in allowed_senders):
            raise ValueError("allowed_senders must contain non-empty sender IDs")

        self.repositories = resolved
        self.allowed_senders = frozenset(allowed_senders)
        self.max_depth = max_depth
        self.max_entries = max_entries
        self.sample_limit = sample_limit

    @staticmethod
    def _blocked(reason: str, message: Message) -> dict:
        return {
            "status": "BLOCKED",
            "worker": "repository-cartographer",
            "reason": reason,
            "message_id": message.message_id,
            "mission_id": message.mission_id,
            "source_content_read": False,
            "commands_executed": False,
            "files_modified": False,
            "network_used": False,
        }

    def __call__(self, message: Message) -> dict:
        if message.sender_id not in self.allowed_senders:
            return self._blocked("sender_not_allowlisted", message)
        if not message.mission_id or not message.correlation_id:
            return self._blocked("mission_or_correlation_id_missing", message)
        if not isinstance(message.body, str) or len(message.body.encode("utf-8")) > 4096:
            return self._blocked("request_size_invalid", message)

        try:
            request = json.loads(message.body)
        except (json.JSONDecodeError, UnicodeError):
            return self._blocked("request_json_invalid", message)
        if not isinstance(request, dict) or set(request) != self._REQUEST_KEYS:
            return self._blocked("request_schema_invalid", message)
        if request.get("schema_version") != 1:
            return self._blocked("request_schema_version_unsupported", message)
        if request.get("operation") != "inventory_repository":
            return self._blocked("operation_not_allowed", message)

        repository_id = request.get("repository_id")
        if not isinstance(repository_id, str) or not self._REPOSITORY_ID.fullmatch(repository_id):
            return self._blocked("repository_id_invalid", message)
        repository_root = self.repositories.get(repository_id)
        if repository_root is None:
            return self._blocked("repository_not_allowlisted", message)

        try:
            # build_inventory does not read file contents and does not follow symlinks.
            report = build_inventory(
                repository_root,
                max_depth=self.max_depth,
                max_entries=self.max_entries,
            )
        except (OSError, RepositorySnapshotError):
            return self._blocked("repository_inventory_unavailable", message)

        serialized_entries = [asdict(entry) for entry in report.entries]
        canonical = json.dumps(
            serialized_entries,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        sample = [
            {
                "path": entry.path,
                "kind": entry.kind,
                "size_bytes": entry.size_bytes,
                "suffix": entry.suffix,
            }
            for entry in report.entries
            if not entry.sensitive_name
        ][: self.sample_limit]

        return {
            "status": "COMPLETED_READ_ONLY",
            "worker": "repository-cartographer",
            "repository_id": repository_id,
            "mission_id": message.mission_id,
            "correlation_id": message.correlation_id,
            "generated_at": report.generated_at,
            "counts": {
                "files": report.files,
                "directories": report.directories,
                "entries": len(report.entries),
                "skipped": report.skipped,
                "sensitive_names_detected": sum(entry.sensitive_name for entry in report.entries),
            },
            "sample": sample,
            "sample_truncated": len(sample) < sum(not entry.sensitive_name for entry in report.entries),
            "inventory_limit_reached": len(report.entries) >= self.max_entries,
            "inventory_sha256": hashlib.sha256(canonical).hexdigest(),
            "source_content_read": False,
            "commands_executed": False,
            "files_modified": False,
            "network_used": False,
        }
