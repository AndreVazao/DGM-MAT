import pytest
from core.autonomy.repo_analysis_pipeline import RepoAnalysisPipeline

def test_analysis_report():
    pipeline = RepoAnalysisPipeline()
    report = pipeline.analyze_repo("test_repo", ".")
    assert report.repo_id == "test_repo"
    assert report.score >= 0
