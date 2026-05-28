import pytest
from core.runtime.reality_snapshot import RealitySnapshotService

def test_snapshot_structure():
    service = RealitySnapshotService(workspace_root="/tmp")
    data = service.snapshot()

    assert "timestamp" in data
    assert "machine" in data
    assert "runtime" in data
    assert "providers" in data
    assert "repos" in data
    assert "agents" in data
    assert "workspaces" in data
    assert "processes" in data
    assert "memory" in data

def test_snapshot_summary():
    service = RealitySnapshotService(workspace_root="/tmp")
    summary = service.snapshot_summary()

    assert "timestamp" in summary
    assert "total_repos" in summary
    assert "total_processes" in summary
    assert "active_providers" in summary
    assert "is_runtime_healthy" in summary
