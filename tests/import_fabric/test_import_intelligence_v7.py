import pytest
from pathlib import Path
from core.repository_intelligence.repo_importer import RepoImporter
from core.repository_intelligence.intelligence_engine import IntelligenceEngine
from core.strategy.goal_engine import GoalEngine
from core.kernel.live_kernel import LiveKernel

def test_intelligence_engine_scan():
    intel = IntelligenceEngine()
    caps = intel.scan_ecosystem()
    assert isinstance(caps, dict)
    assert len(caps) > 0

def test_intelligence_engine_gaps():
    intel = IntelligenceEngine()
    gaps = intel.detect_gaps()
    assert isinstance(gaps, list)

def test_intelligence_engine_discovery():
    intel = IntelligenceEngine()
    opps = intel.discover_opportunities()
    assert isinstance(opps, list)
    if opps:
        assert "score" in opps[0]
        assert "url" in opps[0]

def test_goal_engine_parsing():
    goal_engine = GoalEngine()
    roles = goal_engine.parse_goal("I want a trading system")
    assert "finance" in roles

def test_goal_engine_planning():
    goal_engine = GoalEngine()
    plan = goal_engine.create_plan("Build an AI agent network")
    assert len(plan) > 0
    assert any(step["role"] == "labs" for step in plan)

def test_live_kernel_cycle():
    # Run a single cycle in SAFE mode
    kernel = LiveKernel(mode="SAFE")
    # Should not raise any exceptions
    kernel.run_cycle()

def test_repo_importer_mock_setup(tmp_path):
    # Test internal helper with mock path
    importer = RepoImporter(workspace_path=tmp_path)
    # We won't run a full import_repo here as it hits network/git
    # But we can check initialization
    assert importer.workspace_path == tmp_path
