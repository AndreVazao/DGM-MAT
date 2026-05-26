import pytest
from core.provider_mesh.consensus_engine import ConsensusEngine
from core.provider_mesh.provider_ranker import ProviderRanker

def test_consensus_generation():
    engine = ConsensusEngine()
    consensus = engine.generate_consensus(["A", "A", "B"])
    assert consensus == "A"

def test_provider_ranking():
    ranker = ProviderRanker()
    ranks = ranker.rank_providers({})
    assert len(ranks) > 0
    assert "claude" in ranks[0].lower() or "gpt" in ranks[0].lower()
