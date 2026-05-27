import pytest
from core.security.vault import credential_vault

def test_vault_encryption():
    test_key = "sk-test-security-123"
    credential_vault.store_credential("test_provider", "api_key", test_key)
    retrieved = credential_vault.get_credential("test_provider", "api_key")
    assert retrieved == test_key

def test_vault_export_import():
    bundle = credential_vault.export_vault()
    assert len(bundle) > 0

    # Clear and import
    credential_vault._credentials = {}
    credential_vault.import_vault(bundle)
    assert credential_vault.get_credential("test_provider", "api_key") == "sk-test-security-123"
