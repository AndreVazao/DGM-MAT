import pytest
from pathlib import Path
from core.repository_intelligence.tech_detector import detect_tech_stack
from core.repository_intelligence.repo_classifier import classify_repo
from core.repository_intelligence.models import RepositoryInfo
from core.repository_intelligence.duplicate_detector import DuplicateDetector

def test_tech_detector(tmp_path):
    (tmp_path / "package.json").touch()
    (tmp_path / "requirements.txt").touch()
    stack = detect_tech_stack(tmp_path)
    assert "Node.js" in stack
    assert "Python" in stack

def test_repo_classifier(tmp_path):
    mobile_path = tmp_path / "my-mobile-app"
    mobile_path.mkdir()
    category = classify_repo(mobile_path, [])
    assert category == "mobile"

    python_path = tmp_path / "backend-service"
    python_path.mkdir()
    category = classify_repo(python_path, ["Python"])
    assert category == "backend"

def test_duplicate_detector():
    repos = [
        RepositoryInfo(name="repo1", path=Path("/tmp/repo1"), tech_stack=["Python"], total_files=10, has_git=True, category="backend"),
        RepositoryInfo(name="repo2", path=Path("/tmp/repo2"), tech_stack=["Python"], total_files=12, has_git=True, category="backend"),
        RepositoryInfo(name="repo3", path=Path("/tmp/repo3"), tech_stack=["Node.js"], total_files=5, has_git=False, category="general"),
    ]
    detector = DuplicateDetector()
    duplicates = detector.detect(repos)
    assert len(duplicates) == 1
    assert duplicates[0]["stack"] == ("Python",)
    assert "repo1" in duplicates[0]["repos"]
    assert "repo2" in duplicates[0]["repos"]
