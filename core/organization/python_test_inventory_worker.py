"""Bounded, read-only inventory of Python test suites using AST parsing only."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from pathlib import Path

from .models import Message


class PythonTestInventoryWorker:
    """Describe Python test structure without importing or executing test code."""

    agent_id = "agent:python-test-inventory"
    capabilities = ("python-test-inventory", "python-test-structure", "python-test-gap-signals")
    _REQUEST_KEYS = {"schema_version", "operation", "repository_id"}
    _REPOSITORY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    _SKIP_DIRS = {
        ".git", ".venv", "venv", "node_modules", "__pycache__", ".tox",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".idea",
    }
    _SENSITIVE_NAMES = {
        ".env", ".env.local", ".env.production", "credentials.json",
        "secrets.json", "id_rsa", "id_ed25519",
    }

    def __init__(
        self,
        *,
        allowed_root: str | Path,
        repositories: dict[str, str | Path],
        allowed_senders: tuple[str, ...] = ("agent:hq-orchestrator",),
        max_files: int = 300,
        max_file_bytes: int = 512_000,
        max_total_bytes: int = 5_000_000,
    ) -> None:
        self.allowed_root = Path(allowed_root).expanduser().resolve(strict=True)
        if not self.allowed_root.is_dir():
            raise ValueError("allowed_root must be an existing directory")
        if not isinstance(repositories, dict) or not repositories:
            raise ValueError("repositories must be a non-empty mapping")
        if type(max_files) is not int or not 1 <= max_files <= 1000:
            raise ValueError("max_files must be between 1 and 1000")
        if type(max_file_bytes) is not int or not 1024 <= max_file_bytes <= 2_000_000:
            raise ValueError("max_file_bytes must be between 1024 and 2000000")
        if type(max_total_bytes) is not int or not max_file_bytes <= max_total_bytes <= 20_000_000:
            raise ValueError("max_total_bytes must be bounded and at least max_file_bytes")
        if not isinstance(allowed_senders, (tuple, list, set, frozenset)) or not allowed_senders:
            raise ValueError("allowed_senders must be a non-empty collection")
        if any(not isinstance(item, str) or not item.strip() for item in allowed_senders):
            raise ValueError("allowed_senders must contain non-empty sender IDs")

        roots: dict[str, Path] = {}
        for repository_id, raw_path in repositories.items():
            if not isinstance(repository_id, str) or not self._REPOSITORY_ID.fullmatch(repository_id):
                raise ValueError("repository IDs must be stable safe identifiers")
            candidate = Path(raw_path).expanduser().resolve(strict=True)
            if not candidate.is_dir() or not candidate.is_relative_to(self.allowed_root):
                raise ValueError("repository must be a directory inside allowed_root")
            roots[repository_id] = candidate
        self.repositories = roots
        self.allowed_senders = frozenset(allowed_senders)
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes

    @staticmethod
    def _blocked(reason: str, message: Message) -> dict:
        return {
            "status": "BLOCKED", "worker": "python-test-inventory",
            "reason": reason, "message_id": message.message_id,
            "mission_id": message.mission_id, "source_content_returned": False,
            "tests_executed": False, "code_executed": False,
            "files_modified": False, "network_used": False,
        }

    def __call__(self, message: Message) -> dict:
        if message.recipient_id != self.agent_id:
            return self._blocked("recipient_mismatch", message)
        if message.sender_id not in self.allowed_senders:
            return self._blocked("sender_not_allowlisted", message)
        if not message.mission_id or not message.correlation_id:
            return self._blocked("mission_or_correlation_id_missing", message)
        if not isinstance(message.body, str) or len(message.body.encode("utf-8", errors="replace")) > 4096:
            return self._blocked("request_size_invalid", message)
        try:
            request = json.loads(message.body)
        except (json.JSONDecodeError, UnicodeError):
            return self._blocked("request_json_invalid", message)
        if not isinstance(request, dict) or set(request) != self._REQUEST_KEYS:
            return self._blocked("request_schema_invalid", message)
        if type(request["schema_version"]) is not int or request["schema_version"] != 1:
            return self._blocked("request_schema_version_unsupported", message)
        if request["operation"] != "inventory_python_tests":
            return self._blocked("operation_not_allowed", message)
        repository_id = request["repository_id"]
        if not isinstance(repository_id, str) or not self._REPOSITORY_ID.fullmatch(repository_id):
            return self._blocked("repository_id_invalid", message)
        if repository_id not in self.repositories:
            return self._blocked("repository_not_allowlisted", message)

        root = self.repositories[repository_id]
        try:
            verified_root = root.resolve(strict=True)
            if not verified_root.is_dir() or not verified_root.is_relative_to(self.allowed_root):
                return self._blocked("repository_root_changed_or_escaped", message)
            return self._inventory(repository_id, verified_root, message)
        except (OSError, ValueError):
            return self._blocked("repository_unavailable", message)

    def _inventory(self, repository_id: str, root: Path, message: Message) -> dict:
        candidates: list[Path] = []
        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            dirs[:] = sorted(
                name for name in dirs
                if name.casefold() not in self._SKIP_DIRS
                and not name.startswith(".")
                and not (current_path / name).is_symlink()
            )
            relative_dir = current_path.relative_to(root)
            in_test_tree = "tests" in {part.casefold() for part in relative_dir.parts}
            if not in_test_tree:
                continue
            for name in sorted(files):
                path = current_path / name
                if name.casefold() in self._SENSITIVE_NAMES or path.is_symlink():
                    continue
                if path.suffix.casefold() == ".py":
                    candidates.append(path)
                    if len(candidates) > self.max_files:
                        return self._blocked("file_limit_exceeded", message)
        candidates.sort(key=lambda item: item.relative_to(root).as_posix())

        digest = hashlib.sha256()
        imports: set[str] = set()
        diagnostics: list[dict] = []
        analyzed = skipped_oversize = total_bytes = 0
        tests = async_tests = fixtures = parametrized = test_classes = 0
        framework_imports: set[str] = set()

        for path in candidates:
            try:
                if not path.resolve(strict=True).is_relative_to(root):
                    continue
                raw = path.read_bytes()
            except OSError:
                continue
            if len(raw) > self.max_file_bytes:
                skipped_oversize += 1
                continue
            total_bytes += len(raw)
            if total_bytes > self.max_total_bytes:
                return self._blocked("total_source_budget_exceeded", message)
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(raw)
            try:
                source = raw.decode("utf-8")
                tree = ast.parse(source, filename=relative, type_comments=True)
            except UnicodeDecodeError:
                diagnostics.append({"path": relative, "kind": "encoding_error"})
                analyzed += 1
                continue
            except SyntaxError as exc:
                diagnostics.append({
                    "path": relative, "kind": "syntax_error",
                    "line": exc.lineno, "column": exc.offset, "message": str(exc.msg)[:160],
                })
                analyzed += 1
                continue
            except (ValueError, RecursionError, MemoryError):
                diagnostics.append({"path": relative, "kind": "parser_limit_error"})
                analyzed += 1
                continue
            analyzed += 1
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                        if alias.name.split(".", 1)[0] in {"pytest", "unittest"}:
                            framework_imports.add(alias.name.split(".", 1)[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                    if node.module.split(".", 1)[0] in {"pytest", "unittest"}:
                        framework_imports.add(node.module.split(".", 1)[0])
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        tests += 1
                        async_tests += isinstance(node, ast.AsyncFunctionDef)
                    for decorator in node.decorator_list:
                        target = decorator.func if isinstance(decorator, ast.Call) else decorator
                        name = target.id if isinstance(target, ast.Name) else (
                            target.attr if isinstance(target, ast.Attribute) else ""
                        )
                        if name == "fixture":
                            fixtures += 1
                        elif name == "parametrize":
                            parametrized += 1
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    test_classes += 1

        return {
            "status": "COMPLETED_READ_ONLY",
            "worker": "python-test-inventory",
            "repository_id": repository_id,
            "test_files_discovered": len(candidates),
            "test_files_analyzed": analyzed,
            "test_files_skipped_oversize": skipped_oversize,
            "bytes_analyzed": total_bytes,
            "test_functions": tests,
            "async_test_functions": async_tests,
            "test_classes": test_classes,
            "fixtures": fixtures,
            "parametrize_decorators": parametrized,
            "framework_imports": sorted(framework_imports),
            "imports": sorted(imports)[:500],
            "syntax_diagnostics": diagnostics[:100],
            "inventory_sha256": digest.hexdigest(),
            "source_content_returned": False,
            "tests_executed": False,
            "code_executed": False,
            "files_modified": False,
            "network_used": False,
            "message_id": message.message_id,
            "mission_id": message.mission_id,
        }
