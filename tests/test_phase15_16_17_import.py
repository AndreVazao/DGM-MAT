import pytest

def test_imports():
    import core.execution.worktree_manager
    import core.execution.branch_manager
    import core.execution.execution_engine
    import core.execution.execution_context
    import core.execution.approval_manager
    import core.execution.repair_loop
    import core.execution.merge_guard
    import core.execution.rollback_engine
    import core.execution.execution_models

    import core.labs.lab_scanner
    import core.labs.pattern_extractor
    import core.labs.architecture_analyzer
    import core.labs.orchestration_detector
    import core.labs.lab_memory

    import core.distributed.node_registry
    import core.distributed.node_manager
    import core.distributed.node_identity
    import core.distributed.node_heartbeat
    import core.distributed.node_failover
    import core.distributed.node_sync
    import core.distributed.distributed_memory
    import core.distributed.node_state
    import core.distributed.node_capabilities
    import core.distributed.mesh_models

    import core.learning.learning_engine
    import core.learning.execution_learning
    import core.learning.provider_learning
    import core.learning.failure_learning
    import core.learning.learning_models
    import core.learning.learning_snapshot
    import core.learning.prompt_learning
    import core.learning.orchestration_learning
    import core.learning.specialization_engine
    import core.learning.pattern_memory
    import core.learning.adaptive_routing
    import core.learning.capability_evolution

    print("All modules imported successfully")
