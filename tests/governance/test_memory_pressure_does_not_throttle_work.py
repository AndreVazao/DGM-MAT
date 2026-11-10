from core.governance.degradation_controller import DegradationController


def test_memory_pressure_is_observed_but_does_not_degrade_execution():
    controller = DegradationController()

    controller.update_degradation(
        cpu_usage=25.0,
        mem_usage=99.9,
        cpu_threshold=80.0,
        mem_threshold=None,
    )

    assert controller.is_degraded() is False


def test_cpu_safeguard_remains_active_without_ram_threshold():
    controller = DegradationController()

    controller.update_degradation(
        cpu_usage=95.0,
        mem_usage=20.0,
        cpu_threshold=80.0,
        mem_threshold=None,
    )

    assert controller.is_degraded() is True
