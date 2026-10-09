# Path: C:\ProgramasGodMode\DGM-MAT\tests\provider_sync\test_sync.py

from core.operator.provider_sync import ProviderSync


def test_legacy_provider_sync_fails_closed_without_verified_implementation():
    assert ProviderSync().sync_providers() is False
