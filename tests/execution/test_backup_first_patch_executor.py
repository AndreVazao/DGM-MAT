import hashlib
import json
import os

import pytest

from core.execution.backup_first_patch_executor import (
    BackupFirstPatchExecutor,
    PatchBackupError,
    PatchRejected,
    PatchRollbackError,
)




requires_posix_directory_handles = pytest.mark.skipif(
    os.name != "posix",
    reason="Filesystem mutation is deliberately disabled without secure POSIX directory handles.",
)

def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
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


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd", ".env", "secrets/key.txt", ".git/config", "id_rsa"])
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

    with pytest.raises(PatchRejected):
        executor.apply_text("src/linked/escape.py", "blocked\n")


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


@pytest.mark.skipif(os.name != "nt", reason="Native Windows crash-recovery integration test.")
def test_windows_prepared_manifest_recovers_partial_in_place_write(tmp_path):
    root = repository(tmp_path)
    target = root / "src" / "module.py"
    original = b"before-crash\\n"
    target.write_bytes(original)
    backup_root = tmp_path / "backups"
    executor = BackupFirstPatchExecutor(root, backup_root=backup_root)
    result = executor.apply_text(
        "src/module.py",
        "complete-new-content\\n",
        expected_sha256=digest(original),
    )

    backup_dir = backup_root / result["backup_id"]
    manifest_path = backup_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["state"] = "prepared"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    target.write_bytes(b"partial-write-from-simulated-crash")

    rolled_back = executor.rollback(result["backup_id"])

    assert target.read_bytes() == original
    assert rolled_back["state"] == "rolled_back"
    assert rolled_back["rollback_available"] is False


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
    with pytest.raises(PatchRejected, match="multiple hard links"):
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

    with pytest.raises(PatchRollbackError, match="multiple hard links"):
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

    with pytest.raises(PatchRejected, match="hard-linked"):
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

    with pytest.raises(PatchRollbackError, match="hard links"):
        executor.rollback(result["backup_id"])

    assert target.read_bytes() == b"patched-content"
    assert linked.read_bytes() == b"patched-content"
