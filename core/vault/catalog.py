from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")
KNOWN_PROJECTS: tuple[dict[str, Any], ...] = (
    {"project_id": "dgm-mat", "name": "DGM-MAT",
     "aliases": ("DGM-MAT", "DevOps God Mode", "Multi Agent Tool")},
    {"project_id": "dgm-hub", "name": "DGM-HUB",
     "aliases": ("DGM-HUB", "DGM Hub", "Hub Meeting Room")},
    {"project_id": "dgm-mcp", "name": "DGM-MCP",
     "aliases": ("DGM-MCP", "DGM MCP")},
    {"project_id": "andreos-memory", "name": "AndreOS Memory",
     "aliases": ("AndreOS Memory", "AndreOS-Memory", "AndreOS MEME")},
    {"project_id": "dgm-mat-mobile", "name": "DGM-MAT-Mobile",
     "aliases": ("DGM-MAT-Mobile", "DGM-MAT Mobile", "DGM MAT Mobile")},
    {"project_id": "vazao-evse", "name": "VAZAO EVSE Platform",
     "aliases": ("VAZAO-EVSE-Platform", "VAZAO EVSE", "TestStation V1")},
    {"project_id": "vazao-sovereign-trader", "name": "VazaoSovereignTrader",
     "aliases": ("VazaoSovereignTrader", "Vazão Sovereign Trader")},
    {"project_id": "office-kit", "name": "Office Kit",
     "aliases": ("Office Kit", "DGM Office Kit")},
    {"project_id": "family-dgm", "name": "Family DGM",
     "aliases": ("Family DGM",)},
)

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


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _segment(value: str, fallback: str = "item") -> str:
    normalized = SAFE_SEGMENT.sub("-", str(value).strip()).strip(".-_")[:80]
    return normalized or fallback


def _format_tree(root_name: str, entries: list[dict[str, Any]]) -> str:
    tree: dict[str, Any] = {}
    for entry in entries:
        parts = str(entry["path"]).split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = None

    lines = [f"{root_name}/"]

    def render(node: dict[str, Any], prefix: str) -> None:
        items = sorted(node.items(), key=lambda item: (item[1] is None, item[0].casefold()))
        for index, (name, child) in enumerate(items):
            last = index == len(items) - 1
            connector = "└── " if last else "├── "
            is_directory = isinstance(child, dict)
            lines.append(prefix + connector + name + ("/" if is_directory else ""))
            if is_directory:
                render(child, prefix + ("    " if last else "│   "))

    render(tree, "")
    return "\n".join(lines) + "\n"


class VaultCatalog:
    """Indexes immutable local conversation captures and repository snapshots.

    The vault root is deliberately independent of the installed application path.
    Set DGM_VAULT_PATH or pass an explicit path; never place private transcripts in Git.
    """

    SCHEMA_VERSION = 3

    @staticmethod
    def default_root() -> Path:
        """Stable per-user data location, independent of the executable and Git checkout."""
        configured = os.environ.get("DGM_VAULT_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data)
        else:
            data_home = os.environ.get("XDG_DATA_HOME")
            base = Path(data_home) if data_home else Path.home() / ".local" / "share"
        return (base / "DGM-MAT" / "Vault").expanduser().resolve()

    def __init__(self, vault_root: str | Path | None = None) -> None:
        configured = vault_root or os.environ.get("DGM_VAULT_PATH")
        if not configured:
            raise ValueError("Vault path is required; set DGM_VAULT_PATH or pass vault_root")
        self.root = Path(configured).expanduser().resolve()
        application_root = Path(__file__).resolve().parents[2]
        try:
            self.root.relative_to(application_root)
        except ValueError:
            pass
        else:
            raise ValueError("Vault root must be outside the DGM-MAT application repository")
        if any((parent / ".git").exists() for parent in (self.root, *self.root.parents)):
            raise ValueError("Vault root must be outside every Git worktree/repository")
        self.index_dir = self.root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = self.index_dir / "catalog.sqlite3"
        for folder in ("projects", "providers", "missions", "quarantine"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            has_schema_meta = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_meta'"
            ).fetchone()
            if has_schema_meta:
                existing_version = db.execute(
                    "SELECT value FROM schema_meta WHERE key='schema_version'"
                ).fetchone()
                if existing_version and int(existing_version["value"]) > self.SCHEMA_VERSION:
                    raise RuntimeError(
                        f"Vault schema {existing_version['value']} is newer than this DGM-MAT build "
                        f"(supported: {self.SCHEMA_VERSION}); refusing to downgrade or modify it"
                    )
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
                CREATE TABLE IF NOT EXISTS github_repository_refs (
                    canonical_url TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    verification_status TEXT NOT NULL CHECK(verification_status IN (
                        'pending_verification','verified_public','not_found_or_private',
                        'rate_limited','unavailable'
                    )),
                    html_url TEXT,
                    description TEXT,
                    default_branch TEXT,
                    is_archived INTEGER,
                    verified_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_github_refs_status
                    ON github_repository_refs(verification_status, updated_at);
                CREATE TABLE IF NOT EXISTS github_repository_ref_sources (
                    canonical_url TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    conversation_url TEXT,
                    conversation_title TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    PRIMARY KEY(canonical_url, provider, conversation_id, message_id),
                    FOREIGN KEY(canonical_url) REFERENCES github_repository_refs(canonical_url)
                );
                CREATE INDEX IF NOT EXISTS ix_github_ref_sources_conversation
                    ON github_repository_ref_sources(provider, conversation_id);
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

    def register_known_projects(self) -> list[dict[str, Any]]:
        """Seed known projects without overwriting user-added aliases or repo paths."""
        registered = []
        for item in KNOWN_PROJECTS:
            existing = self.get_project(item["project_id"])
            aliases = list(dict.fromkeys([
                *(existing["aliases"] if existing else []),
                item["name"], item["project_id"], *item["aliases"],
            ]))
            registered.append(self.register_project(
                item["project_id"],
                existing["name"] if existing else item["name"],
                repository_path=existing.get("repository_path") if existing else None,
                aliases=aliases,
            ))
        return registered

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
        title_text = title.casefold()
        content_text = content.casefold()
        candidates: list[dict[str, Any]] = []
        for project in self.list_projects():
            title_hits = [alias for alias in project["aliases"] if alias and alias.casefold() in title_text]
            content_hits = [alias for alias in project["aliases"] if alias and alias.casefold() in content_text]
            hits = list(dict.fromkeys([*title_hits, *content_hits]))
            if not hits:
                continue
            # A project named in the title is stronger evidence than a mention
            # buried in the transcript; within that source, prefer the longest alias.
            strongest_source = title_hits or content_hits
            longest = max(len(alias) for alias in strongest_source)
            strongest = [alias for alias in strongest_source if len(alias) == longest]
            base = 0.88 if title_hits else 0.74
            score = min(0.99, base + 0.003 * min(longest, 30) + 0.015 * (len(strongest) - 1))
            candidates.append({
                "project_id": project["project_id"],
                "name": project["name"],
                "confidence": round(score, 3),
                "matched_aliases": hits,
                "strongest_aliases": strongest,
                "evidence_source": "title" if title_hits else "content",
            })
        candidates.sort(key=lambda item: (-item["confidence"], item["project_id"]))
        if not candidates:
            return {"project_id": None, "status": "unclassified", "candidates": []}
        if len(candidates) > 1 and candidates[0]["confidence"] == candidates[1]["confidence"]:
            return {"project_id": None, "status": "ambiguous", "candidates": candidates}
        return {"project_id": candidates[0]["project_id"], "status": "suggested", "candidates": candidates}

    def archive_raw_capture(self, *, provider: str, source_id: str, raw_bytes: bytes) -> dict[str, Any]:
        """Keep the exact browser/API capture bytes in the portable Vault."""
        if not isinstance(raw_bytes, bytes) or not raw_bytes:
            raise ValueError("raw_bytes must be non-empty bytes")
        provider_key = _segment(provider, "unknown").lower()
        source_key = _segment(source_id, "source")
        fingerprint = _digest(raw_bytes)
        folder = self.root / "providers" / "browser-captures" / provider_key
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / f"{source_key}--{fingerprint[:16]}.json"
        if destination.exists():
            if _digest(destination.read_bytes()) != fingerprint:
                raise OSError("Vault raw capture collision; refusing to overwrite")
            return {"status": "duplicate", "sha256": fingerprint, "archive_path": str(destination)}
        with destination.open("xb") as stream:
            stream.write(raw_bytes)
        if _digest(destination.read_bytes()) != fingerprint:
            destination.unlink(missing_ok=True)
            raise OSError("Vault raw capture verification failed")
        return {"status": "archived", "sha256": fingerprint, "archive_path": str(destination)}

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
             "content": re.sub(r"\s+", " ", str(message.get("content") or "")).strip().casefold()}
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
        if not has_transcript:
            # Empty/metadata-only captures are not evidence of duplicate conversations.
            # Keep them idempotent for the same provider/source, but never collapse
            # unrelated empty conversations across providers or projects.
            transcript_identity["empty_source"] = [provider_key, conversation_key, fingerprint]
        content_fingerprint = _digest(_json(transcript_identity).encode("utf-8"))
        with self._connect() as db:
            source_existing = db.execute(
                "SELECT * FROM conversations WHERE provider=? AND conversation_id=? AND source_fingerprint=?",
                (provider_key, conversation_key, fingerprint),
            ).fetchone()
            canonical_conversation = db.execute(
                "SELECT * FROM conversations WHERE content_fingerprint=? ORDER BY created_at LIMIT 1",
                (content_fingerprint,),
            ).fetchone() if has_transcript else None
        if source_existing:
            # Re-importing the exact same source is idempotent. Record the replay
            # while keeping the original immutable transcript as the canonical item.
            with self._connect() as db:
                db.execute("""
                    INSERT OR IGNORE INTO duplicate_candidates(
                        source_provider,source_conversation_id,source_fingerprint,
                        canonical_provider,canonical_conversation_id,canonical_path,match_type,created_at
                    ) VALUES(?,?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, provider_key,
                      conversation_key, source_existing["archive_path"], "byte_identical", _now()))
            self.record_github_repository_references(
                provider=provider_key, conversation_id=conversation_key, title=title,
                conversation_url=url, messages=messages,
            )
            return {"status": "duplicate", "duplicate": True, "source_reused": True,
                    "fingerprint": fingerprint, "archive_path": source_existing["archive_path"],
                    "project_id": source_existing["project_id"]}

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
            if canonical_conversation:
                db.execute("""
                    INSERT OR IGNORE INTO duplicate_candidates(
                        source_provider,source_conversation_id,source_fingerprint,
                        canonical_provider,canonical_conversation_id,canonical_path,match_type,created_at
                    ) VALUES(?,?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, canonical_conversation["provider"],
                      canonical_conversation["conversation_id"], canonical_conversation["archive_path"],
                      "byte_identical" if canonical_conversation["source_fingerprint"] == fingerprint else "same_transcript_content", now))
            for sequence, message in enumerate(messages):
                role = str(message.get("role") or "unknown").casefold()
                message_text = re.sub(r"\s+", " ", str(message.get("content") or "")).strip().casefold()
                if not message_text:
                    continue
                message_fingerprint = _digest((role + "\0" + message_text).encode("utf-8"))
                message_id = str(message.get("message_id") or message.get("id") or sequence)
                canonical_message = db.execute(
                    "SELECT provider,conversation_id,message_id,source_fingerprint FROM messages "
                    "WHERE content_fingerprint=? LIMIT 1", (message_fingerprint,)
                ).fetchone()
                db.execute("""
                    INSERT INTO messages(provider,conversation_id,source_fingerprint,sequence,message_id,
                        role,content_fingerprint,archive_path) VALUES(?,?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, sequence, message_id,
                      role, message_fingerprint, str(destination)))
                if canonical_message:
                    db.execute("""
                        INSERT OR IGNORE INTO message_duplicate_candidates(
                            source_provider,source_conversation_id,source_message_id,source_fingerprint,
                            canonical_provider,canonical_conversation_id,canonical_message_id,
                            content_fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?)
                    """, (provider_key, conversation_key, message_id, fingerprint,
                          canonical_message["provider"], canonical_message["conversation_id"], canonical_message["message_id"],
                          message_fingerprint, now))
            for index, artifact in enumerate(artifacts or []):
                if not isinstance(artifact, dict):
                    continue
                code = str(artifact.get("code") or "")
                if not code.strip():
                    continue
                language = str(artifact.get("language") or "unknown").casefold()
                artifact_fingerprint = str(artifact.get("fingerprint") or _digest((language + "\0" + code).encode("utf-8")))
                artifact_id = str(artifact.get("artifact_id") or index)
                canonical_artifact = db.execute(
                    "SELECT provider,conversation_id,artifact_id FROM code_artifacts "
                    "WHERE content_fingerprint=? LIMIT 1", (artifact_fingerprint,)
                ).fetchone()
                db.execute("""
                    INSERT INTO code_artifacts(provider,conversation_id,source_fingerprint,artifact_id,
                        language,content_fingerprint,archive_path) VALUES(?,?,?,?,?,?,?)
                """, (provider_key, conversation_key, fingerprint, artifact_id,
                      language, artifact_fingerprint, str(destination)))
                if canonical_artifact:
                    db.execute("""
                        INSERT OR IGNORE INTO code_duplicate_candidates(
                            source_provider,source_conversation_id,source_artifact_id,source_fingerprint,
                            canonical_provider,canonical_conversation_id,canonical_artifact_id,
                            content_fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?)
                    """, (provider_key, conversation_key, artifact_id, fingerprint,
                          canonical_artifact["provider"], canonical_artifact["conversation_id"], canonical_artifact["artifact_id"],
                          artifact_fingerprint, now))
        self.record_github_repository_references(
            provider=provider_key, conversation_id=conversation_key, title=title,
            conversation_url=url, messages=messages,
        )
        return {"status": "archived_duplicate" if canonical_conversation else "archived",
                "duplicate": bool(canonical_conversation), "source_reused": False, "fingerprint": fingerprint,
                "archive_path": str(destination), "project_id": project_id,
                "assignment_status": assignment_status, "message_count": len(messages),
                "canonical_provider": canonical_conversation["provider"] if canonical_conversation else None,
                "canonical_conversation_id": canonical_conversation["conversation_id"] if canonical_conversation else None,
                "canonical_archive_path": canonical_conversation["archive_path"] if canonical_conversation else None}

    @staticmethod
    def _extract_github_repository_links(text: str) -> list[dict[str, str]]:
        """Extract only canonical github.com owner/repository URLs; ignore other hosts."""
        pattern = re.compile(
            r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^\s<>\"']*)?",
            re.IGNORECASE,
        )
        found: dict[str, dict[str, str]] = {}
        for raw in pattern.findall(str(text or "")):
            candidate = raw.rstrip(".,;:!?)]}\u00bb")
            try:
                parsed = urlsplit(candidate)
                port = parsed.port
            except ValueError:
                continue
            if parsed.scheme.casefold() != "https" or (parsed.hostname or "").casefold() not in {"github.com", "www.github.com"}:
                continue
            if parsed.username or parsed.password or port not in (None, 443):
                continue
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) < 2:
                continue
            owner, repository = parts[0], parts[1]
            if repository.casefold().endswith(".git"):
                repository = repository[:-4]
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repository):
                continue
            if owner in {".", ".."} or repository in {".", ".."}:
                continue
            canonical = f"https://github.com/{owner.casefold()}/{repository.casefold()}"
            found[canonical] = {"canonical_url": canonical, "owner": owner, "repository": repository}
        return list(found.values())

    def record_github_repository_references(
        self, *, provider: str, conversation_id: str, title: str,
        conversation_url: str | None, messages: list[dict[str, Any]],
    ) -> int:
        """Persist repository references with message provenance; never verifies by URL shape alone."""
        now = _now()
        occurrences: dict[tuple[str, str], dict[str, str]] = {}
        for sequence, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            message_id = str(message.get("message_id") or message.get("id") or sequence)[:200]
            body = str(message.get("content") or "")
            for item in self._extract_github_repository_links(body):
                occurrences[(item["canonical_url"], message_id)] = item
        for item in self._extract_github_repository_links(title):
            occurrences[(item["canonical_url"], "__conversation_title__")] = item
        if not occurrences:
            return 0
        with self._connect() as db:
            for (canonical, message_id), item in occurrences.items():
                db.execute("""
                    INSERT INTO github_repository_refs(
                        canonical_url,owner,repository,verification_status,created_at,updated_at
                    ) VALUES(?,?,?,'pending_verification',?,?)
                    ON CONFLICT(canonical_url) DO UPDATE SET
                        updated_at=excluded.updated_at
                """, (canonical, item["owner"], item["repository"], now, now))
                db.execute("""
                    INSERT OR IGNORE INTO github_repository_ref_sources(
                        canonical_url,provider,conversation_id,message_id,conversation_url,
                        conversation_title,first_seen_at
                    ) VALUES(?,?,?,?,?,?,?)
                """, (canonical, provider, conversation_id, message_id,
                      conversation_url, str(title or "Untitled")[:500], now))
        return len(occurrences)

    def list_github_repository_references(
        self, *, limit: int = 100, offset: int = 0,
        verification_status: str | None = None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("Invalid reference pagination")
        allowed = {"pending_verification", "verified_public", "not_found_or_private", "rate_limited", "unavailable"}
        if verification_status is not None and verification_status not in allowed:
            raise ValueError("Unsupported verification status")
        where = " WHERE verification_status=?" if verification_status else ""
        params: tuple[Any, ...] = (verification_status,) if verification_status else ()
        with self._connect() as db:
            total = db.execute("SELECT COUNT(*) FROM github_repository_refs" + where, params).fetchone()[0]
            rows = db.execute(
                "SELECT * FROM github_repository_refs" + where +
                " ORDER BY CASE verification_status WHEN 'pending_verification' THEN 0 ELSE 1 END, updated_at DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            items = []
            for row in rows:
                sources = db.execute(
                    "SELECT provider,conversation_id,message_id,conversation_url,conversation_title,first_seen_at "
                    "FROM github_repository_ref_sources WHERE canonical_url=? ORDER BY first_seen_at",
                    (row["canonical_url"],),
                ).fetchall()
                items.append({
                    **dict(row),
                    "is_archived": bool(row["is_archived"]) if row["is_archived"] is not None else None,
                    "sources": [dict(source) for source in sources],
                    "occurrence_count": len(sources),
                })
        return {"total": total, "limit": limit, "offset": offset, "items": items}

    def reindex_github_repository_references(self, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """Backfill references from already archived Vault conversations without altering transcripts."""
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("Invalid reindex pagination")
        rows = self.list_conversations()
        selected = rows[offset:offset + limit]
        indexed = skipped = failed = 0
        errors: list[dict[str, str]] = []
        for row in selected:
            archive_path = Path(row["archive_path"])
            try:
                if archive_path.is_symlink() or not archive_path.is_file():
                    skipped += 1
                    continue
                payload = json.loads(archive_path.read_text(encoding="utf-8"))
                messages = payload.get("messages", []) if isinstance(payload, dict) else []
                if not isinstance(messages, list):
                    raise ValueError("archive messages are not a list")
                indexed += self.record_github_repository_references(
                    provider=str(row["provider"]),
                    conversation_id=str(row["conversation_id"]),
                    title=str(row.get("title") or "Untitled"),
                    conversation_url=row.get("url"),
                    messages=messages,
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                failed += 1
                errors.append({
                    "provider": str(row.get("provider") or "")[:40],
                    "conversation_id": str(row.get("conversation_id") or "")[:120],
                    "error": type(exc).__name__,
                })
        next_offset = offset + len(selected)
        return {
            "status": "completed" if failed == 0 else "partial",
            "conversations_seen": len(selected),
            "links_indexed": indexed,
            "skipped": skipped,
            "failed": failed,
            "total_conversations": len(rows),
            "next_offset": next_offset if next_offset < len(rows) else None,
            "errors": errors[:50],
        }

    def verify_pending_github_repository_references(self, *, limit: int = 10, timeout: float = 5.0) -> dict[str, Any]:
        """Verify a small batch using only the public GitHub REST endpoint; never sends credentials."""
        if not 1 <= limit <= 25 or not 1 <= timeout <= 10:
            raise ValueError("Verification batch or timeout is outside safe bounds")
        with self._connect() as db:
            pending = db.execute(
                "SELECT canonical_url,owner,repository FROM github_repository_refs "
                "WHERE verification_status IN ('pending_verification','rate_limited','unavailable') "
                "ORDER BY created_at LIMIT ?", (limit,)
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in pending:
            api_url = f"https://api.github.com/repos/{row['owner']}/{row['repository']}"
            request = Request(api_url, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DGM-MAT-GitHub-Reference-Verifier",
                "X-GitHub-Api-Version": "2022-11-28",
            })
            status = "unavailable"
            details: dict[str, Any] = {}
            try:
                with urlopen(request, timeout=timeout) as response:
                    if response.status == 200:
                        payload = json.loads(response.read(256 * 1024).decode("utf-8"))
                        if payload.get("full_name", "").casefold() != f"{row['owner']}/{row['repository']}".casefold():
                            status = "unavailable"
                        else:
                            status = "verified_public"
                            details = {
                                "html_url": payload.get("html_url"),
                                "description": str(payload.get("description") or "")[:1000],
                                "default_branch": str(payload.get("default_branch") or "")[:120],
                                "is_archived": bool(payload.get("archived")),
                            }
                    elif response.status == 403:
                        status = "rate_limited"
            except HTTPError as exc:
                status = "not_found_or_private" if exc.code == 404 else "rate_limited" if exc.code in {403, 429} else "unavailable"
            except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
                status = "unavailable"
            now = _now()
            with self._connect() as db:
                db.execute("""
                    UPDATE github_repository_refs SET verification_status=?,html_url=?,description=?,
                        default_branch=?,is_archived=?,verified_at=?,updated_at=?
                    WHERE canonical_url=?
                """, (
                    status, details.get("html_url"), details.get("description"),
                    details.get("default_branch"), int(details["is_archived"]) if "is_archived" in details else None,
                    now if status in {"verified_public", "not_found_or_private"} else None,
                    now, row["canonical_url"],
                ))
            results.append({"canonical_url": row["canonical_url"], "verification_status": status, **details})
        return {"checked": len(results), "results": results, "credentials_sent": False}

    def sync_completed_progress(
        self,
        progress_paths: list[str | Path],
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Copy completed local conversation records into the Vault without moving source DBs."""
        from core.conversation_intelligence.progress_store import ConversationProgressStore

        unique_paths = list(dict.fromkeys(Path(value).expanduser().resolve() for value in progress_paths))
        records: list[dict[str, Any]] = []
        opened: list[str] = []
        failures: list[dict[str, str]] = []
        for database_path in unique_paths:
            if not database_path.is_file():
                continue
            try:
                records.extend(ConversationProgressStore(database_path).list_conversations())
                opened.append(str(database_path))
            except Exception as exc:
                failures.append({
                    "database": str(database_path),
                    "error": type(exc).__name__,
                    "detail": str(exc)[:300],
                })

        provider_filter = {item.casefold() for item in (providers or [])}
        archived = 0
        duplicates = 0
        skipped = 0
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
            if provider_filter and provider.casefold() not in provider_filter:
                continue
            conversation_id = str(conversation.get("conversation_id") or row.get("conversation_id") or "")
            if not conversation_id:
                skipped += 1
                continue
            metadata = conversation.get("metadata") or {}
            try:
                result = self.archive_conversation(
                    provider=provider,
                    conversation_id=conversation_id,
                    title=str(conversation.get("title") or row.get("title") or "Untitled"),
                    url=conversation.get("url"),
                    content=str(conversation.get("content") or ""),
                    messages=conversation.get("messages") or [],
                    completeness=str(metadata.get("completeness") or metadata.get("capture_status") or "unknown"),
                    assignment_evidence=[
                        "local completed progress-store record",
                        "evidence-based project classifier",
                    ],
                    metadata=metadata,
                    artifacts=snapshot.get("artifacts") or [],
                )
                duplicates += int(bool(result.get("duplicate")))
                archived += int(not bool(result.get("duplicate")))
            except Exception as exc:
                failures.append({
                    "provider": provider,
                    "conversation_id": conversation_id,
                    "error": type(exc).__name__,
                    "detail": str(exc)[:300],
                })

        return {
            "progress_databases": opened,
            "progress_records_seen": len(records),
            "conversations_archived": archived,
            "duplicates_detected": duplicates,
            "records_skipped": skipped,
            "failures": failures,
        }

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
                entry = {
                    "path": relative,
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "extension": suffix,
                    "language": language,
                }
                if (language or name in MANIFEST_NAMES) and stat.st_size <= 10 * 1024 * 1024:
                    entry["sha256"] = _file_digest(path)
                entries.append(entry)
                if len(entries) > max_entries:
                    raise ValueError(f"Repository tree exceeded max_entries={max_entries}; no partial snapshot saved")
        entries.sort(key=lambda item: item["path"].casefold())
        tree = {"schema": "dgm-mat.repository-tree.v1", "project_id": project_id,
                "repository_path": str(root), "generated_at": _now(),
                "file_count": len(entries), "languages": dict(sorted(languages.items())),
                "manifests": sorted(manifests), "entries": entries,
                "ignored_directories": sorted(ignored)}
        raw = (_json(tree) + "\n").encode("utf-8")
        raw_sha256 = _digest(raw)
        fingerprint_payload = {key: value for key, value in tree.items() if key != "generated_at"}
        fingerprint = _digest((_json(fingerprint_payload) + "\n").encode("utf-8"))
        folder = self.root / "projects" / project_id / "trees"
        folder.mkdir(parents=True, exist_ok=True)

        with self._connect() as db:
            existing = db.execute("""
                SELECT snapshot_id,snapshot_path FROM tree_snapshots
                WHERE project_id=? AND repository_path=? AND tree_fingerprint=?
                ORDER BY created_at DESC LIMIT 1
            """, (project_id, str(root), fingerprint)).fetchone()
        if existing:
            existing_json = Path(existing["snapshot_path"])
            existing_text = existing_json.with_suffix(".txt")
            if existing_json.is_file() and existing_text.is_file():
                snapshot_id = existing["snapshot_id"]
                current_pointer = folder / "CURRENT.json"
                temporary_pointer = folder / ".CURRENT.json.tmp"
                temporary_pointer.write_text(_json({
                    "snapshot_id": snapshot_id, "json": existing_json.name,
                    "text": existing_text.name, "fingerprint": fingerprint,
                }) + "\n", encoding="utf-8")
                temporary_pointer.replace(current_pointer)
                self.register_project(project_id, project["name"], root, project["aliases"])
                return {
                    "snapshot_id": snapshot_id, "snapshot_path": str(existing_json),
                    "tree_text_path": str(existing_text), "current_pointer": str(current_pointer),
                    "fingerprint": fingerprint, "file_count": len(entries),
                    "languages": tree["languages"], "manifests": tree["manifests"],
                    "reused": True,
                }

        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + fingerprint[:12]
        destination = folder / f"{snapshot_id}.json"
        with destination.open("xb") as stream:
            stream.write(raw)
        if _digest(destination.read_bytes()) != raw_sha256:
            destination.unlink(missing_ok=True)
            raise OSError("Repository tree snapshot verification failed")
        text_destination = folder / f"{snapshot_id}.txt"
        text_raw = _format_tree(root.name, entries).encode("utf-8")
        with text_destination.open("xb") as stream:
            stream.write(text_raw)
        current_pointer = folder / "CURRENT.json"
        temporary_pointer = folder / ".CURRENT.json.tmp"
        temporary_pointer.write_text(_json({
            "snapshot_id": snapshot_id, "json": destination.name,
            "text": text_destination.name, "fingerprint": fingerprint,
        }) + "\n", encoding="utf-8")
        temporary_pointer.replace(current_pointer)
        with self._connect() as db:
            db.execute("""
                INSERT INTO tree_snapshots(snapshot_id,project_id,repository_path,tree_fingerprint,
                    snapshot_path,file_count,language_summary_json,created_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (snapshot_id, project_id, str(root), fingerprint, str(destination),
                  len(entries), _json(tree["languages"]), tree["generated_at"]))
        self.register_project(project_id, project["name"], root, project["aliases"])
        return {"snapshot_id": snapshot_id, "snapshot_path": str(destination),
                "tree_text_path": str(text_destination), "current_pointer": str(current_pointer),
                "fingerprint": fingerprint, "file_count": len(entries),
                "languages": tree["languages"], "manifests": tree["manifests"], "reused": False}

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
