from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QComboBox, QHeaderView,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt
import requests
from pathlib import Path
from core.provider_sync.provider_registry import provider_registry
from core.security.vault import credential_vault
from shared.config.settings import API_HOST, API_PORT

class ProviderManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGM-MAT Provider Orchestration")
        layout = QVBoxLayout(self)

        header = QLabel("Dynamic Provider Orchestration Layer")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        self.provider_table = QTableWidget(0, 6)
        self.provider_table.setHorizontalHeaderLabels([
            "Provider", "Status", "Latency", "Quota", "Capabilities", "Cooldown"
        ])
        self.provider_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.provider_table)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Status")
        self.set_key_btn = QPushButton("Set API Key")
        self.test_btn = QPushButton("Test Fallback")
        self.recovery_btn = QPushButton("Browser Recovery")

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.set_key_btn)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.recovery_btn)
        layout.addLayout(btn_layout)

        # Connect signals
        self.refresh_btn.clicked.connect(self.refresh_providers)
        self.set_key_btn.clicked.connect(self.prompt_set_key)

        self.refresh_providers()

    def refresh_providers(self):
        """Updates the table with data from the runtime API, then local registry as fallback."""
        self.provider_table.setRowCount(0)
        providers = self._load_backend_providers()

        if providers:
            for provider in providers:
                self._add_provider_row(provider)
            return

        for name in provider_registry.list_providers():
            p = provider_registry.get_provider(name)
            if p:
                self._add_provider_row({
                    "name": name,
                    "status": p.health_metrics.get("status", "unknown"),
                    "latency": p.get_avg_latency(),
                    "quota_used": p.health_metrics.get("quota_used", 0),
                    "capabilities": p.capabilities,
                    "cooldown_until": p.health_metrics.get("cooldown_until", 0),
                    "loaded": True,
                    "installed": True,
                })

        if self.provider_table.rowCount() == 0:
            for name in self._load_installed_provider_names():
                self._add_provider_row({
                    "name": name,
                    "status": "installed",
                    "latency": 0,
                    "quota_used": 0,
                    "capabilities": {},
                    "installed": True,
                    "loaded": False,
                })

    def _load_backend_providers(self):
        try:
            response = requests.get(f"http://{API_HOST}:{API_PORT}/runtime/providers", timeout=1)
            if response.status_code == 200:
                return response.json().get("providers", [])
        except Exception:
            return []
        return []

    def _load_installed_provider_names(self):
        providers_dir = Path(__file__).resolve().parents[2] / "core" / "providers"
        if not providers_dir.exists():
            return []
        names = []
        for entry in providers_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("__"):
                if (entry / f"{entry.name}_provider.py").exists():
                    names.append(entry.name)
        return sorted(names)

    def _add_provider_row(self, provider: dict):
        name = provider.get("name", "unknown")
        status = provider.get("status", "unknown")
        row = self.provider_table.rowCount()
        self.provider_table.insertRow(row)

        self.provider_table.setItem(row, 0, QTableWidgetItem(name))

        status_item = QTableWidgetItem(status)
        if status in ["ok", "active", "deferred", "installed"]:
            status_item.setForeground(Qt.green)
        elif status == "cooldown":
            status_item.setForeground(Qt.red)
        self.provider_table.setItem(row, 1, status_item)

        latency = provider.get("latency", 0) or 0
        self.provider_table.setItem(row, 2, QTableWidgetItem(f"{float(latency):.0f}ms"))
        self.provider_table.setItem(row, 3, QTableWidgetItem(str(provider.get("quota_used", 0))))

        capabilities = provider.get("capabilities", {}) or {}
        caps = ", ".join([f"{k}:{v}" for k, v in capabilities.items() if isinstance(v, (int, float))])
        if not caps:
            caps = "installed" if provider.get("installed") else "not installed"
        self.provider_table.setItem(row, 4, QTableWidgetItem(caps))

        cooldown = "No"
        if status == "cooldown":
            import time
            remaining = max(0, int((provider.get("cooldown_until") or 0) - time.time()))
            cooldown = f"{remaining}s"
        self.provider_table.setItem(row, 5, QTableWidgetItem(cooldown))

    def prompt_set_key(self):
        """Prompts the user to set an API key for a provider."""
        providers = provider_registry.list_providers()
        if not providers:
            QMessageBox.warning(self, "Error", "No providers registered.")
            return

        provider_name, ok = QComboBox().currentText(), False # Simplification
        # Real implementation would use a proper dialog
        provider_name, ok = QInputDialog.getItem(self, "Select Provider", "Provider:", providers, 0, False)
        if ok and provider_name:
            key, ok = QInputDialog.getText(self, "Set API Key", f"Enter API Key for {provider_name}:", QLineEdit.Password)
            if ok and key:
                credential_vault.store_credential(provider_name, "api_key", key)
                QMessageBox.information(self, "Success", f"API Key stored for {provider_name}")
                self.refresh_providers()
