# Path: C:\ProgramasGodMode\DGM-MAT\tests\repository_intelligence\test_snapshot.py
from pathlib import Path

from core.repository_intelligence.snapshot import build_inventory, render_tree, write_inventory


def test_inventory_skips_dependency_folders_and_marks_sensitive_names(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("contents must not be read", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "external.js").write_text("ignored", encoding="utf-8")
    (tmp_path / ".env").write_text("DO_NOT_READ", encoding="utf-8")

    report = build_inventory(tmp_path)
    paths = [entry.path for entry in report.entries]
    assert "src/main.py" in paths
    assert ".env" in paths
    assert "node_modules/external.js" not in paths
    assert next(entry for entry in report.entries if entry.path == ".env").sensitive_name
    tree = render_tree(report)
    assert "main.py" in tree
    assert "[SENSITIVE NAME]" in tree
    assert "DO_NOT_READ" not in tree
    assert tree == render_tree(build_inventory(tmp_path))


def test_inventory_does_not_follow_symlinks(tmp_path: Path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "external.txt").write_text("external", encoding="utf-8")
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        return
    report = build_inventory(root)
    assert any(entry.path == "linked" and entry.kind == "symlink" for entry in report.entries)
    assert not any("external.txt" in entry.path for entry in report.entries)


def test_inventory_caps_entries_and_refuses_overwrite(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("a.txt", "b.txt", "c.txt"):
        (root / name).write_text("x", encoding="utf-8")
    report = build_inventory(root, max_entries=2)
    assert len(report.entries) == 2

    full_report = build_inventory(root)
    json_path = tmp_path / "out" / "tree.json"
    tree_path = tmp_path / "out" / "tree.txt"
    write_inventory(full_report, json_path=json_path, tree_path=tree_path)
    try:
        write_inventory(full_report, json_path=json_path, tree_path=tree_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing inventory reports must never be overwritten silently.")
