import json
import os
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class CredentialVault:
    def __init__(self):
        self.vault_file = "credentials.enc"
        self.key_file = "vault.key"
        self._key = self._load_or_generate_key()
        self._fernet = Fernet(self._key)
        self._credentials = self._load_vault()

    def _load_or_generate_key(self) -> bytes:
        """Loads the master key from storage or generates a new one."""
        key_data = storage_manager.read_data("governance", self.key_file)
        if key_data:
            return key_data.encode()

        key = Fernet.generate_key()
        storage_manager.save_data("governance", self.key_file, key.decode())
        dgm_logger.info("CredentialVault: Generated new master key.")
        return key

    def _load_vault(self) -> Dict[str, Any]:
        """Loads and decrypts the credential vault."""
        encrypted_data = storage_manager.read_data("governance", self.vault_file)
        if not encrypted_data:
            return {}

        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            dgm_logger.error(f"CredentialVault: Failed to decrypt vault: {e}")
            return {}

    def _save_vault(self):
        """Encrypts and saves the credential vault."""
        try:
            data = json.dumps(self._credentials).encode()
            encrypted_data = self._fernet.encrypt(data)
            storage_manager.save_data("governance", self.vault_file, encrypted_data.decode())
        except Exception as e:
            dgm_logger.error(f"CredentialVault: Failed to save vault: {e}")

    def store_credential(self, provider: str, cred_type: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """Stores a credential for a provider."""
        if provider not in self._credentials:
            self._credentials[provider] = {}

        self._credentials[provider][cred_type] = {
            "value": value,
            "metadata": metadata or {},
            "timestamp": os.path.getmtime(__file__) if os.path.exists(__file__) else 0 # Placeholder for real time
        }
        self._save_vault()
        dgm_logger.info(f"CredentialVault: Stored {cred_type} for '{provider}'")

    def get_credential(self, provider: str, cred_type: str) -> Optional[Any]:
        """Retrieves a credential for a provider."""
        return self._credentials.get(provider, {}).get(cred_type, {}).get("value")

    def delete_credential(self, provider: str, cred_type: str):
        """Deletes a specific credential."""
        if provider in self._credentials and cred_type in self._credentials[provider]:
            del self._credentials[provider][cred_type]
            self._save_vault()
            dgm_logger.info(f"CredentialVault: Deleted {cred_type} for '{provider}'")

    def export_vault(self) -> str:
        """Returns the encrypted vault bundle as a base64 string."""
        encrypted_data = storage_manager.read_data("governance", self.vault_file)
        return encrypted_data or ""

    def import_vault(self, encrypted_bundle: str):
        """Imports an encrypted vault bundle."""
        try:
            # Verify it's decryptable with current key
            self._fernet.decrypt(encrypted_bundle.encode())
            storage_manager.save_data("governance", self.vault_file, encrypted_bundle)
            self._credentials = self._load_vault()
            dgm_logger.info("CredentialVault: Vault imported successfully.")
        except Exception as e:
            dgm_logger.error(f"CredentialVault: Failed to import vault: {e}")

# Singleton
credential_vault = CredentialVault()
