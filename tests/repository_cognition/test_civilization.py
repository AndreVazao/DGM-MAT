import pytest
from core.repository_cognition.repository_civilizer import RepositoryCivilizer

def test_capability_extraction():
    civilizer = RepositoryCivilizer()
    caps = civilizer.extract_capabilities([])
    assert len(caps) > 0

def test_repo_categorization():
    civilizer = RepositoryCivilizer()
    cat = civilizer.categorize_repository([])
    assert cat == "distributed_system"
