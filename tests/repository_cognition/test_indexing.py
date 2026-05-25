import pytest
from pathlib import Path
from core.repository_cognition.architecture_mapper import ArchitectureMapper

def test_architecture_mapper():
    mapper = ArchitectureMapper()
    # Simple test
    assert mapper is not None
