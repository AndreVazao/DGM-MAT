import pytest
from core.provider_mesh.consensus_engine import ConsensusEngine
from core.provider_mesh.provider_ranker import ProviderRanker
from core.provider_sync.provider_registry import initialize_default_providers

@pytest.fixture(autouse=True)
def setup_providers():
    initialize_default_providers()

def test_consensus_generation():
    engine = ConsensusEngine()
    consensus = engine.generate_consensus(["A", "A", "B"])
    assert consensus == "A"

def test_provider_ranking():
    ranker = ProviderRanker()
    ranks = ranker.rank_for_mission("coding")
    assert len(ranks) > 0
    # chatgpt has coding: 0.95, it should be top if available
    assert ranks[0] == "chatgpt"
