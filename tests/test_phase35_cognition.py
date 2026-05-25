import pytest
from pathlib import Path
from core.cognition.cognitive_analysis_engine import cognitive_engine
from core.cognition.architecture_graph import architecture_graph
from core.cognition.pattern_extractor import pattern_extractor

def test_cognitive_analysis():
    report = cognitive_engine.analyze_repository("test_repo", Path("core"))
    assert report.target_repo == "test_repo"
    assert report.quality_score > 0
    assert "Singleton" in report.patterns_detected

def test_architecture_graph():
    architecture_graph.map_module_relationships("test_repo", [{"name": "mod1", "dependencies": ["mod2"]}])
    assert "test_repo" in architecture_graph.graph
    assert "test_repo.mod1" in architecture_graph.graph
    deps = architecture_graph.get_dependencies("test_repo.mod1")
    assert "test_repo.mod2" in deps

def test_pattern_extraction():
    pattern_extractor.scan_for_patterns("test_repo", Path("core"))
    summary = pattern_extractor.get_pattern_library_summary()
    assert summary["total_patterns"] > 0
