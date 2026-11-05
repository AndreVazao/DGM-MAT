"""Backup-first, repository-scoped text patch application.

This primitive is intentionally not wired to mission execution yet. It provides
an auditable, reversible write boundary for the governed development pipeline.
It never executes commands, follows symlinks, writes outside one Git worktree,
or modifies protected credential/system paths.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4


class PatchRejected(ValueError):
    """A proposed patch violates the repository or backup policy."""


class PatchBackupError(RuntimeError):
    """A safe backup could not be created; the source file was not changed."""


class PatchRollbackError(RuntimeError):
    """A rollback could not be completed safely."""


class BackupFirstPatchExecutor:
    """Apply one bounded UTF-8 text replacement/create with a verified backup."""

    DEFAULT_MAX_FILE_BYTES = 2_000_000
    PROTECTED_PARTS = {
        ".git", ".ssh", "secrets", "secret", "credentials", "credential",
        "tokens", "token-store", "browser", "profiles",
    }
    PROTECTED_NAMES = {
        ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
        "credentials.json", "secrets.json",
    }
    PROTECTED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore", ".kdbx"}

    def __init__(
        self,
        repo_root: str | Path,
        *,
        backup_root: str | Path | None = None,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve(strict=True)
        if not self.repo_root.is_dir():
            raise PatchRejected("repo_root must be an existing directory.")
        if not ((self.repo_root / ".git").exists() or (self.repo_root / ".git").is_file()):
            raise PatchRejected("repo_root must be a Git working tree.")
        if isinstance(max_file_bytes, bool) or not isinstance(max_file_bytes, int):
            raise ValueError("max_file_bytes must be an integer.")
        if not 1 <= max_file_bytes <= 10_000_000:
            raise ValueError("max_file_bytes must be between 1 and 10000000.")
        self.max_file_bytes = max_file_bytes
        configured = (
            Path(backup_root).expanduser()
            if backup_root is not None
            else Path.home() / ".dgm-mat" / "patch-backups" / self.repo_root.name
        )
        self.backup_root = configured.resolve(strict=False)
        try:
            self.backup_root.relative_to(self.repo_root)
        except ValueError:
            pass
        else:
            raise PatchRejected("Backup storage must be outside the Git worktree.")
        if self.backup_root == self.repo_root:
            raise PatchRejected("Backup storage must be outside the Git worktree.")

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _relative_target(self, raw_path: str) -> tuple[Path, str]:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise PatchRejected("A non-empty repository-relative path is required.")
        normalized = raw_path.replace("\\", "/")
        raw_parts = normalized.split("/")
        pure = PurePosixPath(normalized)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
            raise PatchRejected("Absolute paths, empty segments and traversal are denied.")
        if pure.parts and ":" in pure.parts[0]:
            raise PatchRejected("Drive-qualified paths are denied.")
        lowered = [part.casefold() for part in pure.parts]
        if any(part in self.PROTECTED_PARTS for part in lowered):
            raise PatchRejected("Protected credential, browser or VCS paths are denied.")
        name = pure.name.casefold()
        if name in self.PROTECTED_NAMES or name.startswith(".env.") or name.startswith(".env-") or Path(name).suffix in self.PROTECTED_SUFFIXES:
            raise PatchRejected("Protected credential/key files are denied.")

        target = self.repo_root.joinpath(*pure.parts)
        cursor = self.repo_root
        for part in pure.parts[:-1]:
            cursor = cursor / part
            if cursor.is_symlink():
                raise PatchRejected("Symbolic-link path components are denied.")
        parent = target.parent
        try:
            resolved_parent = parent.resolve(strict=True)
            resolved_parent.relative_to(self.repo_root)
        except (OSError, ValueError) as exc:
            raise PatchRejected("Target parent must already exist inside the selected worktree.") from exc
        if target.is_symlink():
            raise PatchRejected("Symbolic-link targets are denied.")
        resolved_target = resolved_parent / target.name
        try:
            resolved_target.relative_to(self.repo_root)
        except ValueError as exc:
            raise PatchRejected("Target escapes the selected worktree.") from exc
        if resolved_target.exists() and not resolved_target.is_file():
            raise PatchRejected("Only regular files can be patched.")
        return resolved_target, pure.as_posix()

    @staticmethod
    def _require_secure_directory_fd_support() -> None:
        """Fail closed where the platform cannot anchor operations to directory handles."""
        required = {"O_NOFOLLOW", "O_DIRECTORY"}
        if os.name != "posix" or any(not hasattr(os, name) for name in required):
            raise PatchRejected(
                "Secure directory-handle writes are unavailable on this platform; refusing filesystem mutation."
            )
        if os.open not in os.supports_dir_fd or os.replace not in os.supports_dir_fd:
            raise PatchRejected(
                "Secure dir_fd filesystem operations are unavailable; refusing filesystem mutation."
            )

    def _open_parent_fd(self, normalized: str) -> tuple[int, str]:
        """Open each parent component without following links and pin the final directory."""
        self._require_secure_directory_fd_support()
        parts = PurePosixPath(normalized).parts
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        current_fd = os.open(self.repo_root, flags)
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, flags, dir_fd=current_fd)
                os.close(current_fd)
                current_fd = next_fd
            return current_fd, parts[-1]
        except Exception:
            os.close(current_fd)
            raise

    def _read_at(self, parent_fd: int, name: str) -> bytes | None:
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(name, flags, dir_fd=parent_fd)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise PatchRejected("Target could not be opened without following links.") from exc
        try:
            info = os.fstat(fd)
            if not os.path.stat.S_ISREG(info.st_mode):
                raise PatchRejected("Only regular files can be patched.")
            if info.st_size > self.max_file_bytes:
                raise PatchRejected("Original file exceeds the configured size limit.")
            chunks = []
            total = 0
            while True:
                chunk = os.read(fd, min(65536, self.max_file_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > self.max_file_bytes:
                    raise PatchRejected("Original file exceeds the configured size limit.")
            return b"".join(chunks)
        finally:
            os.close(fd)

    @staticmethod
    def _write_all(fd: int, data: bytes) -> None:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("Short write while creating guarded patch file.")
            view = view[written:]

    def _write_atomic_at(self, parent_fd: int, name: str, data: bytes) -> None:
        """Write and replace a basename relative to a pinned, no-follow directory handle."""
        temporary = f".dgm-patch-{uuid4().hex}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        fd = os.open(temporary, flags, 0o600, dir_fd=parent_fd)
        try:
            self._write_all(fd, data)
            os.fsync(fd)
        except Exception:
            os.close(fd)
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except OSError:
                pass
            raise
        else:
            os.close(fd)
        try:
            os.replace(
                temporary, name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            os.fsync(parent_fd)
        except Exception:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except OSError:
                pass
            raise

    def apply_text(
        self,
        relative_path: str,
        content: str,
        *,
        expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        """Create or replace a UTF-8 text file using a pinned directory handle."""
        if not isinstance(content, str):
            raise PatchRejected("Patch content must be text.")
        encoded = content.encode("utf-8")
        if len(encoded) > self.max_file_bytes:
            raise PatchRejected("Patch content exceeds the configured size limit.")

        # Keep the static policy checks, but never use the returned path for writes.
        _, normalized = self._relative_target(relative_path)
        parent_fd, target_name = self._open_parent_fd(normalized)
        try:
            original = self._read_at(parent_fd, target_name)
            existed = original is not None
            original_sha = self._sha256(original) if original is not None else None
            if existed:
                if not isinstance(expected_sha256, str) or expected_sha256.casefold() != original_sha:
                    raise PatchRejected("Existing-file replacement requires a matching expected_sha256.")
            elif expected_sha256 is not None:
                raise PatchRejected("expected_sha256 must be omitted when creating a new file.")

            backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:12]
            backup_dir = self.backup_root / backup_id
            backup_file: Path | None = None
            self.backup_root.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=False)

            try:
                if original is not None:
                    backup_file = backup_dir / "original.bin"
                    try:
                        with backup_file.open("xb") as stream:
                            stream.write(original)
                            stream.flush()
                            os.fsync(stream.fileno())
                        if self._sha256(backup_file.read_bytes()) != original_sha:
                            raise PatchBackupError("Backup hash does not match the original file.")
                    except Exception as exc:
                        shutil.rmtree(backup_dir, ignore_errors=True)
                        raise PatchBackupError("Could not create and verify the original-file backup.") from exc

                try:
                    # Recheck immediately before promotion. The operation remains
                    # anchored to the already-open directory even if its path is
                    # concurrently replaced with a symlink.
                    current = self._read_at(parent_fd, target_name)
                    if (self._sha256(current) if current is not None else None) != original_sha:
                        raise PatchRejected("Target changed after the guarded read; refusing replacement.")
                    self._write_atomic_at(parent_fd, target_name, encoded)
                    result = self._read_at(parent_fd, target_name)
                    result_sha = self._sha256(result or b"")
                    if result_sha != self._sha256(encoded):
                        raise OSError("Post-write SHA-256 mismatch.")
                    manifest = {
                        "schema": "dgm-mat.backup-first-patch.v1",
                        "backup_id": backup_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "repository": str(self.repo_root),
                        "relative_path": normalized,
                        "operation": "replace" if existed else "create",
                        "original_sha256": original_sha,
                        "result_sha256": result_sha,
                        "backup_file": str(backup_file) if backup_file else None,
                        "rollback_available": True,
                    }
                    (backup_dir / "manifest.json").write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n",
                        encoding="utf-8",
                    )
                except Exception:
                    if existed and backup_file and backup_file.exists():
                        self._write_atomic_at(parent_fd, target_name, backup_file.read_bytes())
                    elif not existed:
                        try:
                            os.unlink(target_name, dir_fd=parent_fd)
                            os.fsync(parent_fd)
                        except FileNotFoundError:
                            pass
                    raise
            except Exception:
                raise
            return manifest
        finally:
            os.close(parent_fd)

    def rollback(self, backup_id: str) -> dict[str, Any]:
        """Restore the original bytes only if the current file still matches this patch."""
        if not isinstance(backup_id, str) or not backup_id or "/" in backup_id or "\\" in backup_id:
            raise PatchRejected("Invalid backup ID.")
        backup_dir = (self.backup_root / backup_id).resolve(strict=True)
        try:
            backup_dir.relative_to(self.backup_root)
        except ValueError as exc:
            raise PatchRejected("Backup ID escapes backup storage.") from exc
        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.is_file():
            raise PatchRollbackError("Backup manifest is missing.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "dgm-mat.backup-first-patch.v1":
            raise PatchRollbackError("Unsupported backup manifest.")
        if Path(manifest.get("repository", "")).resolve() != self.repo_root:
            raise PatchRollbackError("Backup belongs to a different repository.")
        target, normalized = self._relative_target(manifest.get("relative_path", ""))
        if normalized != manifest.get("relative_path"):
            raise PatchRollbackError("Backup path normalization mismatch.")
        if not target.is_file() or self._sha256(target.read_bytes()) != manifest.get("result_sha256"):
            raise PatchRollbackError("Current file changed after the patch; refusing to overwrite newer work.")

        backup_file_value = manifest.get("backup_file")
        if backup_file_value:
            backup_file = Path(backup_file_value).resolve(strict=True)
            try:
                backup_file.relative_to(backup_dir)
            except ValueError as exc:
                raise PatchRollbackError("Backup file escapes its backup directory.") from exc
            original = backup_file.read_bytes()
            if self._sha256(original) != manifest.get("original_sha256"):
                raise PatchRollbackError("Original backup hash verification failed.")
            self._write_atomic(target, original)
            restored_sha = self._sha256(target.read_bytes())
        else:
            target.unlink()
            restored_sha = None

        manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        manifest["rollback_result_sha256"] = restored_sha
        manifest["rollback_available"] = False
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest
