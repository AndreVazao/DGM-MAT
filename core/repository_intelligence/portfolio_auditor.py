from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse


DEFAULT_WORKSPACE = Path("C:/ProgramasGodMode")
DEFAULT_EXCLUSIONS = {
    ".git", ".runtime", "__pycache__", "node_modules", "dist", "build",
    ".venv", "venv", ".next", "coverage", "test_worktrees",
}
PROTECTED_MARKERS = {
    "DGM-MAT-FULL-MIRROR",
    "manual_clones",
    "AndreOS-Memory-LEGACY",
}


@dataclass
class RepositoryAudit:
    name: str
    path: str
    local: bool
    has_git: bool
    github: bool
    origin: Optional[str]
    branch: Optional[str]
    commit_count: int
    dirty: bool
    file_count: int
    languages: list[str]
    purpose: str
    classification: str
    project_group: str
    protected: bool
    readme_present: bool
    manifests: list[str]
    relationships: list[str]
    risks: list[str]
    recommended_action: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepositoryAuditEngine:
    """Evidence-first portfolio auditor used by DGM-MAT itself.

    Audit is read-only. It never moves, deletes, renames, commits, pushes,
    creates repositories, or triggers workflows.
    """

    def __init__(
        self,
        workspace_root: Path | str = DEFAULT_WORKSPACE,
        exclusions: Optional[Iterable[str]] = None,
    ):
        self.workspace_root = Path(workspace_root)
        self.exclusions = set(exclusions or DEFAULT_EXCLUSIONS)

    def discover_repositories(self) -> list[Path]:
        roots = [self.workspace_root]
        repos: dict[str, Path] = {}
        for root in roots:
            if not root.exists():
                continue
            try:
                for item in root.iterdir():
                    if not item.is_dir() or item.name in self.exclusions:
                        continue
                    if (item / ".git").exists():
                        repos[str(item.resolve()).lower()] = item
            except (OSError, PermissionError):
                continue
        return sorted(repos.values(), key=lambda p: p.name.lower())

    def audit_workspace(self, limit: int | None = None) -> dict[str, Any]:
        repos = self.discover_repositories()
        if limit:
            repos = repos[:limit]
        audits = [self.audit_repository(p) for p in repos]
        return {
            "schema": "dgm-mat.repository-audit.v1",
            "workspace": str(self.workspace_root),
            "repository_count": len(audits),
            "repositories": [a.to_dict() for a in audits],
            "summary": self._summary(audits),
        }

    def audit_repository(self, repo: Path | str) -> RepositoryAudit:
        path = Path(repo)
        protected = self._is_protected(path)
        has_git = (path / ".git").exists()
        origin = self._git(path, ["remote", "get-url", "origin"]) if has_git else None
        branch = self._git(path, ["branch", "--show-current"]) if has_git else None
        commit_count = self._int_git(path, ["rev-list", "--count", "HEAD"]) if has_git else 0
        status = self._git(path, ["status", "--porcelain"]) if has_git else ""
        file_paths = list(self._iter_files(path))
        languages = self._languages(file_paths)
        manifests = self._manifests(file_paths)
        readme = self._read_readme(path)
        purpose = self._infer_purpose(path.name, readme, manifests)
        classification, confidence = self._classify(path.name, readme, origin)
        project_group = self._project_group(path.name, readme)
        relationships = self._relationships(path.name, readme, origin)
        risks = []
        if not has_git:
            risks.append("not-a-git-repository")
        if has_git and not origin:
            risks.append("missing-origin")
        if status:
            risks.append("working-tree-dirty")
        if not readme:
            risks.append("missing-readme")
        if "DGM-MAT-FULL-MIRROR" in path.name:
            risks.append("frozen-mirror-do-not-touch")
        action = self._recommended_action(
            classification=classification,
            protected=protected,
            dirty=bool(status),
            origin=origin,
            risks=risks,
        )
        return RepositoryAudit(
            name=path.name,
            path=str(path),
            local=path.exists(),
            has_git=has_git,
            github=self._looks_like_github(origin),
            origin=origin,
            branch=branch or None,
            commit_count=commit_count,
            dirty=bool(status),
            file_count=len(file_paths),
            languages=languages,
            purpose=purpose,
            classification=classification,
            project_group=project_group,
            protected=protected,
            readme_present=bool(readme),
            manifests=manifests,
            relationships=relationships,
            risks=risks,
            recommended_action=action,
            confidence=confidence,
        )

    def _iter_files(self, root: Path):
        if not root.exists():
            return
        stack = [root]
        while stack:
            current = stack.pop()
            try:
                for item in current.iterdir():
                    if item.is_dir():
                        if item.name in self.exclusions:
                            continue
                        stack.append(item)
                    elif item.is_file():
                        yield item
            except (OSError, PermissionError):
                continue

    def _git(self, repo: Path, args: list[str]) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-c", f"safe.directory={repo}", *args],
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def _int_git(self, repo: Path, args: list[str]) -> int:
        value = self._git(repo, args)
        try:
            return int(value or 0)
        except ValueError:
            return 0

    def _read_readme(self, repo: Path) -> str:
        for name in ("README.md", "README.MD", "readme.md"):
            path = repo / name
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8", errors="replace")[:30000]
                except OSError:
                    return ""
        return ""

    def _manifests(self, files: list[Path]) -> list[str]:
        names = {
            "pyproject.toml", "requirements.txt", "package.json",
            "Cargo.toml", "go.mod", "Dockerfile", "docker-compose.yml",
            "docker-compose.yaml", "composer.json", "pom.xml",
        }
        return sorted({p.name for p in files if p.name in names})

    def _languages(self, files: list[Path]) -> list[str]:
        ext_map = {
            ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
            ".js": "JavaScript", ".jsx": "JavaScript", ".rs": "Rust",
            ".go": "Go", ".java": "Java", ".cs": "C#", ".cpp": "C++",
            ".c": "C", ".ps1": "PowerShell", ".sh": "Shell",
            ".html": "HTML", ".css": "CSS",
        }
        counts = Counter(ext_map[p.suffix.lower()] for p in files if p.suffix.lower() in ext_map)
        return [name for name, _ in counts.most_common(6)]

    def _infer_purpose(self, name: str, readme: str, manifests: list[str]) -> str:
        text = f"{name} {readme[:12000]}".lower()
        rules = [
            ("multi-agent engineering/devops", ["multi-agent", "multi agent", "devops", "orchestrator", "agent runtime"]),
            ("AI/LLM tooling", ["llm", "ollama", "gpt", "language model", "ai assistant"]),
            ("trading/finance", ["trading", "freqtrade", "backtest", "crypto"]),
            ("automotive/engineering", ["engine swap", "ecu", "automotive", "car parts", "vehicle"]),
            ("EV charging", ["evse", "electric vehicle", "charger", "charging station"]),
            ("media/content creation", ["youtube", "avatar", "character", "storytelling", "video creation"]),
            ("workflow/build tooling", ["build pipeline", "github actions", "workflow", "builder", "ci/cd"]),
        ]
        for purpose, needles in rules:
            if any(n in text for n in needles):
                return purpose
        if "package.json" in manifests:
            return "web/application project"
        if "pyproject.toml" in manifests:
            return "Python application/library"
        return "unclassified repository"

    def _classify(self, name: str, readme: str, origin: Optional[str]) -> tuple[str, float]:
        text = f"{name} {readme[:16000]}".lower()
        external_names = ["freecad", "freqtrade", "ghost", "n8n"]
        if any(x in name.lower() for x in external_names) and origin:
            return "UPSTREAM", 0.95
        if "dgm-mat-full-mirror" in name.lower():
            return "ARCHIVE", 1.0
        if "dgm-mat" in name.lower() or "godmode" in name.lower():
            return "SUBPROJECT", 0.92
        if "lab" in name.lower() or "hackathon" in text:
            return "LAB", 0.86
        if any(x in text for x in ["prototype", "proof of concept", "experimental"]):
            return "EXPERIMENT", 0.78
        if any(x in text for x in ["multi-agent", "devops", "orchestration", "build control"]):
            return "LEGACY", 0.72
        return "PRODUCT", 0.55

    def _project_group(self, name: str, readme: str) -> str:
        text = f"{name} {readme[:8000]}".lower()
        groups = [
            ("DGM-MAT", ["dgm-mat", "god mode", "devops god mode", "multi-agent devops"]),
            ("VAZAO-EVSE", ["vazao evse", "evse", "charging station"]),
            ("PROVENTIL", ["proventil"]),
            ("AUTOMOTIVE", ["ecu-pro", "engine swap", "automotive", "car parts"]),
            ("TRADING", ["sovereign trader", "freqtrade", "trading"]),
            ("BARIBUDOS", ["baribudos", "children's stories", "children stories"]),
            ("N8N", ["n8n"]),
            ("OLLAMA/AI", ["ollama", "airllm", "rabbitllm"]),
        ]
        for group, needles in groups:
            if any(n in text for n in needles):
                return group
        return "UNKNOWN"

    def _relationships(self, name: str, readme: str, origin: Optional[str]) -> list[str]:
        text = f"{name} {readme[:10000]}".lower()
        relationships: list[str] = []
        if "dgm-mat" in text:
            relationships.append("DGM-MAT ecosystem")
        if any(x in text for x in ["upstream", "forked from", "based on"]):
            relationships.append("explicit upstream/fork relationship claimed in documentation")
        if origin and "github.com" in origin:
            relationships.append("GitHub remote")
        return relationships

    def _recommended_action(
        self,
        *,
        classification: str,
        protected: bool,
        dirty: bool,
        origin: Optional[str],
        risks: list[str],
    ) -> str:
        if protected:
            return "AUDIT_ONLY: protected/frozen path"
        if dirty:
            return "AUDIT_ONLY: preserve working tree before structural changes"
        if not origin:
            return "AUDIT: establish repository authority/remote"
        if classification in {"UPSTREAM", "ARCHIVE"}:
            return "AUDIT_ONLY: preserve as reference/archive"
        if classification in {"LEGACY", "EXPERIMENT", "LAB"}:
            return "STUDY: extract concepts; do not wholesale merge"
        return "AUDIT: candidate for project grouping after evidence review"

    def _is_protected(self, path: Path) -> bool:
        text = str(path).replace("\\", "/")
        return any(marker.lower() in text.lower() for marker in PROTECTED_MARKERS)

    @staticmethod
    def _looks_like_github(origin: Optional[str]) -> bool:
        if not origin:
            return False
        return "github.com" in urlparse(origin).netloc.lower() or "github.com" in origin.lower()

    @staticmethod
    def _summary(audits: list[RepositoryAudit]) -> dict[str, Any]:
        by_class = Counter(a.classification for a in audits)
        by_group = Counter(a.project_group for a in audits)
        return {
            "classifications": dict(sorted(by_class.items())),
            "project_groups": dict(sorted(by_group.items())),
            "dirty_repositories": sum(a.dirty for a in audits),
            "protected_repositories": sum(a.protected for a in audits),
            "missing_readmes": sum(not a.readme_present for a in audits),
            "missing_origins": sum(not a.origin for a in audits),
        }

    def github_metadata(self, origin: str) -> dict[str, Any]:
        """Read-only public GitHub metadata when the origin maps to github.com."""
        parsed = urlparse(origin)
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        if parsed.netloc.lower() not in {"github.com", "www.github.com"} or path.count("/") != 1:
            return {"available": False, "reason": "unsupported-origin"}
        url = f"https://api.github.com/repos/{path}"
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            return {
                "available": True,
                "full_name": data.get("full_name"),
                "default_branch": data.get("default_branch"),
                "archived": data.get("archived"),
                "private": data.get("private"),
                "html_url": data.get("html_url"),
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            return {"available": False, "reason": str(exc)}
