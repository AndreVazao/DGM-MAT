import pytest
import importlib

def test_critical_imports():
    critical_modules = [
        "pydantic",
        "requests",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "loguru",
        "rich",
        "networkx",
        "psutil"
    ]
    for module in critical_modules:
        try:
            importlib.import_module(module)
        except ImportError as e:
            pytest.fail(f"Critical module '{module}' failed to import: {e}")

def test_subsystem_dependencies():
    # Test that core subsystems can be imported without missing dependencies
    subsystems = [
        "core.runtime.runtime",
        "core.event_bus.event_bus",
        "core.repository_intelligence.github_client",
        "core.storage.storage_manager",
        "core.governance.governance_engine"
    ]
    for subsys in subsystems:
        try:
            importlib.import_module(subsys)
        except ImportError as e:
            pytest.fail(f"Subsystem '{subsys}' failed to import: {e}")
