"""Evidence-first, explicitly mapped project context dossiers.

The generator reads completed conversation snapshots from ConversationProgressStore.
It never guesses project membership, rewrites source archives, or treats assistant
messages as user approvals. Output files are generated artifacts, not source records.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Mapping

from .progress_store import ConversationProgressStore


def _safe_project_key(value: str) -> str:
    key = value.strip()
    if not key or key in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", key):
        raise ValueError("project key must be a safe, explicit identifier (letters, digits, dot, underscore, hyphen).")
    return key


def _message_ref(provider: str, conversation_id: str, message_id: str) -> str:
    return f"{provider}:{conversation_id}#message={message_id}"


def render_project_context(
    project_key: str,
    conversations: list[dict],
) -> str:
    """Render a stable Markdown dossier from explicitly assigned completed snapshots."""
    project_key = _safe_project_key(project_key)
    ordered = sorted(
        conversations,
        key=lambda item: (
            str(item.get("provider", "")),
            str(item.get("conversation_id", "")),
        ),
    )
    lines = [
        f"# Project context: {project_key}",
        "",
        "> Generated from archived conversation intelligence. This dossier is evidence-linked; it is not an approval record.",
        "",
        "## Coverage",
        "",
        f"- Completed conversations included: {len(ordered)}",
        f"- Messages retained in snapshots: {sum(len(item.get('messages', [])) for item in ordered)}",
        f"- Extracted code candidates: {sum(len(item.get('artifacts', [])) for item in ordered)}",
        "- Repository state: not asserted by this generator; verify against a live repository inventory.",
        "",
        "## User requirements and statements",
        "",
    ]
    user_items: list[tuple[str, str, str]] = []
    proposal_items: list[tuple[str, str, str]] = []
    artifact_items: list[tuple[str, dict]] = []
    for item in ordered:
        provider = str(item.get("provider", "unknown"))
        cid = str(item.get("conversation_id", ""))
        title = str(item.get("title", "Untitled conversation"))
        for message in sorted(item.get("messages", []), key=lambda msg: (int(msg.get("sequence", 0)), str(msg.get("message_id", "")))):
            role = str(message.get("role", "unknown")).casefold()
            content = str(message.get("content", "")).strip()
            if not content:
                continue
            ref = _message_ref(provider, cid, str(message.get("message_id", "")))
            entry = (title, ref, content)
            if role in {"user", "human"}:
                user_items.append(entry)
            elif role in {"assistant", "model", "ai"}:
                proposal_items.append(entry)
        for artifact in item.get("artifacts", []):
            artifact_items.append((f"{provider}:{cid}", artifact))

    if user_items:
        for title, ref, content in user_items:
            lines.extend([f"### {title}", "", content, "", f"Source: `{ref}`", ""])
    else:
        lines.extend(["_No explicit user-role messages are present in the assigned snapshots._", ""])

    lines.extend(["## AI proposals and assistant output (not approvals)", ""])
    if proposal_items:
        for title, ref, content in proposal_items:
            lines.extend([f"### {title}", "", content, "", f"Source: `{ref}`", ""])
    else:
        lines.extend(["_No assistant-role messages are present in the assigned snapshots._", ""])

    lines.extend(["## Extracted code candidates", ""])
    if artifact_items:
        for source, artifact in sorted(
            artifact_items,
            key=lambda pair: (pair[0], str(pair[1].get("artifact_id", ""))),
        ):
            language = str(artifact.get("language", "text") or "text")
            code = str(artifact.get("code", ""))
            fingerprint = str(artifact.get("fingerprint", ""))
            file_path = artifact.get("file_path")
            lines.extend([
                f"### Candidate `{artifact.get('artifact_id', 'unknown')}`",
                "",
                f"- Conversation: `{source}`",
                f"- Suggested path: `{file_path}`" if file_path else "- Suggested path: not identified",
                f"- Language: {language}",
                f"- Code fingerprint: `{fingerprint or hashlib.sha256(code.encode('utf-8')).hexdigest()}`",
                "- Repository verification: not performed",
                "",
                f"```{language}",
                code,
                "```",
                "",
            ])
    else:
        lines.extend(["_No code candidates were extracted from these conversations._", ""])

    lines.extend([
        "## Decisions",
        "",
        "_No decision is promoted automatically. User statements above are evidence to review; assistant proposals remain separate. Confirmed decisions must be recorded through an explicit user-review workflow._",
        "",
        "## Conflicts and unresolved items",
        "",
        "_Not inferred by this generator. Review contradictory user statements and missing context before treating this dossier as authoritative._",
        "",
        "## Next actions",
        "",
        "- Review user statements and explicitly confirm current requirements.",
        "- Review AI proposals; record acceptance or rejection separately.",
        "- Compare code candidates against the actual repository and verify file hashes before marking anything recovered.",
        "- Attach repository, branch, commit, test and deployment evidence in a subsequent repository-context pass.",
        "",
        "## Source manifest",
        "",
    ])
    for item in ordered:
        lines.extend([
            f"- Provider: `{item.get('provider', 'unknown')}`",
            f"  - Conversation ID: `{item.get('conversation_id', '')}`",
            f"  - Title: {str(item.get('title', 'Untitled conversation')).replace(chr(10), ' ')}",
            f"  - Processed at: `{item.get('processed_at') or 'unknown'}`",
            f"  - Source fingerprint: `{item.get('source_fingerprint') or 'unknown'}`",
            f"  - Source URL: {item.get('url') or 'not supplied'}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


class ProjectContextDossierGenerator:
    """Build and atomically publish dossiers for exact, operator-supplied mappings."""

    def __init__(self, progress_store: ConversationProgressStore, output_root: str | Path):
        self.progress_store = progress_store
        self.output_root = Path(output_root).expanduser().resolve()

    @staticmethod
    def _mapping_key(provider: str, conversation_id: str) -> str:
        return f"{provider}:{conversation_id}"

    def build(self, explicit_mapping: Mapping[str, str]) -> dict:
        """Build assigned projects; unmapped conversations are counted, never guessed."""
        normalized: dict[str, str] = {}
        for source_key, project_key in explicit_mapping.items():
            if not isinstance(source_key, str) or ":" not in source_key:
                raise ValueError("mapping keys must be exact 'provider:conversation_id' identifiers.")
            normalized[source_key] = _safe_project_key(str(project_key))

        rows = self.progress_store.list_conversations()
        grouped: dict[str, list[dict]] = defaultdict(list)
        unmapped = 0
        incomplete = 0
        for row in rows:
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
            project_key = normalized.get(self._mapping_key(provider, cid))
            if not project_key:
                unmapped += 1
                continue
            grouped[project_key].append({
                "provider": provider,
                "conversation_id": cid,
                "title": conversation.get("title") or row.get("title") or "Untitled conversation",
                "url": conversation.get("url"),
                "processed_at": row.get("processed_at"),
                "source_fingerprint": row.get("source_fingerprint"),
                "messages": conversation.get("messages") if isinstance(conversation.get("messages"), list) else [],
                "artifacts": result.get("artifacts") if isinstance(result.get("artifacts"), list) else [],
            })

        outputs = []
        for project_key in sorted(grouped):
            markdown = render_project_context(project_key, grouped[project_key])
            digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
            project_dir = (self.output_root / project_key).resolve()
            if self.output_root not in project_dir.parents:
                raise ValueError("project output escaped the configured output root.")
            history_dir = project_dir / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            history_path = history_dir / f"{digest}.md"
            if not history_path.exists():
                self._atomic_write(history_path, markdown)
            current_path = project_dir / "PROJECT_CONTEXT.md"
            self._atomic_write(current_path, markdown)
            manifest = {
                "schema_version": 1,
                "project_key": project_key,
                "sha256": digest,
                "conversation_count": len(grouped[project_key]),
                "source_ids": [
                    self._mapping_key(item["provider"], item["conversation_id"])
                    for item in sorted(grouped[project_key], key=lambda x: (x["provider"], x["conversation_id"]))
                ],
                "mapping_mode": "explicit_only",
            }
            self._atomic_write(
                project_dir / "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            outputs.append({
                "project_key": project_key,
                "path": str(current_path),
                "sha256": digest,
                "conversation_count": len(grouped[project_key]),
            })
        return {
            "projects_written": len(outputs),
            "conversations_assigned": sum(item["conversation_count"] for item in outputs),
            "conversations_unmapped": unmapped,
            "conversations_incomplete": incomplete,
            "outputs": outputs,
        }

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
