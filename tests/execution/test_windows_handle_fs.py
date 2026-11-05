import os

import pytest

from core.execution.windows_handle_fs import (
    WindowsDirectoryHandleBackend,
    WindowsHandleError,
)


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows handle tests run only on Windows.")


def test_open_directory_handle_blocks_parent_rename(tmp_path):
    root = tmp_path / "repo"
    source = root / "src"
    source.mkdir(parents=True)
    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    child_handle = None
    try:
        child_handle = backend.open_child_directory(root_handle, "src")
        with pytest.raises(OSError):
            os.rename(source, root / "src-moved")
        assert source.is_dir()
    finally:
        if child_handle:
            backend.close(child_handle)
        backend.close(root_handle)


def test_relative_handle_create_write_and_rename(tmp_path):
    root = tmp_path / "repo"
    source = root / "src"
    source.mkdir(parents=True)
    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    source_handle = backend.open_child_directory(root_handle, "src")
    temporary_handle = None
    try:
        temporary_handle = backend.create_file(source_handle, ".dgm-temp-01")
        backend.write_all(temporary_handle, b"native-handle-write\\n")
        backend.rename_relative(
            temporary_handle,
            None,
            "module.py",
            replace_existing=False,
        )
        backend.close(temporary_handle)
        temporary_handle = None
        assert (source / "module.py").read_bytes() == b"native-handle-write\\n"
    finally:
        if temporary_handle:
            backend.close(temporary_handle)
        backend.close(source_handle)
        backend.close(root_handle)

def test_relative_handle_replace_existing_file(tmp_path):
    root = tmp_path / "repo"
    source = root / "src"
    source.mkdir(parents=True)
    target = source / "module.py"
    target.write_bytes(b"old\\n")
    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    source_handle = backend.open_child_directory(root_handle, "src")
    original_handle = None
    temporary_handle = None
    try:
        original_handle = backend.open_file(source_handle, "module.py")
        assert backend.read_all(original_handle, max_bytes=100) == b"old\\n"
        backend.close(original_handle)
        original_handle = None

        temporary_handle = backend.create_file(source_handle, ".dgm-temp-02")
        backend.write_all(temporary_handle, b"new\\n")
        backend.rename_relative(
            temporary_handle,
            None,
            "module.py",
            replace_existing=True,
        )
        backend.close(temporary_handle)
        temporary_handle = None
        assert target.read_bytes() == b"new\\n"
    finally:
        if original_handle:
            backend.close(original_handle)
        if temporary_handle:
            backend.close(temporary_handle)
        backend.close(source_handle)
        backend.close(root_handle)

def test_reparse_point_directory_is_rejected(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "linked"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation is unavailable: {type(exc).__name__}")

    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    try:
        with pytest.raises(WindowsHandleError):
            backend.open_child_directory(root_handle, "linked")
    finally:
        backend.close(root_handle)


def test_open_root_blocks_root_directory_replacement(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    try:
        with pytest.raises(OSError):
            os.rename(root, tmp_path / "repo-moved")
        assert root.is_dir()
    finally:
        backend.close(root_handle)


@pytest.mark.parametrize("name", ["..", ".", "nested/file.py", "nested\\\\file.py", "C:drive-relative.py", "trailing.", "trailing "])
def test_windows_backend_rejects_non_basename_components(name):
    backend = WindowsDirectoryHandleBackend()
    with pytest.raises(WindowsHandleError):
        backend._validate_basename(name)


def test_exclusive_target_handle_blocks_external_write_and_rename(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "target.txt"
    target.write_bytes(b"original\\n")
    backend = WindowsDirectoryHandleBackend()
    root_handle = backend.open_root(root)
    target_handle = None
    try:
        target_handle = backend.open_file(root_handle, "target.txt", exclusive=True)
        assert backend.read_all(target_handle, max_bytes=100) == b"original\\n"
        with pytest.raises(OSError):
            target.write_bytes(b"external-change\\n")
        with pytest.raises(OSError):
            os.rename(target, root / "target-moved.txt")
        backend.truncate_file(target_handle)
        backend.write_all(target_handle, b"controlled-change\\n")
        backend.reset_file_pointer(target_handle)
        assert backend.read_all(target_handle, max_bytes=100) == b"controlled-change\\n"
        assert target.exists()
        assert not (root / "target-moved.txt").exists()
    finally:
        if target_handle:
            backend.close(target_handle)
        backend.close(root_handle)
