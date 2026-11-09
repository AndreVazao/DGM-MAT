"""Evidence-first, bounded, explicitly mapped project context dossiers.

The generator streams SQLite pages and writes Markdown incrementally. A single
conversation snapshot is decoded at a time; original progress rows are read-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path
from typing import TextIO

from .progress_store import ConversationProgressStore


def _safe_project_key(value: str) -> str:
    key = value.strip()
    if not key or key in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", key):
        raise ValueError("project key must be a safe, explicit identifier (letters, digits, dot, underscore, hyphen).")
    return key


def _message_ref(provider: str, conversation_id: str, message_id: str) -> str:
    return f"{provider}:{conversation_id}#message={message_id}"


def _write(stream: TextIO, *lines: str) -> None:
    stream.write("\n".join(lines) + "\n")


def _ordered_messages(conversation: dict) -> Iterator[dict]:
    # Message ordering is normalized at ingestion; sorting only this one
    # conversation avoids retaining messages from other snapshots.
    messages = conversation.get("messages", [])
    if not isinstance(messages, list):
        return iter(())
    return iter(sorted(
        messages,
        key=lambda msg: (int(msg.get("sequence", 0)), str(msg.get("message_id", ""))),
    ))


def _write_project_context(
    stream: TextIO,
    project_key: str,
    conversations: Callable[[], Iterable[dict]],
) -> dict[str, int]:
    project_key = _safe_project_key(project_key)
    conversation_count = message_count = artifact_count = 0
    for item in conversations():
        conversation_count += 1
        conversation = item.get("conversation") or item
        message_count += len(conversation.get("messages", [])) if isinstance(conversation.get("messages"), list) else 0
        artifacts = item.get("artifacts", [])
        artifact_count += len(artifacts) if isinstance(artifacts, list) else 0

    _write(stream,
        f"# Project context: {project_key}", "",
        "> Generated from archived conversation intelligence. This dossier is evidence-linked; it is not an approval record.", "",
        "## Coverage", "",
        f"- Completed conversations included: {conversation_count}",
        f"- Messages retained in snapshots: {message_count}",
        f"- Extracted code candidates: {artifact_count}",
        "- Repository state: not asserted by this generator; verify against a live repository inventory.", "",
        "## User requirements and statements", "")
    user_count = 0
    for item in conversations():
        conversation = item.get("conversation") or item
        provider = str(conversation.get("provider") or item.get("provider") or "unknown")
        cid = str(conversation.get("conversation_id") or item.get("conversation_id") or "")
        title = str(conversation.get("title") or item.get("title") or "Untitled conversation")
        for message in _ordered_messages(conversation):
            if str(message.get("role", "unknown")).casefold() not in {"user", "human"}:
                continue
            body = str(message.get("content", "")).strip()
            if not body:
                continue
            user_count += 1
            ref = _message_ref(provider, cid, str(message.get("message_id", "")))
            _write(stream, f"### {title}", "", body, "", f"Source: `{ref}`")
            _write_message_metadata(stream, message)
            _write(stream, "")
    if not user_count:
        _write(stream, "_No explicit user-role messages are present in the assigned snapshots._", "")

    _write(stream, "## AI proposals and assistant output (not approvals)", "")
    proposal_count = 0
    for item in conversations():
        conversation = item.get("conversation") or item
        provider = str(conversation.get("provider") or item.get("provider") or "unknown")
        cid = str(conversation.get("conversation_id") or item.get("conversation_id") or "")
        title = str(conversation.get("title") or item.get("title") or "Untitled conversation")
        for message in _ordered_messages(conversation):
            if str(message.get("role", "unknown")).casefold() not in {"assistant", "model", "ai"}:
                continue
            body = str(message.get("content", "")).strip()
            if not body:
                continue
            proposal_count += 1
            ref = _message_ref(provider, cid, str(message.get("message_id", "")))
            _write(stream, f"### {title}", "", body, "", f"Source: `{ref}`")
            _write_message_metadata(stream, message)
            _write(stream, "")
    if not proposal_count:
        _write(stream, "_No assistant-role messages are present in the assigned snapshots._", "")

    _write(stream, "## Extracted code candidates", "")
    written_artifacts = 0
    for item in conversations():
        conversation = item.get("conversation") or item
        provider = str(conversation.get("provider") or item.get("provider") or "unknown")
        cid = str(conversation.get("conversation_id") or item.get("conversation_id") or "")
        artifacts = item.get("artifacts", [])
        if not isinstance(artifacts, list):
            continue
        for artifact in sorted(artifacts, key=lambda value: str(value.get("artifact_id", ""))):
            written_artifacts += 1
            language = str(artifact.get("language", "text") or "text").replace("\n", "").replace("\r", "")
            code = str(artifact.get("code", ""))
            fingerprint = str(artifact.get("fingerprint", "")) or hashlib.sha256(code.encode("utf-8")).hexdigest()
            provenance = artifact.get("provenance") if isinstance(artifact.get("provenance"), dict) else {}
            source_message_id = provenance.get("message_id") or artifact.get("message_id")
            source_ref = _message_ref(provider, cid, str(source_message_id)) if source_message_id else f"{provider}:{cid}"
            source_path = provenance.get("source_path") or artifact.get("source_path")
            source_url = provenance.get("source_url") or artifact.get("source_url")
            source_fingerprint = provenance.get("source_fingerprint") or item.get("source_fingerprint")
            _write(stream,
                f"### Candidate `{artifact.get('artifact_id', 'unknown')}`", "",
                f"- Conversation: `{provider}:{cid}`",
                f"- Source message: `{source_ref}`",
                f"- Suggested path: {artifact.get('file_path') or 'not identified'}",
                f"- Source path: {source_path or 'not available'}",
                f"- Source URL: {source_url or conversation.get('url') or 'not available'}",
                f"- Source fingerprint: `{source_fingerprint or 'not available'}`",
                f"- Language: {language}",
                f"- Code fingerprint: `{fingerprint}`",
                "- Repository verification: not performed", "", f"```{language}")
            stream.write(code)
            if not code.endswith("\n"):
                stream.write("\n")
            _write(stream, "```", "")
    if not written_artifacts:
        _write(stream, "_No code candidates were extracted from these conversations._", "")

    _write(stream,
        "## Decisions", "",
        "_No decision is promoted automatically. User statements above are evidence to review; assistant proposals remain separate. Confirmed decisions must be recorded through an explicit user-review workflow._", "",
        "## Conflicts and unresolved items", "",
        "_Not inferred by this generator. Review contradictory user statements and missing context before treating this dossier as authoritative._", "",
        "## Next actions", "",
        "- Review user statements and explicitly confirm current requirements.",
        "- Review AI proposals; record acceptance or rejection separately.",
        "- Compare code candidates against the actual repository and verify file hashes before marking anything recovered.",
        "- Attach repository, branch, commit, test and deployment evidence in a subsequent repository-context pass.", "",
        "## Source manifest", "")
    for item in conversations():
        conversation = item.get("conversation") or item
        _write(stream,
            f"- Provider: `{conversation.get('provider') or item.get('provider') or 'unknown'}`",
            f"  - Conversation ID: `{conversation.get('conversation_id') or item.get('conversation_id') or ''}`",
            f"  - Title: {str(conversation.get('title') or item.get('title') or 'Untitled conversation').replace(chr(10), ' ')}",
            f"  - Processed at: `{item.get('processed_at') or 'unknown'}`",
            f"  - Source fingerprint: `{item.get('source_fingerprint') or 'unknown'}`",
            f"  - Source URL: {conversation.get('url') or 'not supplied'}", "")
    return {"conversation_count": conversation_count, "message_count": message_count, "artifact_count": artifact_count}


def _write_message_metadata(stream: TextIO, message: dict) -> None:
    timestamp = message.get("timestamp")
    source_path = message.get("source_path")
    metadata = message.get("metadata")
    _write(stream, f"- Timestamp: `{timestamp or 'not available'}`")
    _write(stream, f"- Source path: {source_path or 'not available'}")
    if isinstance(metadata, dict) and metadata:
        encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        _write(stream, f"- Message metadata: `{encoded}`")


def render_project_context(project_key: str, conversations: list[dict]) -> str:
    """Compatibility renderer for in-memory callers; production build streams rows."""
    import io
    ordered = sorted(conversations, key=lambda item: (str(item.get("provider", "")), str(item.get("conversation_id", ""))))
    stream = io.StringIO()
    _write_project_context(stream, project_key, lambda: iter(ordered))
    return stream.getvalue().rstrip() + "\n"


class ProjectContextDossierGenerator:
    """Build dossiers from exact mappings, with bounded SQLite reads and streamed output."""

    def __init__(self, progress_store: ConversationProgressStore, output_root: str | Path, batch_size: int = 10):
        if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 100:
            raise ValueError("batch_size must be an integer between 1 and 100")
        self.progress_store = progress_store
        self.output_root = Path(output_root).expanduser().resolve()
        self.batch_size = batch_size

    @staticmethod
    def _mapping_key(provider: str, conversation_id: str) -> str:
        return f"{provider}:{conversation_id}"

    def _project_rows(self, project_key: str, mapping: Mapping[str, str]) -> Iterator[dict]:
        """Yield only completed snapshots explicitly assigned to one project."""
        for row in self.progress_store.iter_conversations(batch_size=self.batch_size):
            if row.get("status") != "complete" or not isinstance(row.get("result"), dict):
                continue
            result = row["result"]
            conversation = result.get("conversation")
            if not isinstance(conversation, dict):
                continue
            provider = str(conversation.get("provider") or row.get("provider") or "unknown")
            conversation_id = str(conversation.get("conversation_id") or row.get("conversation_id") or "")
            if mapping.get(self._mapping_key(provider, conversation_id)) != project_key:
                continue
            yield {
                "provider": provider,
                "conversation_id": conversation_id,
                "title": conversation.get("title") or row.get("title") or "Untitled conversation",
                "url": conversation.get("url"),
                "processed_at": row.get("processed_at"),
                "source_fingerprint": row.get("source_fingerprint"),
                "conversation": conversation,
                "artifacts": result.get("artifacts") if isinstance(result.get("artifacts"), list) else [],
            }

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _atomic_copy(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent))
        os.close(fd)
        try:
            shutil.copyfile(source, temporary)
            os.replace(temporary, destination)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def _write_manifest(
        self, path: Path, project_key: str, mapping: Mapping[str, str], digest: str, count: int
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\\n") as stream:
                header = {
                    "schema_version": 2,
                    "project_key": project_key,
                    "sha256": digest,
                    "conversation_count": count,
                    "mapping_mode": "explicit_only",
                }
                stream.write(json.dumps(header, ensure_ascii=False, sort_keys=True)[:-1])
                stream.write(',"source_ids":[')
                first = True
                for row in self._project_rows(project_key, mapping):
                    source_id = self._mapping_key(row["provider"], row["conversation_id"])
                    if not first:
                        stream.write(",")
                    stream.write(json.dumps(source_id, ensure_ascii=False))
                    first = False
                stream.write("]}\\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def build(self, explicit_mapping: Mapping[str, str]) -> dict:
        """Build assigned projects; unmapped conversations are counted, never guessed."""
        if not isinstance(explicit_mapping, Mapping):
            raise ValueError("explicit_mapping must be a mapping of exact provider:conversation_id keys.")
        normalized: dict[str, str] = {}
        for source_key, project_key in explicit_mapping.items():
            if not isinstance(source_key, str) or ":" not in source_key:
                raise ValueError("mapping keys must be exact 'provider:conversation_id' identifiers.")
            provider, conversation_id = source_key.split(":", 1)
            if not provider.strip() or not conversation_id.strip():
                raise ValueError("mapping keys must include a provider and conversation ID.")
            normalized[source_key] = _safe_project_key(str(project_key))

        seen_projects: set[str] = set()
        unmapped = incomplete = 0
        for row in self.progress_store.iter_conversations(batch_size=self.batch_size):
            if row.get("status") != "complete" or not isinstance(row.get("result"), dict):
                incomplete += 1
                continue
            result = row["result"]
            conversation = result.get("conversation")
            if not isinstance(conversation, dict):
                incomplete += 1
                continue
            provider = str(conversation.get("provider") or row.get("provider") or "unknown")
            cid = str(conversation.get("conversation_id") or row.get("conversation_id") or "")
            source_key = self._mapping_key(provider, cid)
            project_key = normalized.get(source_key)
            if project_key is None:
                unmapped += 1
            else:
                seen_projects.add(project_key)

        outputs = []
        project_keys = sorted(seen_projects)
        for project_key in project_keys:
            project_dir = (self.output_root / project_key).resolve()
            if self.output_root not in project_dir.parents:
                raise ValueError("project output escaped the configured output root.")
            project_dir.mkdir(parents=True, exist_ok=True)
            current_path = project_dir / "PROJECT_CONTEXT.md"
            fd, temporary = tempfile.mkstemp(prefix=f".{current_path.name}.", suffix=".tmp", dir=str(project_dir))
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                    counts = _write_project_context(
                        stream, project_key, lambda key=project_key: self._project_rows(key, normalized)
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
                digest = self._hash_file(Path(temporary))
                history_path = project_dir / "history" / f"{digest}.md"
                if not history_path.exists():
                    self._atomic_copy(Path(temporary), history_path)
                os.replace(temporary, current_path)
            except Exception:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
                raise
            self._write_manifest(project_dir / "manifest.json", project_key, normalized, digest, counts["conversation_count"])
            outputs.append({
                "project_key": project_key, "path": str(current_path), "sha256": digest,
                "conversation_count": counts["conversation_count"],
                "message_count": counts["message_count"], "artifact_count": counts["artifact_count"],
                "batch_size": self.batch_size,
            })
        assigned = sum(item["conversation_count"] for item in outputs)
        return {
            "projects_written": len(outputs), "conversations_assigned": assigned,
            "conversations_unmapped": unmapped, "conversations_incomplete": incomplete,
            "batch_size": self.batch_size,
            "memory_bound": "SQLite fetchmany(batch_size) plus one decoded conversation snapshot and streamed output",
            "outputs": outputs,
        }
