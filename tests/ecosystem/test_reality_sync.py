import pytest
import os
import json
from pathlib import Path
from core.ecosystem.reality_sync_engine import RealitySyncEngine
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemRole, EcosystemStatus

def test_reality_sync_detects_missing(tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "ProgramasGodMode"
    workspace.mkdir()

    # Setup mock registry
    registry = EcosystemRegistry()
    registry.register_node(EcosystemNode(name="MissingRepo", role=EcosystemRole.LABS, status=EcosystemStatus.ACTIVE))
    registry.save()

    engine = RealitySyncEngine(workspace_root=str(workspace))
    report = engine.run_sync()

    assert "MissingRepo" in report["details"]["missing"]
    assert report["summary"]["missing"] >= 1

def test_reality_sync_detects_orphans(tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "ProgramasGodMode"
    workspace.mkdir()
    orphan_repo = workspace / "OrphanRepo"
    orphan_repo.mkdir()
    (orphan_repo / ".git").mkdir()

    engine = RealitySyncEngine(workspace_root=str(workspace))
    report = engine.run_sync()

    assert "OrphanRepo" in report["details"]["orphans"]
    assert report["summary"]["orphans"] >= 1

def test_reality_sync_detects_broken(tmp_path):
    # Setup mock workspace
    workspace = tmp_path / "ProgramasGodMode"
    workspace.mkdir()

    # Setup mock registry
    registry = EcosystemRegistry()
    registry.register_node(EcosystemNode(name="BrokenRepo", role=EcosystemRole.LABS, status=EcosystemStatus.ACTIVE))
    registry.save()

    engine = RealitySyncEngine(workspace_root=str(workspace))
    report = engine.run_sync()

    assert "BrokenRepo" in report["details"]["broken"]
    assert report["summary"]["broken"] >= 1
