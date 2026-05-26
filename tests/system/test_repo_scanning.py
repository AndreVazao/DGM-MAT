import pytest
from core.repository_cognition.repo_scanner import CognitiveRepoScanner

def test_repo_indexing_and_scanning():
    scanner = CognitiveRepoScanner(root_path=".")
    # Use current repo for scanning test
    results = scanner.scan()
    assert results is not None
    assert len(results) > 0
