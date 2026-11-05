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
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from core.execution.windows_handle_fs import WindowsDirectoryHandleBackend, WindowsHandleError


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
        self._windows_backend: WindowsDirectoryHandleBackend | None = None
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
        if os.name == "nt":
            self._windows_backend = WindowsDirectoryHandleBackend()
            root_handle = self._windows_backend.open_root(self.repo_root)
            try:
                self._repo_identity = self._windows_backend.file_identity(root_handle)
            finally:
                self._windows_backend.close(root_handle)
        else:
            root_identity = self.repo_root.stat()
            self._repo_identity = (root_identity.st_dev, root_identity.st_ino)

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
        if any(operation not in os.supports_dir_fd for operation in (os.open, os.rename, os.unlink)):
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
            opened_root = os.fstat(current_fd)
            if (opened_root.st_dev, opened_root.st_ino) != self._repo_identity:
                raise PatchRejected("Repository root changed after executor initialization.")
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
            if not stat.S_ISREG(info.st_mode):
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
            os.rename(
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

    def _open_parent_handles_windows(self, normalized: str) -> tuple[Any, Any, str]:
        backend = self._windows_backend
        if backend is None:
            raise PatchRejected("Native Windows handle backend is unavailable.")
        parts = PurePosixPath(normalized).parts
        root_handle = backend.open_root(self.repo_root)
        parent_handle = root_handle
        try:
            if backend.file_identity(root_handle) != self._repo_identity:
                raise PatchRejected("Repository root changed after executor initialization.")
            for part in parts[:-1]:
                child_handle = backend.open_child_directory(parent_handle, part)
                if parent_handle is not root_handle:
                    backend.close(parent_handle)
                parent_handle = child_handle
            return root_handle, parent_handle, parts[-1]
        except Exception:
            if parent_handle is not root_handle:
                backend.close(parent_handle)
            backend.close(root_handle)
            raise

    def _write_manifest_windows(
        self,
        backup_dir_handle: Any,
        manifest: dict[str, Any],
        *,
        replace_existing: bool,
    ) -> None:
        backend = self._windows_backend
        if backend is None:
            raise PatchBackupError("Native Windows handle backend is unavailable.")
        temporary = f".dgm-manifest-{uuid4().hex}.tmp"
        handle = backend.create_file(backup_dir_handle, temporary)
        promoted = False
        try:
            payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            backend.write_all(handle, payload)
            backend.rename_relative(
                handle,
                None,
                "manifest.json",
                replace_existing=replace_existing,
            )
            promoted = True
        finally:
            if not promoted:
                try:
                    backend.delete_handle(handle)
                except Exception:
                    pass
            backend.close(handle)

    def _apply_text_windows(self, relative_path: str, encoded: bytes, expected_sha256: str | None) -> dict[str, Any]:
        backend = self._windows_backend
        if backend is None:
            raise PatchRejected("Native Windows handle backend is unavailable.")
        _, normalized = self._relative_target(relative_path)
        root_handle, parent_handle, target_name = self._open_parent_handles_windows(normalized)
        backup_root_handle = backup_dir_handle = target_handle = None
        manifest: dict[str, Any] | None = None
        target_identity: tuple[int, int] | None = None
        existed = False
        original: bytes | None = None
        try:
            # Existing targets are opened exclusively: the handle denies new
            # write/delete opens and remains pinned through backup and mutation.
            target_handle = backend.open_file_optional(
                parent_handle, target_name, exclusive=True
            )
            existed = target_handle is not None
            if existed:
                original = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
                target_identity = backend.file_identity(target_handle)
            original_sha = self._sha256(original) if original is not None else None
            if existed and (
                not isinstance(expected_sha256, str)
                or expected_sha256.casefold() != original_sha
            ):
                raise PatchRejected("Existing-file replacement requires a matching expected_sha256.")
            if not existed and expected_sha256 is not None:
                raise PatchRejected("expected_sha256 must be omitted when creating a new file.")

            backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:12]
            backup_file = self.backup_root / backup_id / "original.bin" if existed else None
            try:
                self.backup_root.mkdir(parents=True, exist_ok=True)
                backup_root_handle = backend.open_root(self.backup_root)
                backup_dir_handle = backend.create_directory(backup_root_handle, backup_id)
                if original is not None:
                    backup_handle = backend.create_file(backup_dir_handle, "original.bin", exclusive=True)
                    try:
                        backend.write_all(backup_handle, original)
                    finally:
                        backend.close(backup_handle)
                    verify_handle = backend.open_file(backup_dir_handle, "original.bin")
                    try:
                        if self._sha256(backend.read_all(verify_handle, max_bytes=self.max_file_bytes)) != original_sha:
                            raise PatchBackupError("Backup hash does not match the original file.")
                    finally:
                        backend.close(verify_handle)
            except PatchBackupError:
                raise
            except Exception as exc:
                raise PatchBackupError("Could not create and verify the original-file backup.") from exc

            manifest = {
                "schema": "dgm-mat.backup-first-patch.v1",
                "backup_id": backup_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "repository": str(self.repo_root),
                "relative_path": normalized,
                "operation": "replace" if existed else "create",
                "original_sha256": original_sha,
                "result_sha256": self._sha256(encoded),
                "backup_file": str(backup_file) if backup_file else None,
                "target_identity": (
                    {"volume_serial": target_identity[0], "file_index": target_identity[1]}
                    if target_identity else None
                ),
                "state": "prepared",
                "rollback_available": True,
            }
            # A prepared manifest is durable before changing target bytes.
            self._write_manifest_windows(backup_dir_handle, manifest, replace_existing=False)

            if existed:
                assert target_handle is not None
                backend.truncate_file(target_handle)
                backend.write_all(target_handle, encoded)
                backend.reset_file_pointer(target_handle)
                result = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
            else:
                # FILE_CREATE is atomic: a concurrent creator wins or we do.
                target_handle = backend.create_file(parent_handle, target_name, exclusive=True)
                target_identity = backend.file_identity(target_handle)
                manifest["target_identity"] = {
                    "volume_serial": target_identity[0],
                    "file_index": target_identity[1],
                }
                self._write_manifest_windows(backup_dir_handle, manifest, replace_existing=True)
                backend.write_all(target_handle, encoded)
                backend.reset_file_pointer(target_handle)
                result = backend.read_all(target_handle, max_bytes=self.max_file_bytes)

            result_sha = self._sha256(result)
            if result_sha != self._sha256(encoded):
                raise OSError("Post-write SHA-256 mismatch.")
            manifest["state"] = "applied"
            manifest["applied_at"] = datetime.now(timezone.utc).isoformat()
            self._write_manifest_windows(backup_dir_handle, manifest, replace_existing=True)
            return manifest
        except Exception as exc:
            if target_handle is not None and target_identity is not None:
                try:
                    if existed and original is not None:
                        backend.truncate_file(target_handle)
                        backend.write_all(target_handle, original)
                        backend.reset_file_pointer(target_handle)
                        restored = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
                        if self._sha256(restored) != self._sha256(original):
                            raise PatchRollbackError("Automatic Windows rollback verification failed.")
                    else:
                        backend.delete_handle(target_handle)
                except Exception as rollback_exc:
                    raise PatchRollbackError(
                        "Patch failed and automatic rollback could not be verified; preserve the backup for recovery."
                    ) from rollback_exc
            if isinstance(exc, (PatchRejected, PatchBackupError, PatchRollbackError)):
                raise
            if isinstance(exc, WindowsHandleError):
                raise PatchRejected(str(exc)) from exc
            raise
        finally:
            if target_handle is not None:
                backend.close(target_handle)
            if backup_dir_handle is not None:
                backend.close(backup_dir_handle)
            if backup_root_handle is not None:
                backend.close(backup_root_handle)
            if parent_handle is not root_handle:
                backend.close(parent_handle)
            backend.close(root_handle)

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
        if os.name == "nt":
            return self._apply_text_windows(relative_path, encoded, expected_sha256)

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
                        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
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

    def _rollback_windows(self, backup_id: str) -> dict[str, Any]:
        backend = self._windows_backend
        if backend is None:
            raise PatchRollbackError("Native Windows handle backend is unavailable.")
        backup_root_handle = backup_dir_handle = root_handle = parent_handle = target_handle = None
        try:
            backend._validate_basename(backup_id)
            backup_root_handle = backend.open_root(self.backup_root)
            backup_dir_handle = backend.open_child_directory(backup_root_handle, backup_id)
            manifest_handle = backend.open_file(backup_dir_handle, "manifest.json")
            try:
                manifest = json.loads(
                    backend.read_all(manifest_handle, max_bytes=1_000_000).decode("utf-8")
                )
            finally:
                backend.close(manifest_handle)
            if manifest.get("schema") != "dgm-mat.backup-first-patch.v1":
                raise PatchRollbackError("Unsupported backup manifest.")
            if manifest.get("rollback_available") is not True:
                raise PatchRollbackError("This backup has already been rolled back.")
            if Path(manifest.get("repository", "")).resolve() != self.repo_root:
                raise PatchRollbackError("Backup belongs to a different repository.")
            relative_path = manifest.get("relative_path", "")
            _, normalized = self._relative_target(relative_path)
            if normalized != relative_path:
                raise PatchRollbackError("Backup path normalization mismatch.")

            root_handle, parent_handle, target_name = self._open_parent_handles_windows(normalized)
            created = manifest.get("operation") == "create"
            target_handle = backend.open_file_optional(
                parent_handle,
                target_name,
                writable=created,
                exclusive=True,
            )
            if target_handle is None:
                raise PatchRollbackError("Patched target is missing; refusing an unverified rollback.")
            expected_identity = manifest.get("target_identity")
            actual_identity = backend.file_identity(target_handle)
            if not isinstance(expected_identity, dict) or (
                expected_identity.get("volume_serial") != actual_identity[0]
                or expected_identity.get("file_index") != actual_identity[1]
            ):
                raise PatchRollbackError("Target file identity changed after the patch; refusing rollback.")

            current = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
            current_sha = self._sha256(current)
            state = manifest.get("state")
            if state == "applied" and current_sha != manifest.get("result_sha256"):
                raise PatchRollbackError("Current file changed after the patch; refusing to overwrite newer work.")
            if state not in {"prepared", "applied"}:
                raise PatchRollbackError("Backup manifest is not in a recoverable state.")

            if manifest.get("backup_file"):
                expected_backup = self.backup_root / backup_id / "original.bin"
                if Path(manifest["backup_file"]) != expected_backup:
                    raise PatchRollbackError("Backup file path does not match the selected backup.")
                backup_handle = backend.open_file(backup_dir_handle, "original.bin")
                try:
                    original = backend.read_all(backup_handle, max_bytes=self.max_file_bytes)
                finally:
                    backend.close(backup_handle)
                if self._sha256(original) != manifest.get("original_sha256"):
                    raise PatchRollbackError("Original backup hash verification failed.")
                backend.truncate_file(target_handle)
                backend.write_all(target_handle, original)
                backend.reset_file_pointer(target_handle)
                restored = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
                restored_sha = self._sha256(restored)
                if restored_sha != manifest.get("original_sha256"):
                    raise PatchRollbackError("Restored file hash verification failed.")
            else:
                backend.delete_handle(target_handle)
                restored_sha = None

            manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
            manifest["rollback_result_sha256"] = restored_sha
            manifest["state"] = "rolled_back"
            manifest["rollback_available"] = False
            self._write_manifest_windows(backup_dir_handle, manifest, replace_existing=True)
            return manifest
        except (PatchRejected, PatchRollbackError):
            raise
        except Exception as exc:
            raise PatchRollbackError(
                "Native Windows rollback failed; preserve the backup for manual recovery."
            ) from exc
        finally:
            for handle in (target_handle, parent_handle, root_handle, backup_dir_handle, backup_root_handle):
                if handle is not None:
                    try:
                        backend.close(handle)
                    except Exception:
                        pass

    def rollback(self, backup_id: str) -> dict[str, Any]:
        """Restore original bytes through a pinned no-follow directory handle."""
        if os.name == "nt":
            return self._rollback_windows(backup_id)
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

        relative_path = manifest.get("relative_path", "")
        _, normalized = self._relative_target(relative_path)
        if normalized != relative_path:
            raise PatchRollbackError("Backup path normalization mismatch.")
        parent_fd, target_name = self._open_parent_fd(normalized)
        try:
            current = self._read_at(parent_fd, target_name)
            if current is None or self._sha256(current) != manifest.get("result_sha256"):
                raise PatchRollbackError(
                    "Current file changed after the patch; refusing to overwrite newer work."
                )

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
                self._write_atomic_at(parent_fd, target_name, original)
                restored = self._read_at(parent_fd, target_name)
                restored_sha = self._sha256(restored or b"")
                if restored_sha != manifest.get("original_sha256"):
                    raise PatchRollbackError("Restored file hash verification failed.")
            else:
                os.unlink(target_name, dir_fd=parent_fd)
                os.fsync(parent_fd)
                restored_sha = None
        finally:
            os.close(parent_fd)

        manifest["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        manifest["rollback_result_sha256"] = restored_sha
        manifest["rollback_available"] = False
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest
