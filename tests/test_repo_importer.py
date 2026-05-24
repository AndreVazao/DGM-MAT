import pytest
from pathlib import Path
from core.repository_intelligence.repo_importer import RepoImporter
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemRole, EcosystemNode, EcosystemStatus

def test_classifier_logic():
    from core.repository_intelligence.repo_classifier import classify_repo

    # Test cases for new logic and centralized intake list
    assert classify_repo(Path("gpt4free"), []) == "labs"
    assert classify_repo(Path("freqtrade"), []) == "finance"
    assert classify_repo(Path("coreui-admin"), []) == "ui"
    assert classify_repo(Path("public-apis"), []) == "connectors"
    assert classify_repo(Path("openai-provider"), []) == "providers"
    assert classify_repo(Path("dgm-mat-core"), []) == "core"
    assert classify_repo(Path("random-repo"), []) == "external-labs"

    # New roles and specific intake list items
    assert classify_repo(Path("n8n"), []) == "core"
    assert classify_repo(Path("temporal"), []) == "core"
    assert classify_repo(Path("qdrant"), []) == "memory"
    assert classify_repo(Path("weaviate"), []) == "memory"
    assert classify_repo(Path("crewAI"), []) == "agents"
    assert classify_repo(Path("autogen"), []) == "agents"
    assert classify_repo(Path("prometheus"), []) == "infra"
    assert classify_repo(Path("grafana"), []) == "ui"
    assert classify_repo(Path("freellmapi"), []) == "providers"
    assert classify_repo(Path("AIClient2API"), []) == "connectors"

def test_importer_registration(tmp_path):
    registry = EcosystemRegistry()

    # Manually register nodes to simulate successful imports for testing
    registry.register_node(EcosystemNode(name="freqtrade", role=EcosystemRole.FINANCE, status=EcosystemStatus.ACTIVE))
    registry.register_node(EcosystemNode(name="qdrant", role=EcosystemRole.MEMORY, status=EcosystemStatus.ACTIVE))
    registry.register_node(EcosystemNode(name="crewai", role=EcosystemRole.AGENTS, status=EcosystemStatus.ACTIVE))

    node = registry.get_node("freqtrade")
    assert node is not None
    assert node.role == EcosystemRole.FINANCE

    node_memory = registry.get_node("qdrant")
    assert node_memory is not None
    assert node_memory.role == EcosystemRole.MEMORY

    node_agents = registry.get_node("crewai")
    assert node_agents is not None
    assert node_agents.role == EcosystemRole.AGENTS
