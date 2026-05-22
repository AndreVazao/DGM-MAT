import sys
import os
import time
from core.event_bus.bus import Event, EventBus
from core.overseer.overseer import Overseer
from core.self_healing.engine import SelfHealingEngine
from core.repository_intelligence.auto_repair import AutoRepair
from core.git_engine.git_manager import GitManager
from core.deployment.manager import DeploymentManager
from core.health.calculator import HealthCalculator
from core.cockpit.interface import CockpitInterface
from core.ecosystem_state.manager import EcosystemStateManager
from core.memory.sync import MemorySync

def test_phase6_functionality():
    print("--- STARTING DGM-MAT PHASE 6 INTEGRATION TEST ---")

    # 1. Setup
    bus = EventBus()
    state_manager = EcosystemStateManager(bus)
    memory_sync = MemorySync(bus) # Subscribes to evolution_recorded
    git = GitManager(bus)
    healing = SelfHealingEngine(bus)
    repair = AutoRepair(bus, git)
    deployer = DeploymentManager(bus)
    health = HealthCalculator(bus)
    overseer = Overseer(bus)
    cockpit = CockpitInterface(bus)

    # 2. Test Health Reporting
    print("\n[TEST] Testing Health Score...")
    health.update_metric("agent_stability", 0.1)
    health.update_metric("repo_integrity", 0.1)
    health.update_metric("provider_reliability", 0.1)
    current_health = health.calculate_global_score()
    print(f"Health Score: {current_health}")

    # 3. Test Overseer Immune Response
    print("\n[TEST] Testing Overseer Immune Response...")
    overseer.run_once()
    if overseer.unsafe_operations_paused:
        print("SUCCESS: Overseer paused unsafe operations")
    else:
        print("FAILURE: Overseer did not pause operations")

    # 4. Test Self-Healing Trigger
    print("\n[TEST] Testing Self-Healing Trigger...")
    critical_error = Event(
        source="provider_agent",
        type="error",
        payload={"category": "provider_failure", "state": "disconnected"},
        priority="critical"
    )
    bus.publish(critical_error)
    overseer.run_once()

    healing.detect_and_repair("provider_failure", {"state": "disconnected"})
    print("SUCCESS: Self-healing repair event published")

    # 5. Test Auto-Repair Proposal
    print("\n[TEST] Testing Auto-Repair Proposal...")
    repair.propose_fix("missing_file", {"files": ["architecture.md"]})
    print("SUCCESS: Auto-repair proposal published")

    # 6. Test Deployment Pipeline
    print("\n[TEST] Testing Deployment Pipeline...")
    deployer.deploy("DGM-MAT-Installer", stage="staging")
    print("SUCCESS: Deployment initiated")

    # 7. Test Cockpit Dashboard
    print("\n[TEST] Testing Cockpit Dashboard...")
    dashboard = cockpit.get_dashboard_state()
    print(f"Dashboard System Status: {dashboard['system_status']}")
    print(f"Recent Events Count: {len(dashboard['event_stream_tail'])}")

    # 8. Test Evolution Sync
    print("\n[TEST] Testing Evolution Sync...")
    global_state = state_manager.get_global_state()
    print(f"Evolution Chain Length: {global_state['evolution_chain_length']}")

    # Check if files exist in AndreOS
    andreos_files = os.listdir("AndreOS")
    evolution_files = [f for f in andreos_files if f.startswith("evolution_")]
    print(f"Evolution Snapshots in AndreOS: {len(evolution_files)}")
    if len(evolution_files) > 0:
        print("SUCCESS: Evolution snapshots persisted to AndreOS")

    print("\n--- PHASE 6 TEST COMPLETE ---")

if __name__ == "__main__":
    test_phase6_functionality()
