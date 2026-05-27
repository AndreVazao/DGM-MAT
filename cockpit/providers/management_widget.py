from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QComboBox, QHeaderView,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt
from core.provider_sync.provider_registry import provider_registry
from core.security.vault import credential_vault

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
        """Updates the table with data from the registry."""
        providers = provider_registry.list_providers()
        self.provider_table.setRowCount(0)

        for name in providers:
            p = provider_registry.get_provider(name)
            if not p:
                continue

            row = self.provider_table.rowCount()
            self.provider_table.insertRow(row)

            self.provider_table.setItem(row, 0, QTableWidgetItem(name))

            status_item = QTableWidgetItem(p.health_metrics["status"])
            if p.health_metrics["status"] == "ok":
                status_item.setForeground(Qt.green)
            elif p.health_metrics["status"] == "cooldown":
                status_item.setForeground(Qt.red)
            self.provider_table.setItem(row, 1, status_item)

            self.provider_table.setItem(row, 2, QTableWidgetItem(f"{p.get_avg_latency():.0f}ms"))
            self.provider_table.setItem(row, 3, QTableWidgetItem(str(p.health_metrics["quota_used"])))

            caps = ", ".join([f"{k}:{v}" for k, v in p.capabilities.items() if isinstance(v, (int, float))])
            self.provider_table.setItem(row, 4, QTableWidgetItem(caps))

            cooldown = "No"
            if p.health_metrics["status"] == "cooldown":
                import time
                remaining = max(0, int(p.health_metrics["cooldown_until"] - time.time()))
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
