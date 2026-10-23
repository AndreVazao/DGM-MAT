import pytest

from core.provider_mesh.consensus_engine import ConsensusEngine
from core.provider_mesh.provider_ranker import ProviderRanker
from core.provider_sync.provider_registry import (
    provider_registry,
    initialize_default_providers,
)


@pytest.fixture(autouse=True)
def setup_providers(monkeypatch):
    # Ranking must reflect only explicitly registered providers.
    monkeypatch.setattr(provider_registry, "_providers", {})
    initialize_default_providers()


def test_consensus_generation():
    engine = ConsensusEngine()
    consensus = engine.generate_consensus(["A", "A", "B"])
    assert consensus == "A"


def test_provider_ranking():
    ranker = ProviderRanker()
    ollama = provider_registry.get_provider("ollama")

    # A provider without an actual health observation must not be ranked.
    assert ranker.rank_for_mission("coding") == []

    ollama.update_capabilities(coding=0.95)
    ollama.health_metrics["last_check"] = 1
    ollama.health_metrics["status"] = "ok"

    ranks = ranker.rank_for_mission("coding")
    assert ranks == ["ollama"]
    assert "chatgpt" not in ranks
