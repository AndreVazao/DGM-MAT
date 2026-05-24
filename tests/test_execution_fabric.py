from core.execution_fabric.execution_state_machine import ExecutionStateMachine, ExecutionStatus

def test_execution_state_machine():
    esm = ExecutionStateMachine("test-123")
    assert esm.status == ExecutionStatus.PENDING
    esm.transition_to(ExecutionStatus.VALIDATING)
    assert esm.status == ExecutionStatus.VALIDATING
    assert len(esm.history) == 1
    assert esm.history[0]["to"] == ExecutionStatus.VALIDATING

def test_specialization_registry():
    from core.agents.specialization.specialization_registry import SpecializationRegistry
    registry = SpecializationRegistry()
    assert "repository" in registry.registry
    assert "analysis" in registry.get_agents_by_role("repository")
