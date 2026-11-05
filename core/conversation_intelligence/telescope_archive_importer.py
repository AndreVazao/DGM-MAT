from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any

from core.storage.storage_manager import storage_manager
from .pipeline import ConversationIntelligencePipeline


_REDACTION_PATTERNS = (
    (re.compile(r"(?im)([\"']?\b(?:api[ _-]?key|access[ _-]?token|refresh[ _-]?token|client[ _-]?secret|password|passwd|secret|token|cookie|authorization)\b[\"']?\s*[:=]\s*[\"']?)([^\s,;\"']+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
)
_GENERIC_CWD_NAMES = {
    "system32", "syswow64", "windows", "dist", "node_modules", "appdata", "temp",
    "programasgodmode", "devopgodmode", "ai", "projects", "projectflux",
    "projectmind", "clonezip", "workspaces", "desktop", "documents", "downloads",
}


def redact_conversation_text(value: Any) -> str:
    text = str(value or "").replace("\x00", "")
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _safe_date(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "undated"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).strftime("%Y%m%d")
    except ValueError:
        return "undated"


def _safe_leaf(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    leaf = PurePath(value.replace("\\", "/").rstrip("/")).name
    if (
        not leaf
        or leaf.casefold() in _GENERIC_CWD_NAMES
        or leaf.casefold() == Path.home().name.casefold()
        or leaf in {".", ".."}
    ):
        return None
    return leaf[:120]


def _turn_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    try:
        index = int(item.get("turn_index") or 0)
    except (TypeError, ValueError):
        index = 0
    return index, str(item.get("started_at") or "")


class TelescopeArchiveImporter:
    """Import user-approved Telescope CLI transcripts with role separation and durable deduplication.

    This is intentionally separate from TelescopeAdapter: the adapter remains metadata-only.
    Full conversation content is imported only through this explicit archive workflow.
    """

    def __init__(
        self,
        archive_root: str | Path | None = None,
        executable: str | Path | None = None,
        timeout: float = 120.0,
        max_sessions: int = 1000,
        max_turns: int = 5000,
        pipeline: ConversationIntelligencePipeline | None = None,
    ) -> None:
        configured_root = archive_root or os.getenv("DGM_CONVERSATION_ARCHIVE_DIR", "").strip()
        self.archive_root = (
            Path(configured_root).expanduser().resolve()
            if configured_root
            else storage_manager.get_path("cognition") / "conversation_archive"
        )
        self.provider_dir = self.archive_root / "claude-code"
        self.cache_dir = self.archive_root / ".cache"
        self.manifest_path = self.archive_root / "manifest.json"
        self.coverage_path = self.archive_root / "coverage.json"
        self.index_path = self.archive_root / "INDEX.md"
        self.timeout = max(10.0, min(float(timeout), 300.0))
        self.max_sessions = max(1, min(int(max_sessions), 5000))
        self.max_turns = max(1, min(int(max_turns), 20000))
        self.executable = self._resolve_executable(executable)
        cognition = storage_manager.get_path("cognition") / "conversation_intelligence"
        self.pipeline = pipeline or ConversationIntelligencePipeline(
            progress_store_path=cognition / "progress.sqlite3",
            knowledge_store_path=cognition / "knowledge.sqlite3",
        )
        self.provider_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_executable(value: str | Path | None) -> str:
        if value:
            return str(value)
        configured = os.getenv("TELESCOPE_CLI", "").strip()
        if configured:
            return configured
        candidate = Path.home() / ".telescope" / "bin" / "tele.exe"
        if candidate.is_file():
            return str(candidate)
        return shutil.which("tele") or "tele"

    def _run_json(self, *arguments: str) -> Any:
        try:
            result = subprocess.run(
                [self.executable, *arguments],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"telescope_cli_unavailable:{type(exc).__name__}") from None
        if result.returncode != 0 or not (result.stdout or "").strip():
            raise RuntimeError(f"telescope_command_failed:{arguments[0] if arguments else 'unknown'}:{result.returncode}")
        try:
            return json.loads((result.stdout or "").lstrip("\ufeff"))
        except json.JSONDecodeError:
            raise RuntimeError("telescope_json_invalid") from None

    def _export_turns(self) -> list[dict[str, Any]]:
        try:
            with tempfile.TemporaryDirectory(prefix="dgm-telescope-") as temporary_dir:
                temporary = Path(temporary_dir) / "export.json"
                try:
                    result = subprocess.run(
                        [
                            self.executable, "export", "json",
                            "--limit", str(self.max_turns),
                            "--output", str(temporary),
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=self.timeout,
                        check=False,
                    )
                except (OSError, subprocess.SubprocessError) as exc:
                    raise RuntimeError(f"telescope_export_unavailable:{type(exc).__name__}") from None
                if result.returncode != 0 or not temporary.is_file():
                    raise RuntimeError(f"telescope_export_failed:{result.returncode}")
                if temporary.stat().st_size > 50 * 1024 * 1024:
                    raise RuntimeError("telescope_export_exceeds_50mb_limit")
                data = json.loads(temporary.read_text(encoding="utf-8-sig"))
                if isinstance(data, dict):
                    data = data.get("turns") or data.get("items") or data.get("data") or []
                if not isinstance(data, list):
                    raise RuntimeError("telescope_export_shape_invalid")
                return [item for item in data if isinstance(item, dict)]
        except json.JSONDecodeError:
            raise RuntimeError("telescope_export_json_invalid") from None

    @staticmethod
    def _repository_for_cwd(cwd: Any, repositories: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not isinstance(cwd, str) or not cwd.strip():
            return None
        try:
            current = Path(cwd).resolve()
        except (OSError, RuntimeError):
            return None
        matches = []
        for repository in repositories:
            try:
                root = Path(str(repository.get("path", ""))).resolve()
                if current == root or root in current.parents:
                    matches.append((len(root.parts), repository))
            except (OSError, RuntimeError):
                continue
        return max(matches, key=lambda item: item[0])[1] if matches else None

    def _build_markdown(
        self,
        session: dict[str, Any],
        agent_name: str,
        metadata: dict[str, Any],
        turns: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]], int, int]:
        session_id = str(session["session_id"])
        messages: list[dict[str, Any]] = []
        lines = [
            "---",
            "provider: " + json.dumps(agent_name, ensure_ascii=False),
            "conversation_id: " + json.dumps(session_id),
            "project: " + json.dumps(metadata.get("project"), ensure_ascii=False),
            "project_group_basis: " + json.dumps(metadata.get("project_group_basis"), ensure_ascii=False),
            "project_group_confidence: " + str(metadata.get("project_group_confidence", 0.0)),
            "repository: " + json.dumps(metadata.get("repository"), ensure_ascii=False),
            "branch: " + json.dumps(metadata.get("git_branch"), ensure_ascii=False),
            "started_at: " + json.dumps(metadata.get("started_at")),
            "ended_at: " + json.dumps(metadata.get("ended_at")),
            "turn_count: " + str(len(turns)),
            "source: Telescope CLI export",
            "---",
            "",
            "# " + str(metadata.get("title") or ("Claude Code session " + session_id[:8])),
            "",
        ]
        user_count = 0
        assistant_count = 0
        sequence = 0
        for turn_number, turn in enumerate(turns, start=1):
            turn_id = str(turn.get("turn_id") or f"{session_id}-{turn_number}")
            timestamp = turn.get("started_at") or turn.get("ended_at")
            user_text = redact_conversation_text(turn.get("user_message")).strip()
            assistant_text = redact_conversation_text(turn.get("assistant_response")).strip()
            lines += [f"## Interação {turn_number}", ""]
            if timestamp:
                lines += ["Data: " + str(timestamp), ""]
            lines += ["### UTILIZADOR", ""]
            lines += [user_text or "[Pedido do utilizador não capturado pela origem.]", ""]
            if user_text:
                messages.append({
                    "id": turn_id + ":user", "role": "user", "content": user_text,
                    "timestamp": str(timestamp) if timestamp else None,
                })
                user_count += 1
                sequence += 1
            lines += ["### " + agent_name.upper(), ""]
            if assistant_text:
                lines += [assistant_text, ""]
                messages.append({
                    "id": turn_id + ":assistant", "role": "assistant", "content": assistant_text,
                    "timestamp": str(turn.get("ended_at") or timestamp) if (turn.get("ended_at") or timestamp) else None,
                })
                assistant_count += 1
                sequence += 1
            else:
                lines += ["[Resposta da IA não capturada pela origem.]", ""]
        return "\n".join(lines).rstrip() + "\n", messages, user_count, assistant_count

    def import_payload(
        self,
        sessions: list[dict[str, Any]],
        turns: list[dict[str, Any]],
        agents: list[dict[str, Any]] | None = None,
        repositories: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        agent_names = {
            str(agent.get("agent_id") or agent.get("id")): str(
                agent.get("name") or agent.get("display_name") or "AI agent"
            )
            for agent in (agents or [])
            if isinstance(agent, dict) and (agent.get("agent_id") or agent.get("id"))
        }
        turns_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for turn in turns[:self.max_turns]:
            session_id = turn.get("session_id")
            if isinstance(session_id, str) and session_id:
                turns_by_session[session_id].append(turn)

        normalized: list[dict[str, Any]] = []
        try:
            existing_manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            manifest = dict(existing_manifest.get("sessions", {}))
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            manifest = {}
        updated = 0
        unchanged = 0
        user_messages = 0
        assistant_messages = 0
        missing_assistant = 0
        errors = []
        repo_records = repositories or []

        selected_sessions = [
            session for session in sessions[:self.max_sessions]
            if isinstance(session, dict) and isinstance(session.get("session_id"), str)
        ]
        for session in selected_sessions:
            session_id = str(session["session_id"])
            session_turns = sorted(turns_by_session.get(session_id, []), key=_turn_sort_key)
            if not session_turns:
                continue
            agent_id = str(session.get("agent_id") or "")
            agent_name = agent_names.get(agent_id, "Telescope agent")
            repo = self._repository_for_cwd(session.get("cwd"), repo_records)
            project = repo.get("project_group") if repo else _safe_leaf(session.get("cwd"))
            repository_name = repo.get("name") if repo else None
            grouping_basis = repo.get("project_group_basis") if repo else (
                "cwd_leaf_only" if project else "unassigned_cwd"
            )
            grouping_confidence = float(repo.get("project_group_confidence", 0.25)) if repo else (
                0.10 if project else 0.0
            )
            title = (str(project) + " — " + agent_name) if project else (agent_name + " session " + session_id[:8])
            safe_metadata = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "git_branch": session.get("git_branch") if isinstance(session.get("git_branch"), str) else None,
                "status": session.get("status") if isinstance(session.get("status"), str) else None,
                "started_at": session.get("started_at") if isinstance(session.get("started_at"), str) else None,
                "ended_at": session.get("ended_at") if isinstance(session.get("ended_at"), str) else None,
                "turn_count": len(session_turns),
                "project": project,
                "repository": repository_name,
                "project_group_basis": grouping_basis,
                "project_group_confidence": grouping_confidence,
            }
            markdown, messages, users, assistants = self._build_markdown(
                session, agent_name, {**safe_metadata, "title": title}, session_turns
            )
            missing = sum(1 for turn in session_turns if not str(turn.get("assistant_response") or "").strip())
            user_messages += users
            assistant_messages += assistants
            missing_assistant += missing
            fingerprint = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
            date_prefix = _safe_date(safe_metadata["started_at"])
            safe_session_id = re.sub(r"[^A-Za-z0-9._-]+", "_", session_id).strip("._-")[:100]
            if not safe_session_id:
                safe_session_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
            archive_name = f"{date_prefix}-{safe_session_id}.md"
            archive_path = self.provider_dir / archive_name
            previous = manifest.get(session_id)
            if previous and previous.get("fingerprint") == fingerprint and archive_path.is_file():
                unchanged += 1
            else:
                _atomic_write(archive_path, markdown)
                updated += 1

            content = "\n\n".join(message["content"] for message in messages)
            normalized.append({
                "id": session_id,
                "provider": "claude",
                "title": title,
                "content": content,
                "messages": messages,
                "metadata": safe_metadata,
            })
            manifest[session_id] = {
                "fingerprint": fingerprint,
                "archive_file": str(archive_path),
                "provider": agent_name,
                "project": project,
                "repository": repository_name,
                "branch": safe_metadata["git_branch"],
                "started_at": safe_metadata["started_at"],
                "turn_count": len(session_turns),
                "user_messages": users,
                "assistant_messages": assistants,
                "missing_assistant_responses": missing,
            }

        normalized_path = self.cache_dir / "telescope-normalized-redacted.json"
        _atomic_write(normalized_path, json.dumps(normalized, ensure_ascii=False, indent=2))
        pipeline_error = None
        try:
            pipeline_audits = self.pipeline.ingest_file(normalized_path, provider="claude")
        except Exception as exc:
            pipeline_audits = []
            pipeline_error = type(exc).__name__
            errors.append("conversation_intelligence_pipeline:" + pipeline_error)
        total_turns = sum(len(turns_by_session.get(str(s.get("session_id")), [])) for s in selected_sessions)
        imported_sessions = len(normalized)
        coverage = {
            "provider": "claude-code",
            "source": "Telescope CLI export",
            "status": "complete" if imported_sessions == len(selected_sessions) else "partial",
            "pipeline_status": "complete" if pipeline_error is None else "failed",
            "pipeline_error": pipeline_error,
            "discovered_sessions": len(selected_sessions),
            "imported_sessions": imported_sessions,
            "turns": total_turns,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "missing_assistant_responses": missing_assistant,
            "updated_sessions": updated,
            "unchanged_sessions": unchanged,
            "pipeline_audits": len(pipeline_audits),
            "errors": errors,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _atomic_write(self.manifest_path, json.dumps({"sessions": manifest}, ensure_ascii=False, indent=2))
        _atomic_write(self.coverage_path, json.dumps(coverage, ensure_ascii=False, indent=2))
        self._write_index(manifest, coverage)
        return coverage

    def _write_index(self, manifest: dict[str, dict[str, Any]], coverage: dict[str, Any]) -> None:
        lines = [
            "# AI Conversation Archive",
            "",
            "Imported provider: Claude Code via Telescope CLI",
            "Updated: " + str(coverage.get("updated_at")),
            "",
            "## Coverage",
            "",
            "- Sessions: " + str(coverage.get("imported_sessions")) + " / " + str(coverage.get("discovered_sessions")),
            "- Turns: " + str(coverage.get("turns")),
            "- User messages: " + str(coverage.get("user_messages")),
            "- AI responses captured: " + str(coverage.get("assistant_messages")),
            "- AI responses not captured by source: " + str(coverage.get("missing_assistant_responses")),
            "",
            "Each session file preserves UTILIZADOR and AI roles separately. Secret-like values are redacted. Absolute working-directory paths and opaque Telescope metadata are not imported.",
            "",
            "## Sessions",
            "",
        ]
        for session_id, item in sorted(manifest.items(), key=lambda pair: str(pair[1].get("started_at") or "")):
            project = item.get("project") or "Projeto por identificar"
            filename = Path(str(item.get("archive_file") or "")).name
            lines.append(
                "- " + str(item.get("started_at") or "undated") + " — " + str(project)
                + " — " + str(item.get("turn_count")) + " interações — " + filename
            )
        _atomic_write(self.index_path, "\n".join(lines) + "\n")

    def import_latest(self, repositories: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        sessions_data = self._run_json("sessions", "list", "--json", "--limit", str(self.max_sessions))
        sessions = sessions_data if isinstance(sessions_data, list) else sessions_data.get("sessions", []) if isinstance(sessions_data, dict) else []
        agents_data = self._run_json("agents", "list", "--json")
        agents = agents_data if isinstance(agents_data, list) else agents_data.get("agents", []) if isinstance(agents_data, dict) else []
        turns = self._export_turns()
        return self.import_payload(sessions, turns, agents, repositories)

    def get_status(self) -> dict[str, Any]:
        try:
            return json.loads(self.coverage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "provider": "claude-code",
                "source": "Telescope CLI export",
                "status": "not_imported",
                "discovered_sessions": 0,
                "imported_sessions": 0,
                "turns": 0,
            }
