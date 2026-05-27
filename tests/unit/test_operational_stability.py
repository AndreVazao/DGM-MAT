import pytest
from core.knowledge.memory_indexer import MemoryIndexer
from core.repository_cognition.repo_scanner import CognitiveRepoScanner

def test_memory_indexer_silence():
    # MemoryIndexer should handle Empty queue silently
    indexer = MemoryIndexer(queue_size=1)
    # The worker thread is running. If it was spamming errors,
    # we'd see them in the logs if we had a log capturer.
    # For now, just ensure it starts and stops.
    indexer.shutdown()

def test_repo_scanner_exclusions():
    scanner = CognitiveRepoScanner(root_path=".")
    assert ".git" in scanner.exclusions
    assert ".runtime" in scanner.exclusions
