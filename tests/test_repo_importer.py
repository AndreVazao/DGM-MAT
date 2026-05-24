import pytest
from pathlib import Path
from core.repository_intelligence.repo_importer import RepoImporter
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemRole, EcosystemNode, EcosystemStatus

def test_classifier_logic():
    from core.repository_intelligence.repo_classifier import classify_repo

    # Test cases for new logic
    assert classify_repo(Path("gpt4free"), []) == "labs"
    assert classify_repo(Path("freqtrade"), []) == "finance"
    assert classify_repo(Path("coreui-admin"), []) == "ui"
    assert classify_repo(Path("public-apis"), []) == "connectors"
    assert classify_repo(Path("openai-provider"), []) == "providers"
    assert classify_repo(Path("dgm-mat-core"), []) == "core"
    assert classify_repo(Path("random-repo"), []) == "external-labs"

def test_importer_registration(tmp_path):
    registry = EcosystemRegistry()

    # Manually register nodes to simulate successful imports for testing
    registry.register_node(EcosystemNode(name="freqtrade", role=EcosystemRole.FINANCE, status=EcosystemStatus.ACTIVE))
    registry.register_node(EcosystemNode(name="coreui-free-bootstrap-admin-template", role=EcosystemRole.UI, status=EcosystemStatus.ACTIVE))

    node = registry.get_node("freqtrade")
    assert node is not None
    assert node.role == EcosystemRole.FINANCE

    node_ui = registry.get_node("coreui-free-bootstrap-admin-template")
    assert node_ui is not None
    assert node_ui.role == EcosystemRole.UI
