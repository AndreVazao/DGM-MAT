from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")
DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv",
    "venv", "env", "dist", "build", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", ".gradle", "target",
}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript/JSX",
    ".ts": "TypeScript", ".tsx": "TypeScript/TSX", ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin", ".cs": "C#", ".cpp": "C++",
    ".c": "C", ".h": "C/C++ Header", ".hpp": "C++ Header",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL",
    ".sh": "Shell", ".ps1": "PowerShell", ".json": "JSON", ".yaml": "YAML",
    ".yml": "YAML", ".toml": "TOML", ".md": "Markdown", ".xml": "XML",
}
MANIFEST_NAMES = {
    "pyproject.toml", "requirements.txt", "requirements-dev.txt", "package.json",
    "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "poetry.lock",
    "Pipfile", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "composer.json",
    "Gemfile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "CMakeLists.txt", "*.csproj", "*.sln",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _segment(value: str, fallback: str = "item") -> str:
    normalized = SAFE_SEGMENT.sub("-", str(value).strip()).strip(".-_")[:80]
    return normalized or fallback


class VaultCatalog:
    """Indexes immutable local conversation captures and repository snapshots.

    The vault root is deliberately independent of the installed application path.
    Set DGM_VAULT_PATH or pass an explicit path; never place private transcripts in Git.
    """

    SCHEMA_VERSION = 1

    def __init__(self, vault_root: str | Path | None = None) -> None:
        configured = vault_root or os.environ.get("DGM_VAULT_PATH")
        if not configured:
            raise ValueError("Vault path is required; set DGM_VAULT_PATH or pass vault_root")
        self.root = Path(configured).expanduser().resolve()
        self.index_dir = self.root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = self.index_dir / "catalog.sqlite3"
        for folder in ("projects", "providers", "missions", "quarantine"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    repository_path TEXT, aliases_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    provider TEXT NOT NULL, conversation_id TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL, content_fingerprint TEXT NOT NULL,
                    title TEXT NOT NULL, url TEXT, archive_path TEXT NOT NULL, completeness TEXT NOT NULL,
                    message_count INTEGER NOT NULL, project_id TEXT,
                    assignment_status TEXT NOT NULL,
                    assignment_evidence_json TEXT NOT NULL,
                    captured_at TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY(provider, conversation_id, source_fingerprint),
                    FOREIGN KEY(project_id) REFERENCES projects(project_id)
                );
                CREATE INDEX IF NOT EXISTS ix_vault_conversation_project
                    ON conversations(project_id, provider, captured_at);
                CREATE INDEX IF NOT EXISTS ix_vault_conversation_fingerprint
                    ON conversations(source_fingerprint);
                CREATE TABLE IF NOT EXISTS messages (
                    provider TEXT NOT NULL, conversation_id TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL, sequence INTEGER NOT NULL,
                    message_id TEXT NOT NULL, role TEXT NOT NULL,
                    content_fingerprint TEXT NOT NULL, archive_path TEXT NOT NULL,
                    PRIMARY KEY(provider,conversation_id,source_fingerprint,sequence)
                );
                CREATE INDEX IF NOT EXISTS ix_vault_message_fingerprint ON messages(content_fingerprint);
                CREATE TABLE IF NOT EXISTS message_duplicate_candidates (
                    duplicate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_provider TEXT NOT NULL, source_conversation_id TEXT NOT NULL,
                    source_message_id TEXT NOT NULL, source_fingerprint TEXT NOT NULL,
                    canonical_provider TEXT NOT NULL, canonical_conversation_id TEXT NOT NULL,
                    canonical_message_id TEXT NOT NULL, content_fingerprint TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_provider,source_conversation_id,source_message_id,source_fingerprint,
                           canonical_provider,canonical_conversation_id,canonical_message_id)
                );
                CREATE TABLE IF NOT EXISTS code_artifacts (
                    provider TEXT NOT NULL, conversation_id TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL, artifact_id TEXT NOT NULL,
                    language TEXT NOT NULL, content_fingerprint TEXT NOT NULL,
                    archive_path TEXT NOT NULL,
                    PRIMARY KEY(provider,conversation_id,source_fingerprint,artifact_id)
                );
                CREATE INDEX IF NOT EXISTS ix_vault_code_fingerprint ON code_artifacts(content_fingerprint);
                CREATE TABLE IF NOT EXISTS code_duplicate_candidates (
                    duplicate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_provider TEXT NOT NULL, source_conversation_id TEXT NOT NULL,
                    source_artifact_id TEXT NOT NULL, source_fingerprint TEXT NOT NULL,
                    canonical_provider TEXT NOT NULL, canonical_conversation_id TEXT NOT NULL,
                    canonical_artifact_id TEXT NOT NULL, content_fingerprint TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_provider,source_conversation_id,source_artifact_id,source_fingerprint,
                           canonical_provider,canonical_conversation_id,canonical_artifact_id)
                );
                CREATE TABLE IF NOT EXISTS duplicate_candidates (
                    duplicate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_provider TEXT NOT NULL, source_conversation_id TEXT NOT NULL,
                    source_fingerprint TEXT NOT NULL, canonical_provider TEXT NOT NULL,
                    canonical_conversation_id TEXT NOT NULL, canonical_path TEXT NOT NULL,
                    match_type TEXT NOT NULL, created_at TEXT NOT NULL,
                    UNIQUE(source_provider, source_conversation_id, source_fingerprint,
                           canonical_provider, canonical_conversation_id)
                );
                CREATE TABLE IF NOT EXISTS tree_snapshots (
                    snapshot_id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                    repository_path TEXT NOT NULL, tree_fingerprint TEXT NOT NULL,
                    snapshot_path TEXT NOT NULL, file_count INTEGER NOT NULL,
                    language_summary_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id)
                );
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(conversations)")}
            if "content_fingerprint" not in columns:
                db.execute("ALTER TABLE conversations ADD COLUMN content_fingerprint TEXT NOT NULL DEFAULT ''")
            db.execute(
                "INSERT INTO schema_meta(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(self.SCHEMA_VERSION),),
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.database_path), timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=20000")
        return db

    def register_project(
        self, project_id: str, name: str, repository_path: str | Path | None = None,
        aliases: Iterable[str] = (),
    ) -> dict[str, Any]:
        project_id = _segment(project_id, "project").lower()
        if not name.strip():
            raise ValueError("Project name is required")
        alias_values = list(dict.fromkeys([name, project_id, *[str(a) for a in aliases if str(a).strip()]]))
        repo = str(Path(repository_path).expanduser().resolve()) if repository_path else None
        now = _now()
        with self._connect() as db:
            db.execute("""
                INSERT INTO projects(project_id,name,repository_path,aliases_json,created_at,updated_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(project_id) DO UPDATE SET name=excluded.name,
                    repository_path=COALESCE(excluded.repository_path,projects.repository_path),
                    aliases_json=excluded.aliases_json, updated_at=excluded.updated_at
            """, (project_id, name.strip(), repo, _json(alias_values), now, now))
        (self.root / "projects" / project_id).mkdir(parents=True, exist_ok=True)
        return self.get_project(project_id) or {}

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["aliases"] = json.loads(result.pop("aliases_json"))
        return result

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM projects ORDER BY name COLLATE NOCASE").fetchall()
        return [{**dict(row), "aliases": json.loads(row["aliases_json"])} for row in rows]

    def suggest_project(self, title: str, content: str = "") -> dict[str, Any]:
        haystack = f"{title}\n{content}".casefold()
        candidates: list[dict[str, Any]] = []
        for project in self.list_projects():
            hits = [alias for alias in project["aliases"] if alias and alias.casefold() in haystack]
            if hits:
                score = min(0.99, 0.78 + 0.07 * len(set(h.casefold() for h in hits)))
                candidates.append({"project_id": project["project_id"], "name": project["name"],
                                   "confidence": round(score, 2), "matched_aliases": hits})
        candidates.sort(key=lambda item: (-item["confidence"], item["project_id"]))
        if not candidates:
            return {"project_id": None, "status": "unclassified", "candidates": []}
        if len(candidates) > 1 and candidates[0]["confidence"] == candidates[1]["confidence"]:
            return {"project_id": None, "status": "ambiguous", "candidates": candidates}
        return {"project_id": candidates[0]["project_id"], "status": "suggested", "candidates": candidates}

    def archive_conversation(
        self, *, provider: str, conversation_id: str, title: str,
        messages: list[dict[str, Any]], content: str = "", url: str | None = None,
        completeness: str = "unknown", project_id: str | None = None,
        assignment_evidence: Iterable[str] = (), metadata: dict[str, Any] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        provider_key = _segment(provider, "unknown").lower()
        conversation_key = str(conversation_id).strip()
        if not conversation_key:
            raise ValueError("conversation_id is required")
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        if project_id and not self.get_project(project_id):
            raise ValueError(f"Unknown project_id: {project_id}")
        if project_id:
            assignment_status = "explicit"
            evidence = list(assignment_evidence) or ["explicit project assignment"]
        else:
            suggestion = self.suggest_project(title, content)
            project_id = suggestion["project_id"]
            assignment_status = suggestion["status"]
            evidence = list(assignment_evidence) + [
                f"matched aliases: {', '.join(c['matched_aliases'])}"
                for c in suggestion["candidates"][:2]
            ]
        payload = {
            "schema": "dgm-mat.vault-conversation.v1", "provider": provider_key,
            "conversation_id": conversation_key, "title": title or "Untitled conversation",
            "url": url, "completeness": completeness, "messages": messages,
            "content": content, "metadata": metadata or {}, "artifacts": artifacts or [],
            "project_assignment": {"project_id": project_id, "status": assignment_status,
                                   "evidence": evidence},
        }
        raw = (_json(payload) + "\n").encode("utf-8")
        fingerprint = _digest(raw)
        normalized_messages = [
            {"role": str(message.get("role") or "unknown").casefold(),
             "content": re.sub(r"\\s+", " ", str(message.get("content") or "")).strip().casefold()}
            for message in messages
        ]
        has_transcript = bool(content.strip() or any(item["content"] for item in normalized_messages))
        transcript_identity = {
            "messages": [
                {"role": str(message.get("role") or "unknown").casefold(),
                 "content": re.sub(r"\s+", " ", str(message.get("content") or "")).strip().casefold()}
                for message in messages
            ],
            "content": re.sub(r"\s+", " ", content).strip().casefold() if not messages else "",
        }
        content_fingerprint = _digest(_json(transcript_identity).encode("utf-8"))
        with self._connect() as db:
            existing = db.execute(
                "SELECT * FROM conversations WHERE content_fingerprint=? ORDER BY created_at LIMIT 1",
                (content_fingerprint,),
            ).fetchone()
        if existing:
            with self._connect() as db:
                db.execute("""
                    INSERT OR IGNORE INTO duplicate_candidates(
                        source_provider,source_conversation_id,source_fingerprint,
                        canonical_provider,canonical_conversation_id,canonical_path,match_type,created_at
                    ) VALUES(?,?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, existing["provider"],
                      existing["conversation_id"], existing["archive_path"],
                      "byte_identical" if existing["source_fingerprint"] == fingerprint else "same_transcript_content", _now()))
            return {"status": "duplicate", "duplicate": True, "fingerprint": fingerprint,
                    "archive_path": existing["archive_path"], "canonical_provider": existing["provider"],
                    "canonical_conversation_id": existing["conversation_id"],
                    "project_id": existing["project_id"]}

        bucket = (self.root / "projects" / project_id / "conversations") if project_id else (self.root / "quarantine" / "conversations")
        bucket.mkdir(parents=True, exist_ok=True)
        filename = f"{provider_key}--{_segment(conversation_key)}--{fingerprint[:16]}.json"
        destination = bucket / filename
        if destination.exists():
            if _digest(destination.read_bytes()) != fingerprint:
                raise OSError("Vault archive path collision; refusing to overwrite")
        else:
            with destination.open("xb") as stream:
                stream.write(raw)
            if _digest(destination.read_bytes()) != fingerprint:
                destination.unlink(missing_ok=True)
                raise OSError("Vault archive verification failed")
        now = _now()
        with self._connect() as db:
            db.execute("""
                INSERT INTO conversations(provider,conversation_id,source_fingerprint,content_fingerprint,title,url,
                    archive_path,completeness,message_count,project_id,assignment_status,
                    assignment_evidence_json,captured_at,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (provider_key, conversation_key, fingerprint, content_fingerprint, payload["title"], url,
                  str(destination), completeness, len(messages), project_id, assignment_status,
                  _json(evidence), (metadata or {}).get("captured_at") or now, now))
            for sequence, message in enumerate(messages):
                role = str(message.get("role") or "unknown").casefold()
                message_text = re.sub(r"\\s+", " ", str(message.get("content") or "")).strip().casefold()
                if not message_text:
                    continue
                message_fingerprint = _digest((role + "\\0" + message_text).encode("utf-8"))
                message_id = str(message.get("message_id") or message.get("id") or sequence)
                canonical = db.execute(
                    "SELECT provider,conversation_id,message_id,source_fingerprint FROM messages "
                    "WHERE content_fingerprint=? LIMIT 1", (message_fingerprint,)
                ).fetchone()
                db.execute("""
                    INSERT INTO messages(provider,conversation_id,source_fingerprint,sequence,message_id,
                        role,content_fingerprint,archive_path) VALUES(?,?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, sequence, message_id,
                      role, message_fingerprint, str(destination)))
                if canonical:
                    db.execute("""
                        INSERT OR IGNORE INTO message_duplicate_candidates(
                            source_provider,source_conversation_id,source_message_id,source_fingerprint,
                            canonical_provider,canonical_conversation_id,canonical_message_id,
                            content_fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?)
                    """, (provider_key, conversation_key, message_id, fingerprint,
                          canonical["provider"], canonical["conversation_id"], canonical["message_id"],
                          message_fingerprint, now))
            for index, artifact in enumerate(artifacts or []):
                if not isinstance(artifact, dict):
                    continue
                code = str(artifact.get("code") or "")
                if not code.strip():
                    continue
                language = str(artifact.get("language") or "unknown").casefold()
                artifact_fingerprint = str(artifact.get("fingerprint") or _digest((language + "\\0" + code).encode("utf-8")))
                artifact_id = str(artifact.get("artifact_id") or index)
                canonical = db.execute(
                    "SELECT provider,conversation_id,artifact_id FROM code_artifacts "
                    "WHERE content_fingerprint=? LIMIT 1", (artifact_fingerprint,)
                ).fetchone()
                db.execute("""
                    INSERT INTO code_artifacts(provider,conversation_id,source_fingerprint,artifact_id,
                        language,content_fingerprint,archive_path) VALUES(?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, artifact_id,
                      language, artifact_fingerprint, str(destination)))
                if canonical:
                    db.execute("""
                        INSERT OR IGNORE INTO code_duplicate_candidates(
                            source_provider,source_conversation_id,source_artifact_id,source_fingerprint,
                            canonical_provider,canonical_conversation_id,canonical_artifact_id,
                            content_fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?)
                    """, (provider_key, conversation_key, artifact_id, fingerprint,
                          canonical["provider"], canonical["conversation_id"], canonical["artifact_id"],
                          artifact_fingerprint, now))
        return {"status": "archived", "duplicate": False, "fingerprint": fingerprint,
                "archive_path": str(destination), "project_id": project_id,
                "assignment_status": assignment_status, "message_count": len(messages)}

    def snapshot_repository(
        self, project_id: str, repository_path: str | Path, *,
        ignore_names: Iterable[str] = (), max_entries: int = 100_000,
    ) -> dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Unknown project_id: {project_id}")
        root = Path(repository_path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise NotADirectoryError(root)
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        ignored = DEFAULT_IGNORES | set(ignore_names)
        entries: list[dict[str, Any]] = []
        languages: dict[str, int] = {}
        manifests: list[str] = []
        for current, dirs, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            dirs[:] = sorted(
                name for name in dirs
                if name not in ignored and not (current_path / name).is_symlink()
            )
            for name in sorted(files):
                path = current_path / name
                if path.is_symlink():
                    continue
                relative = path.relative_to(root).as_posix()
                stat = path.stat()
                suffix = path.suffix.lower()
                language = LANGUAGES.get(suffix)
                if language:
                    languages[language] = languages.get(language, 0) + 1
                if name in MANIFEST_NAMES or name.endswith((".csproj", ".sln")):
                    manifests.append(relative)
                entries.append({"path": relative, "size": stat.st_size,
                                "extension": suffix, "language": language})
                if len(entries) > max_entries:
                    raise ValueError(f"Repository tree exceeded max_entries={max_entries}; no partial snapshot saved")
        entries.sort(key=lambda item: item["path"].casefold())
        tree = {"schema": "dgm-mat.repository-tree.v1", "project_id": project_id,
                "repository_path": str(root), "generated_at": _now(),
                "file_count": len(entries), "languages": dict(sorted(languages.items())),
                "manifests": sorted(manifests), "entries": entries,
                "ignored_directories": sorted(ignored)}
        raw = (_json(tree) + "\n").encode("utf-8")
        fingerprint = _digest(raw)
        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + fingerprint[:12]
        folder = self.root / "projects" / project_id / "trees"
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / f"{snapshot_id}.json"
        with destination.open("xb") as stream:
            stream.write(raw)
        if _digest(destination.read_bytes()) != fingerprint:
            destination.unlink(missing_ok=True)
            raise OSError("Repository tree snapshot verification failed")
        with self._connect() as db:
            db.execute("""
                INSERT INTO tree_snapshots(snapshot_id,project_id,repository_path,tree_fingerprint,
                    snapshot_path,file_count,language_summary_json,created_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (snapshot_id, project_id, str(root), fingerprint, str(destination),
                  len(entries), _json(tree["languages"]), tree["generated_at"]))
        self.register_project(project_id, project["name"], root, project["aliases"])
        return {"snapshot_id": snapshot_id, "snapshot_path": str(destination),
                "fingerprint": fingerprint, "file_count": len(entries),
                "languages": tree["languages"], "manifests": tree["manifests"]}

    def list_conversations(self, project_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM conversations"
        params: tuple[Any, ...] = ()
        if project_id is not None:
            query += " WHERE project_id=?"
            params = (project_id,)
        query += " ORDER BY provider,title COLLATE NOCASE,captured_at"
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [{**dict(row), "assignment_evidence": json.loads(row["assignment_evidence_json"])} for row in rows]


    def list_messages(self, provider: str | None = None, conversation_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM messages WHERE 1=1"
        params: list[Any] = []
        if provider is not None:
            query += " AND provider=?"
            params.append(provider)
        if conversation_id is not None:
            query += " AND conversation_id=?"
            params.append(conversation_id)
        query += " ORDER BY provider,conversation_id,sequence"
        with self._connect() as db:
            return [dict(row) for row in db.execute(query, params).fetchall()]

    def list_duplicate_messages(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM message_duplicate_candidates ORDER BY duplicate_id"
            ).fetchall()]

    def list_duplicate_code(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM code_duplicate_candidates ORDER BY duplicate_id"
            ).fetchall()]

    def summary(self) -> dict[str, Any]:
        with self._connect() as db:
            conversations = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            projects = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            duplicates = db.execute("SELECT COUNT(*) FROM duplicate_candidates").fetchone()[0]
            message_duplicates = db.execute("SELECT COUNT(*) FROM message_duplicate_candidates").fetchone()[0]
            code_duplicates = db.execute("SELECT COUNT(*) FROM code_duplicate_candidates").fetchone()[0]
            message_count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            code_count = db.execute("SELECT COUNT(*) FROM code_artifacts").fetchone()[0]
            quarantined = db.execute("SELECT COUNT(*) FROM conversations WHERE project_id IS NULL").fetchone()[0]
            snapshots = db.execute("SELECT COUNT(*) FROM tree_snapshots").fetchone()[0]
        return {"vault_root": str(self.root), "projects": projects,
                "conversations": conversations, "duplicate_candidates": duplicates,
                "messages": message_count, "duplicate_messages": message_duplicates,
                "code_artifacts": code_count, "duplicate_code_artifacts": code_duplicates,
                "quarantined_conversations": quarantined, "tree_snapshots": snapshots}
