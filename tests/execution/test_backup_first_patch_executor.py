import hashlib
import json
import os
import subprocess

import pytest

from core.execution.backup_first_patch_executor import (
    BackupFirstPatchExecutor,
    PatchBackupError,
    PatchRejected,
    PatchRollbackError,
)




requires_posix_directory_handles = pytest.mark.skip(
    reason="POSIX mutation is intentionally fail-closed until conditional replacement/deletion can exclude uncoordinated writers.",
)

def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", str(root)],
        check=True,
        capture_output=True,
    )
    (root / "src").mkdir()
    return root


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@requires_posix_directory_handles
def test_replace_creates_verified_backup_and_rollback_restores_original(tmp_path):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "module.py"
    target.write_text("value = 1\n", encoding="utf-8")
    original = target.read_bytes()
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    result = executor.apply_text(
        "src/module.py",
        "value = 2\n",
        expected_sha256=digest(original),
    )

    assert target.read_text(encoding="utf-8") == "value = 2\n"
    assert result["original_sha256"] == digest(original)
    assert result["result_sha256"] == digest(b"value = 2\n")
    assert (backup_root / result["backup_id"] / "original.bin").read_bytes() == original

    rolled_back = executor.rollback(result["backup_id"])
    assert target.read_bytes() == original
    assert rolled_back["rollback_available"] is False


@requires_posix_directory_handles
def test_create_can_be_rolled_back_by_removing_only_created_file(tmp_path):
    root = repository(tmp_path)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    result = executor.apply_text("src/new.py", "print('safe')\n")

    assert (root / "src" / "new.py").is_file()
    assert result["operation"] == "create"
    executor.rollback(result["backup_id"])
    assert not (root / "src" / "new.py").exists()


@requires_posix_directory_handles
def test_original_file_size_is_bounded_before_backup_or_replacement(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "large.txt"
    original = b"x" * 11
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(
        root,
        backup_root=tmp_path / "backups",
        max_file_bytes=10,
    )

    with pytest.raises(PatchRejected, match="Original file exceeds"):
        executor.apply_text(
            "src/large.txt",
            "small",
            expected_sha256=digest(original),
        )

    assert target.read_bytes() == original
    assert not (tmp_path / "backups").exists()


@requires_posix_directory_handles
def test_existing_file_requires_matching_expected_hash(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    target.write_text("old\n", encoding="utf-8")
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected, match="expected_sha256"):
        executor.apply_text("src/module.py", "new\n", expected_sha256="0" * 64)

    assert target.read_text(encoding="utf-8") == "old\n"


@pytest.mark.skipif(os.name != "nt", reason="Windows 8.3 alias validation.")
@pytest.mark.parametrize("path", ["src/CREDE~10.JSO", "src/PROGRA~12.TXT"])
def test_windows_short_name_aliases_with_multiple_digits_are_rejected(tmp_path, path):
    root = repository(tmp_path)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected, match="8.3 short-name"):
        executor._relative_target(path)


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd", ".env", "secrets/key.txt", "secre~1/key.txt", ".git/config", "id_rsa"])
def test_protected_and_escaping_paths_are_rejected(tmp_path, path):
    root = repository(tmp_path)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected):
        executor.apply_text(path, "blocked\n")


def test_symlink_escape_is_rejected(tmp_path):
    root = repository(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "src" / "linked").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation is unavailable in this test environment: {type(exc).__name__}")
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected, match="Symbolic-link"):
        executor._relative_target("src/linked/escape.py")

def test_backup_root_inside_repository_is_rejected(tmp_path):
    root = repository(tmp_path)

    with pytest.raises(PatchRejected, match="outside"):
        BackupFirstPatchExecutor(root, backup_root=root / ".backups")


@requires_posix_directory_handles
def test_rollback_refuses_to_overwrite_changes_made_after_patch(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    target.write_text("before\n", encoding="utf-8")
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    result = executor.apply_text("src/module.py", "patched\n", expected_sha256=digest(target.read_bytes()))
    target.write_text("later change\n", encoding="utf-8")

    with pytest.raises(PatchRollbackError, match="changed after"):
        executor.rollback(result["backup_id"])

    assert target.read_text(encoding="utf-8") == "later change\n"


@pytest.mark.skip(reason="POSIX mutation is intentionally fail-closed.")
def test_parent_directory_symlink_swap_after_open_cannot_redirect_patch(tmp_path, monkeypatch):
    if os.name != "posix":
        pytest.skip("Pinned dir_fd regression requires POSIX directory handles.")
    root = repository(tmp_path)
    source_dir = root / "src"
    outside = tmp_path / "outside"
    outside.mkdir()
    (source_dir / "module.py").write_text("inside-old\n", encoding="utf-8")
    outside_target = outside / "module.py"
    outside_target.write_text("outside-original\n", encoding="utf-8")
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    original_open_parent = executor._open_parent_fd
    swapped = False

    def open_then_swap(normalized):
        nonlocal swapped
        parent_fd, name = original_open_parent(normalized)
        if not swapped:
            os.rename(source_dir, root / "src-pinned")
            os.symlink(outside, source_dir, target_is_directory=True)
            swapped = True
        return parent_fd, name

    monkeypatch.setattr(executor, "_open_parent_fd", open_then_swap)
    old = b"inside-old\n"
    result = executor.apply_text(
        "src/module.py",
        "inside-new\n",
        expected_sha256=digest(old),
    )

    assert swapped is True
    assert outside_target.read_text(encoding="utf-8") == "outside-original\n"
    assert (root / "src-pinned" / "module.py").read_text(encoding="utf-8") == "inside-new\n"
    assert result["relative_path"] == "src/module.py"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows integration test.")
@pytest.mark.parametrize("expected_hash", [None, "0" * 64])
def test_windows_existing_file_rejects_missing_or_mismatched_hash_without_mutation(tmp_path, expected_hash):
    root = repository(tmp_path)
    target = root / "src" / "guarded.py"
    original = b"original bytes\\n"
    target.write_bytes(original)
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    with pytest.raises(PatchRejected, match="matching expected_sha256"):
        executor.apply_text("src/guarded.py", "must not replace\\n", expected_sha256=expected_hash)

    assert target.read_bytes() == original
    assert not backup_root.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows integration test.")
def test_windows_backup_first_replace_and_rollback(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"value = 1\\n"
    target.write_bytes(original)
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    result = executor.apply_text(
        "src/module.py",
        "value = 2\\n",
        expected_sha256=digest(original),
    )

    assert target.read_bytes() == b"value = 2\\n"
    backup_dir = backup_root / result["backup_id"]
    assert (backup_dir / "original.bin").read_bytes() == original
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["result_sha256"] == digest(b"value = 2\\n")
    assert manifest["original_sha256"] == digest(original)

    rolled_back = executor.rollback(result["backup_id"])
    assert target.read_bytes() == original
    assert rolled_back["rollback_available"] is False
    persisted = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert persisted["rollback_available"] is False
    with pytest.raises(PatchRollbackError, match="already been rolled back"):
        executor.rollback(result["backup_id"])


@pytest.mark.skipif(os.name != "nt", reason="Native Windows integration test.")
def test_windows_backup_first_create_and_rollback(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "created.py"
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    result = executor.apply_text("src/created.py", "print('safe')\\n")

    assert target.read_text(encoding="utf-8") == "print('safe')\\n"
    assert result["operation"] == "create"
    assert (backup_root / result["backup_id"] / "manifest.json").is_file()

    rolled_back = executor.rollback(result["backup_id"])
    assert not target.exists()
    assert rolled_back["rollback_available"] is False


@requires_posix_directory_handles
def test_repository_root_replacement_after_initialization_is_rejected(tmp_path):
    root = repository(tmp_path)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    pinned_root = tmp_path / "repo-pinned"
    os.rename(root, pinned_root)

    replacement_root = tmp_path / "repo"
    replacement_root.mkdir()
    (replacement_root / ".git").mkdir()
    (replacement_root / "src").mkdir()
    replacement_target = replacement_root / "src" / "module.py"
    replacement_target.write_text("replacement-root-unchanged\\n", encoding="utf-8")

    with pytest.raises(PatchRejected, match="Repository root changed"):
        executor.apply_text("src/module.py", "must-not-write\\n")

    assert replacement_target.read_text(encoding="utf-8") == "replacement-root-unchanged\\n"
    assert not (tmp_path / "backups").exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows integration test.")
def test_windows_rollback_refuses_replaced_target_identity(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"before\\n"
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    result = executor.apply_text(
        "src/module.py",
        "after\\n",
        expected_sha256=digest(original),
    )

    moved = target.with_name("module-original-after-patch.py")
    os.rename(target, moved)
    target.write_bytes(b"newer independent file\\n")

    with pytest.raises(PatchRollbackError, match="identity changed"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"newer independent file\\n"
    assert moved.read_bytes() == b"after\\n"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows conflict integration test.")
def test_windows_rollback_refuses_newer_content_with_same_file_identity(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"before\\n"
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    result = executor.apply_text(
        "src/module.py",
        "patched\\n",
        expected_sha256=digest(original),
    )
    target.write_bytes(b"newer-content-same-file\\n")

    with pytest.raises(PatchRollbackError, match="changed after the patch"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"newer-content-same-file\\n"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows hard-link integration test.")
def test_windows_executor_rejects_hard_linked_target(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    external = tmp_path / "outside-hardlink.py"
    original = b"original-hardlink-content\\n"
    target.write_bytes(original)
    try:
        os.link(target, external)
    except OSError as exc:
        pytest.skip(f"Hard-link creation is unavailable: {type(exc).__name__}")

    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    with pytest.raises(PatchRejected, match="(?i)hard.link"):
        executor.apply_text(
            "src/module.py",
            "must-not-modify\\n",
            expected_sha256=digest(original),
        )

    assert target.read_bytes() == original
    assert external.read_bytes() == original
    assert not (tmp_path / "backups").exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows hard-link rollback test.")
def test_windows_rollback_refuses_hard_linked_target(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    external = tmp_path / "outside-hardlink.py"
    original = b"original\\n"
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    result = executor.apply_text(
        "src/module.py",
        "patched\\n",
        expected_sha256=digest(original),
    )
    try:
        os.link(target, external)
    except OSError as exc:
        pytest.skip(f"Hard-link creation is unavailable: {type(exc).__name__}")

    with pytest.raises(PatchRollbackError, match="(?i)hard.link"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"patched\\n"
    assert external.read_bytes() == b"patched\\n"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows hard-link integration test.")
def test_windows_apply_rejects_hard_linked_target_without_mutation(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    linked = root / "src" / "linked-copy.py"
    original = b"original-content"
    target.write_bytes(original)
    try:
        os.link(target, linked)
    except OSError as exc:
        pytest.skip(f"Hard-link creation unavailable: {type(exc).__name__}")
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    with pytest.raises(PatchRejected, match="(?i)hard.link"):
        executor.apply_text(
            "src/module.py",
            "replacement",
            expected_sha256=digest(original),
        )

    assert target.read_bytes() == original
    assert linked.read_bytes() == original
    assert not backup_root.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows hard-link integration test.")
def test_windows_rollback_rejects_target_that_becomes_hard_linked(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    linked = root / "src" / "linked-copy.py"
    original = b"original-content"
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")
    result = executor.apply_text(
        "src/module.py",
        "patched-content",
        expected_sha256=digest(original),
    )
    os.link(target, linked)

    with pytest.raises(PatchRollbackError, match="(?i)hard.link"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"patched-content"
    assert linked.read_bytes() == b"patched-content"


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only fail-closed policy.")
def test_posix_mutation_is_rejected_until_conditional_writes_are_available(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"keep unchanged"
    target.write_bytes(original)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected, match="POSIX mutation is disabled"):
        executor.apply_text("src/module.py", "must-not-write")

    with pytest.raises(PatchRollbackError, match="POSIX rollback is disabled"):
        executor.rollback("untrusted-id")

    assert target.read_bytes() == original
    assert not (tmp_path / "backups").exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows manifest identity integration test.")
def test_windows_rollback_rejects_manifest_from_different_repository_identity(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"original"
    target.write_bytes(original)
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = executor.apply_text(
        "src/module.py",
        "patched",
        expected_sha256=digest(original),
    )
    manifest_path = backup_root / result["backup_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["repository_identity"] = [0, 0]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with pytest.raises(PatchRollbackError, match="repository identity"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"patched"


def test_fake_git_marker_is_not_accepted_as_worktree(tmp_path):
    root = tmp_path / "fake-repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "src").mkdir()

    with pytest.raises(PatchRejected, match="valid Git working tree"):
        BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")


def test_nested_directory_is_not_accepted_as_worktree_root(tmp_path):
    root = repository(tmp_path)
    nested = root / "src" / "nested"
    nested.mkdir()
    (nested / ".git").mkdir()

    with pytest.raises(PatchRejected, match="top-level directory"):
        BackupFirstPatchExecutor(nested, backup_root=tmp_path / "backups")


@pytest.mark.skipif(os.name != "nt", reason="Native Windows manifest validation test.")
def test_windows_rollback_rejects_inconsistent_operation_backup_metadata(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "new.py"
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = executor.apply_text("src/new.py", "created")

    manifest_path = backup_root / result["backup_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operation"] = "replace"
    manifest["backup_file"] = None
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with pytest.raises(PatchRollbackError, match="inconsistent"):
        executor.rollback(result["backup_id"])

    assert target.read_text(encoding="utf-8") == "created"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows staged-create recovery test.")
def test_windows_create_crash_before_identity_persistence_never_creates_repo_target(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    backend = executor._windows_backend
    assert backend is not None
    original_create = backend.create_file

    def create_then_interrupt(parent_handle, name, *, exclusive=False):
        handle = original_create(parent_handle, name, exclusive=exclusive)
        if name == "created-content.stage":
            # A real process/power loss closes all process handles; simulate
            # that OS cleanup before raising the interruption.
            backend.close(handle)
            raise SystemExit("simulated power loss immediately after FILE_CREATE")
        return handle

    monkeypatch.setattr(backend, "create_file", create_then_interrupt)
    with pytest.raises(SystemExit, match="simulated power loss"):
        executor.apply_text("src/new.py", "new content")

    assert not target.exists()
    backup_dirs = list(backup_root.iterdir())
    assert len(backup_dirs) == 1
    manifest = json.loads((backup_dirs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["state"] == "prepared"
    assert manifest["operation"] == "create"
    assert manifest["target_identity"] is None
    assert (backup_dirs[0] / manifest["staging_name"]).is_file()

    monkeypatch.setattr(backend, "create_file", original_create)
    recovered_executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    with pytest.raises(PatchRollbackError, match="identity was not persisted"):
        recovered_executor.rollback(manifest["backup_id"])
    assert not target.exists()
    assert (backup_dirs[0] / manifest["staging_name"]).is_file()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows staged-create integration test.")
def test_windows_staged_create_persists_identity_before_atomic_promotion(tmp_path):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)

    result = executor.apply_text("src/new.py", "new content")

    assert target.read_text(encoding="utf-8") == "new content"
    assert result["target_identity"] is not None
    assert not (backup_root / result["backup_id"] / result["staging_name"]).exists()
    assert result["state"] == "applied"
    rolled_back = executor.rollback(result["backup_id"])
    assert rolled_back["state"] == "rolled_back"
    assert not target.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows staged-create recovery test.")
def test_windows_create_crash_after_identity_persisted_recovers_staging_file(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    backend = executor._windows_backend
    assert backend is not None
    original_rename = backend.rename_relative

    def interrupt_before_promotion(source_handle, parent_handle, target_name, *, replace_existing):
        if target_name == "new.py":
            raise SystemExit("simulated power loss before staged promotion")
        return original_rename(
            source_handle, parent_handle, target_name,
            replace_existing=replace_existing,
        )

    monkeypatch.setattr(backend, "rename_relative", interrupt_before_promotion)
    with pytest.raises(SystemExit, match="before staged promotion"):
        executor.apply_text("src/new.py", "new content")

    assert not target.exists()
    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["target_identity"] is not None
    assert (backup_dir / manifest["staging_name"]).is_file()

    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = recovered.rollback(manifest["backup_id"])
    assert result["state"] == "rolled_back"
    assert not target.exists()
    assert not (backup_dir / manifest["staging_name"]).exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows staged-create recovery test.")
def test_windows_create_crash_after_promotion_recovers_repository_target(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    original_write_manifest = executor._write_manifest_windows

    def interrupt_before_applied_manifest(directory_handle, manifest, *, replace_existing):
        if manifest.get("state") == "applied":
            raise SystemExit("simulated power loss after promotion")
        return original_write_manifest(
            directory_handle, manifest, replace_existing=replace_existing
        )

    monkeypatch.setattr(executor, "_write_manifest_windows", interrupt_before_applied_manifest)
    with pytest.raises(SystemExit, match="after promotion"):
        executor.apply_text("src/new.py", "new content")

    assert target.read_text(encoding="utf-8") == "new content"
    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["state"] == "prepared"
    assert manifest["target_identity"] is not None
    assert not (backup_dir / manifest["staging_name"]).exists()

    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = recovered.rollback(manifest["backup_id"])
    assert result["state"] == "rolled_back"
    assert not target.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows prepared-create conflict test.")
def test_windows_prepared_create_refuses_to_delete_newer_content(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    original_write_manifest = executor._write_manifest_windows

    def interrupt_before_applied_manifest(directory_handle, manifest, *, replace_existing):
        if manifest.get("state") == "applied":
            raise SystemExit("simulated power loss after promotion")
        return original_write_manifest(
            directory_handle, manifest, replace_existing=replace_existing
        )

    monkeypatch.setattr(executor, "_write_manifest_windows", interrupt_before_applied_manifest)
    with pytest.raises(SystemExit, match="after promotion"):
        executor.apply_text("src/new.py", "new content")

    target.write_text("newer independent content", encoding="utf-8")
    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)

    with pytest.raises(PatchRollbackError, match="changed after promotion"):
        recovered.rollback(manifest["backup_id"])
    assert target.read_text(encoding="utf-8") == "newer independent content"


@pytest.mark.skipif(os.name != "nt", reason="Native Windows staged-create failure recovery test.")
def test_windows_create_apply_error_preserves_prepared_target_for_explicit_rollback(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    original_write_manifest = executor._write_manifest_windows

    def fail_applied_manifest(directory_handle, manifest, *, replace_existing):
        if manifest.get("state") == "applied":
            raise OSError("simulated manifest promotion failure")
        return original_write_manifest(
            directory_handle, manifest, replace_existing=replace_existing
        )

    monkeypatch.setattr(executor, "_write_manifest_windows", fail_applied_manifest)
    with pytest.raises(OSError, match="manifest promotion failure"):
        executor.apply_text("src/new.py", "new content")

    assert target.read_text(encoding="utf-8") == "new content"
    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["state"] == "prepared"
    assert manifest["target_identity"] is not None

    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = recovered.rollback(manifest["backup_id"])
    assert result["state"] == "rolled_back"
    assert not target.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows same-volume staging test.")
def test_windows_create_rejects_backup_root_on_another_volume(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "new.py"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    backend = executor._windows_backend
    assert backend is not None
    original_identity = backend.file_identity
    original_ensure = backend.ensure_directory
    backup_handles = []

    def capture_backup_root(directory, **kwargs):
        handle = original_ensure(directory, **kwargs)
        backup_handles.append(handle)
        return handle

    def report_different_volume(handle):
        identity = original_identity(handle)
        if backup_handles and getattr(handle, "value", handle) == getattr(backup_handles[0], "value", backup_handles[0]):
            return (identity[0] + 1, identity[1])
        return identity

    monkeypatch.setattr(backend, "ensure_directory", capture_backup_root)
    monkeypatch.setattr(backend, "file_identity", report_different_volume)

    with pytest.raises(PatchBackupError, match="same NTFS volume"):
        executor.apply_text("src/new.py", "new content")

    assert not target.exists()


@pytest.mark.skipif(os.name != "nt", reason="Native Windows prepared-replacement recovery test.")
@pytest.mark.parametrize(
    "post_crash_content",
    ["partial interrupted write", "newer independent writer content"],
)
def test_windows_prepared_replace_refuses_unrecognized_content(tmp_path, monkeypatch, post_crash_content):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "existing.py"
    target.write_text("original content", encoding="utf-8")
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    backend = executor._windows_backend
    assert backend is not None
    original_truncate = backend.truncate_file
    original_write = backend.write_all

    def interrupt_during_replace(handle):
        original_truncate(handle)
        original_write(handle, b"partial interrupted write")
        raise SystemExit("simulated power loss during in-place replacement")

    monkeypatch.setattr(backend, "truncate_file", interrupt_during_replace)
    with pytest.raises(SystemExit, match="during in-place replacement"):
        executor.apply_text(
            "src/existing.py",
            "expected replacement content",
            expected_sha256=hashlib.sha256(b"original content").hexdigest(),
        )

    if post_crash_content != "partial interrupted write":
        target.write_text(post_crash_content, encoding="utf-8")

    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["operation"] == "replace"
    assert manifest["state"] == "prepared"

    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)
    with pytest.raises(PatchRollbackError, match="neither the original nor the expected result"):
        recovered.rollback(manifest["backup_id"])
    assert target.read_text(encoding="utf-8") == post_crash_content


@pytest.mark.skipif(os.name != "nt", reason="Native Windows prepared-replacement recovery test.")
def test_windows_prepared_replace_restores_only_recognized_result_hash(tmp_path, monkeypatch):
    root = repository(tmp_path)
    backup_root = tmp_path / "backups"
    target = root / "src" / "existing.py"
    target.write_text("original content", encoding="utf-8")
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    backend = executor._windows_backend
    assert backend is not None
    original_write_manifest = executor._write_manifest_windows

    def interrupt_before_applied_manifest(directory_handle, manifest, *, replace_existing):
        if manifest.get("state") == "applied":
            raise SystemExit("simulated power loss after replacement")
        return original_write_manifest(
            directory_handle, manifest, replace_existing=replace_existing
        )

    monkeypatch.setattr(executor, "_write_manifest_windows", interrupt_before_applied_manifest)
    with pytest.raises(SystemExit, match="after replacement"):
        executor.apply_text(
            "src/existing.py",
            "expected replacement content",
            expected_sha256=hashlib.sha256(b"original content").hexdigest(),
        )

    backup_dir = next(backup_root.iterdir())
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["state"] == "prepared"
    recovered = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = recovered.rollback(manifest["backup_id"])
    assert result["state"] == "rolled_back"
    assert target.read_text(encoding="utf-8") == "original content"
