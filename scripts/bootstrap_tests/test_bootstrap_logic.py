import pytest
import os
from core.bootstrap.bootstrap_engine import BootstrapEngine
from core.bootstrap.bootstrap_sequence import BootstrapPhase

def test_full_bootstrap_success():
    engine = BootstrapEngine(profile="FULL")
    context = engine.prepare()
    assert context.runtime_state == "prepared"
    assert len(context.initialized_modules) == len(BootstrapPhase)
    assert len(context.failed_modules) == 0

def test_headless_bootstrap_skips_cockpit():
    engine = BootstrapEngine(profile="HEADLESS")
    context = engine.prepare()
    assert context.runtime_state == "prepared"
    assert BootstrapPhase.INITIALIZE_COCKPIT_BRIDGE.name in context.initialized_modules

def test_critical_phase_failure():
    class FailingEngine(BootstrapEngine):
        def _prepare_governance(self):
            raise RuntimeError("Governance failure")

    engine = FailingEngine(profile="FULL")
    context = engine.prepare()
    assert context.runtime_state == "failed"
    assert BootstrapPhase.INITIALIZE_GOVERNANCE.name in context.failed_modules

def test_non_critical_phase_degradation():
    class DegradedEngine(BootstrapEngine):
        def _prepare_federation(self):
            raise RuntimeError("Federation failure")

    engine = DegradedEngine(profile="FULL")
    context = engine.prepare()
    assert context.runtime_state == "prepared"
    assert BootstrapPhase.INITIALIZE_FEDERATION.name in context.failed_modules
    assert BootstrapPhase.INITIALIZE_FEDERATION.name in context.degraded_modules

def test_health_exposure():
    engine = BootstrapEngine(profile="FULL")
    context = engine.prepare()

    from core.storage.storage_manager import storage_manager
    health_file = storage_manager.get_path("temp", "startup_health.json")
    assert health_file.exists()

    import json
    with open(health_file, "r") as f:
        data = json.load(f)
        assert data["status"] == "prepared"
        assert data["profile"] == "FULL"
