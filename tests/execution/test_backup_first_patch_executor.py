import hashlib

import pytest

from core.execution.backup_first_patch_executor import (
    BackupFirstPatchExecutor,
    PatchBackupError,
    PatchRejected,
    PatchRollbackError,
)


def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "src").mkdir()
    return root


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def test_create_can_be_rolled_back_by_removing_only_created_file(tmp_path):
    root = repository(tmp_path)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    result = executor.apply_text("src/new.py", "print('safe')\n")

    assert (root / "src" / "new.py").is_file()
    assert result["operation"] == "create"
    executor.rollback(result["backup_id"])
    assert not (root / "src" / "new.py").exists()


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
    (root / "src" / "linked").symlink_to(outside, target_is_directory=True)
    executor = BackupFirstPatchExecutor(root, backup_root=tmp_path / "backups")

    with pytest.raises(PatchRejected):
        executor.apply_text("src/linked/escape.py", "blocked\n")


def test_backup_root_inside_repository_is_rejected(tmp_path):
    root = repository(tmp_path)

    with pytest.raises(PatchRejected, match="outside"):
        BackupFirstPatchExecutor(root, backup_root=root / ".backups")


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
