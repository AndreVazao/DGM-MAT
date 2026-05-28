import os
import json
from datetime import datetime
from pathlib import Path
from core.storage.storage_manager import storage_manager
from core.federation.ecosystem_registry import EcosystemRegistry
from core.kernel.cognitive_kernel import CognitiveKernel
from core.strategy.strategic_memory import StrategicMemory

def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def run_phase_finalization():
    print("Starting Phase Finalization Pipeline...")

    registry = EcosystemRegistry()
    kernel = CognitiveKernel()
    kernel.boot()
    strategy_memory = StrategicMemory(storage_manager)

    # 1. Snapshot Ecosystem Topology
    ecosystems = registry.get_ecosystems()
    topology_snapshot = {
        "timestamp": datetime.now().isoformat(),
        "ecosystems": [e.model_dump() for e in ecosystems],
        "topology_type": "hub-and-spoke",
        "maturity_level": "Phase 21/22"
    }

    storage_manager.save_data("topology", f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", json.dumps(topology_snapshot, indent=2, default=datetime_serializer))
    print("Ecosystem topology snapshotted.")

    # 2. Update Strategic Memory
    decision = {
        "id": f"phase_finalization_{datetime.now().strftime('%Y%m%d')}",
        "type": "ARCHITECTURAL_CHECKPOINT",
        "content": "Updated ecosystem registry with reserved repositories and specialization domains.",
        "status": "COMPLETED"
    }
    strategy_memory.store_decision(decision)
    print("Strategic memory updated.")

    # 3. Generate Evolution Summary
    evolution_summary = {
        "phase": "Phase 21/22",
        "completion_date": datetime.now().isoformat(),
        "governance_maturity": "High",
        "cognition_maturity": "Federation-Aware",
        "orchestration_maturity": "Modular",
        "strategic_direction": "Modular Federated AI Operating Civilization"
    }

    storage_manager.save_data("evolution_memory", "current_summary.json", json.dumps(evolution_summary, indent=2))
    print("Evolution summary generated.")

    # 4. Create Architecture Checkpoint in Persistent Memory
    checkpoint_path = storage_manager.get_path("memory", f"architecture_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w") as f:
        json.dump(topology_snapshot, f, indent=2, default=datetime_serializer)
    print(f"Architecture checkpoint created at {checkpoint_path}")

    print("Phase Finalization Pipeline COMPLETED.")

if __name__ == "__main__":
    run_phase_finalization()
