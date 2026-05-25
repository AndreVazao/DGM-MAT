import pytest
import os
import json
from datetime import datetime
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemRole, EcosystemStatus
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_lifecycle import EcosystemLifecycle
from core.storage.storage_manager import storage_manager

@pytest.fixture
def clean_registry():
    registry_path = storage_manager.get_path("federation", "ecosystem_registry.json")
    if registry_path.exists():
        registry_path.unlink()
    registry = EcosystemRegistry()
    return registry

def test_registry_initialization(clean_registry):
    nodes = clean_registry.list_nodes()
    assert len(nodes) > 0
    os_node = clean_registry.get_node("DGM-MAT-OS")
    assert os_node is not None
    assert os_node.status == EcosystemStatus.ACTIVE
    assert os_node.role == EcosystemRole.CORE

def test_register_node(clean_registry):
    new_node = EcosystemNode(name="DGM-MAT-Test", role=EcosystemRole.EXPERIMENTAL)
    clean_registry.register_node(new_node)

    retrieved = clean_registry.get_node("DGM-MAT-Test")
    assert retrieved is not None
    assert retrieved.name == "DGM-MAT-Test"
    assert retrieved.role == EcosystemRole.EXPERIMENTAL
    assert retrieved.status == EcosystemStatus.PLANNED

def test_lifecycle_provision(clean_registry):
    lifecycle = EcosystemLifecycle(clean_registry)
    node = lifecycle.provision("DGM-MAT-New", "product", "Test description")

    assert node.name == "DGM-MAT-New"
    assert node.role == EcosystemRole.PRODUCT
    assert node.status == EcosystemStatus.PLANNED
    assert node.description == "Test description"

    assert clean_registry.get_node("DGM-MAT-New") is not None

def test_lifecycle_transitions(clean_registry):
    lifecycle = EcosystemLifecycle(clean_registry)
    lifecycle.provision("DGM-MAT-Transition", "infra")

    lifecycle.activate("DGM-MAT-Transition")
    assert clean_registry.get_node("DGM-MAT-Transition").status == EcosystemStatus.ACTIVE

    lifecycle.deprecate("DGM-MAT-Transition")
    assert clean_registry.get_node("DGM-MAT-Transition").status == EcosystemStatus.DEPRECATED

    lifecycle.archive("DGM-MAT-Transition")
    assert clean_registry.get_node("DGM-MAT-Transition").status == EcosystemStatus.ARCHIVED

def test_health_check(clean_registry):
    lifecycle = EcosystemLifecycle(clean_registry)
    lifecycle.provision("DGM-MAT-Health", "agents")

    lifecycle.health_check("DGM-MAT-Health", 0.85)
    assert clean_registry.get_node("DGM-MAT-Health").health_score == 0.85

def test_persistence(clean_registry):
    clean_registry.register_node(EcosystemNode(name="Persist-Node", role=EcosystemRole.DATA))
    clean_registry.save()

    new_registry = EcosystemRegistry()
    assert new_registry.get_node("Persist-Node") is not None
    assert new_registry.get_node("Persist-Node").role == EcosystemRole.DATA
