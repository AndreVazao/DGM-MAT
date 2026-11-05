"""Backup-first, repository-scoped text patch application.

This primitive is intentionally not wired to mission execution yet. Native
Windows mutations use pinned, exclusive handles. POSIX mutation is deliberately
fail-closed until a portable conditional replace/delete primitive can exclude
uncoordinated writers. The executor never runs commands.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
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
        try:
            git_root = subprocess.run(
                ["git", "-C", str(self.repo_root), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise PatchRejected("repo_root must be a valid Git working tree.") from exc
        if not git_root or Path(git_root).resolve() != self.repo_root:
            raise PatchRejected("repo_root must be the top-level directory of the selected Git worktree.")
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
        if ".." in configured.parts:
            raise PatchRejected("Parent traversal is denied in backup storage paths.")
        resolved_backup_root = configured.resolve(strict=False)
        try:
            resolved_backup_root.relative_to(self.repo_root)
        except ValueError:
            pass
        else:
            raise PatchRejected("Backup storage must be outside the Git worktree.")
        if resolved_backup_root == self.repo_root:
            raise PatchRejected("Backup storage must be outside the Git worktree.")
        # Windows resolves every existing component through pinned no-follow
        # handles at operation time; retain the lexical path so junctions are
        # rejected instead of silently canonicalized away.
        self.backup_root = (
            configured.absolute() if os.name == "nt" else resolved_backup_root
        )
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
        if os.name == "nt" and any(
            re.search(r"~[0-9](?:\\.[A-Z0-9]{0,3})?$", part, re.IGNORECASE)
            for part in pure.parts
        ):
            raise PatchRejected("Windows 8.3 short-name path components are denied.")
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
        handle = backend.create_file(backup_dir_handle, temporary, exclusive=True)
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
                target_identity = backend.file_identity(target_handle)
                if backend.file_link_count(target_handle) != 1:
                    raise PatchRejected(
                        "Windows hard-linked targets are denied because in-place updates would modify other paths."
                    )
                original = backend.read_all(target_handle, max_bytes=self.max_file_bytes)
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
                backup_root_handle = backend.ensure_directory(self.backup_root)
                backup_dir_handle = backend.create_directory(backup_root_handle, backup_id)
                if original is not None:
                    backup_handle = backend.create_file(backup_dir_handle, "original.bin", exclusive=True)
                    try:
                        backend.write_all(backup_handle, original)
                    finally:
                        backend.close(backup_handle)
                    verify_handle = backend.open_file(backup_dir_handle, "original.bin", exclusive=True)
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
                "repository_identity": list(self._repo_identity),
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
            if target_handle is not None and ((existed and original is not None) or not existed):
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
        if os.name != "nt":
            raise PatchRejected(
                "POSIX mutation is disabled: portable conditional replacement and rollback "
                "cannot exclude uncoordinated writers safely."
            )
        return self._apply_text_windows(relative_path, encoded, expected_sha256)


    def _rollback_windows(self, backup_id: str) -> dict[str, Any]:
        backend = self._windows_backend
        if backend is None:
            raise PatchRollbackError("Native Windows handle backend is unavailable.")
        backup_root_handle = backup_dir_handle = root_handle = parent_handle = target_handle = None
        try:
            backend._validate_basename(backup_id)
            backup_root_handle = backend.open_root(self.backup_root)
            backup_dir_handle = backend.open_child_directory(backup_root_handle, backup_id)
            manifest_handle = backend.open_file(backup_dir_handle, "manifest.json", exclusive=True)
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
            repository_identity = manifest.get("repository_identity")
            if (
                not isinstance(repository_identity, list)
                or tuple(repository_identity) != self._repo_identity
            ):
                raise PatchRollbackError("Backup belongs to a different repository identity.")
            operation = manifest.get("operation")
            backup_file_value = manifest.get("backup_file")
            if (
                (operation == "replace" and not backup_file_value)
                or (operation == "create" and backup_file_value is not None)
                or operation not in {"replace", "create"}
            ):
                raise PatchRollbackError("Backup operation and original-file metadata are inconsistent.")
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
            if backend.file_link_count(target_handle) != 1:
                raise PatchRollbackError(
                    "Hard-linked target detected; refusing rollback that could modify another path."
                )
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
                backup_handle = backend.open_file(backup_dir_handle, "original.bin", exclusive=True)
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
            for handle in (target_handle, backup_dir_handle, backup_root_handle):
                if handle is not None:
                    try:
                        backend.close(handle)
                    except Exception:
                        pass
            if parent_handle is not None and parent_handle is not root_handle:
                try:
                    backend.close(parent_handle)
                except Exception:
                    pass
            if root_handle is not None:
                try:
                    backend.close(root_handle)
                except Exception:
                    pass

    def rollback(self, backup_id: str) -> dict[str, Any]:
        """Restore original bytes only through the native guarded platform backend."""
        if os.name != "nt":
            raise PatchRollbackError(
                "POSIX rollback is disabled until conditional target deletion/replacement "
                "can exclude uncoordinated writers safely."
            )
        return self._rollback_windows(backup_id)
