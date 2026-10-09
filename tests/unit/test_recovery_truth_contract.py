from core.recovery.provider_recovery import ProviderRecovery
from core.recovery.runtime_recovery import RuntimeRecovery
from core.recovery.repair_chain import RepairChain
from core.recovery.recovery_engine import RecoveryEngine


def test_provider_recovery_does_not_claim_success_without_implementation():
    assert ProviderRecovery().recover_provider("test-provider") is False


def test_runtime_recovery_does_not_claim_success_without_implementation():
    assert RuntimeRecovery().recover() is False


def test_empty_repair_chain_is_not_success():
    assert RepairChain().execute() is False


def test_repair_chain_fails_when_any_step_fails():
    chain = RepairChain()
    chain.add_step(lambda: True)
    chain.add_step(lambda: False)
    chain.add_step(lambda: True)

    assert chain.execute() is False


def test_repair_chain_fails_when_step_raises():
    def broken_step():
        raise RuntimeError("synthetic recovery failure")

    chain = RepairChain()
    chain.add_step(broken_step)

    assert chain.execute() is False


def test_unknown_recovery_path_cannot_succeed_with_empty_chain():
    engine = RecoveryEngine()

    assert engine._execute_chain("memory_corruption") is False


def test_provider_crash_is_recorded_as_failed_until_recovery_exists():
    class MemoryRecorder:
        def __init__(self):
            self.records = []

        def record_recovery(self, crash_type, status):
            self.records.append((crash_type, status))

    engine = RecoveryEngine()
    recorder = MemoryRecorder()
    engine.memory = recorder

    result = engine.handle_crash({"message": "provider authentication failed"})

    assert result is False
    assert recorder.records == [("provider_crash", "failed")]
