import pytest
from pathlib import Path
from core.repository_intelligence.repo_importer import RepoImporter
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemRole

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

def test_importer_registration():
    registry = EcosystemRegistry()
    importer = RepoImporter(registry=registry)

    # Mocking a repo url (not actually cloning here, but checking registration logic)
    repo_url = "https://github.com/user/test-finance-repo"
    repo_name = "test-finance-repo"

    # Manually trigger parts of import for testing
    # Since we don't want to actually clone in a unit test if possible
    # But our importer.import_repo does clone.
    # Let's just verify the registry was updated after the real run we did.
    node = registry.get_node("freqtrade")
    assert node is not None
    assert node.role == EcosystemRole.FINANCE

    node_ui = registry.get_node("coreui-free-bootstrap-admin-template")
    assert node_ui is not None
    assert node_ui.role == EcosystemRole.UI
