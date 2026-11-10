from types import SimpleNamespace

from core.runtime import runtime_profile


def test_low_memory_hardware_does_not_disable_runtime_capabilities(monkeypatch):
    monkeypatch.setattr(
        runtime_profile,
        "psutil",
        SimpleNamespace(virtual_memory=lambda: SimpleNamespace(
            total=int(2.96 * 1024 ** 3),
            percent=91.0,
        )),
    )

    profile = runtime_profile._build_runtime_profile()

    assert profile.low_memory is True
    assert profile.name == "low_memory"
    assert profile.lazy_load_knowledge is False
    assert profile.lazy_provider_health is False
    assert profile.enable_startup_provider_scan is True
    assert profile.enable_startup_autonomy_scan is True
