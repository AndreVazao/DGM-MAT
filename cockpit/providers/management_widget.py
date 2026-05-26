from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QComboBox
)

class ProviderManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Multi-Provider Management"))

        self.provider_table = QTableWidget(0, 4)
        self.provider_table.setHorizontalHeaderLabels(["Provider", "Status", "Capabilities", "Health"])
        layout.addWidget(self.provider_table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Provider")
        self.login_btn = QPushButton("Login")
        self.sync_btn = QPushButton("Sync Conversations")
        self.test_btn = QPushButton("Test Connection")

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.sync_btn)
        btn_layout.addWidget(self.test_btn)
        layout.addLayout(btn_layout)

    def update_provider_list(self, providers: list):
        self.provider_table.setRowCount(0)
        for p in providers:
            row = self.provider_table.rowCount()
            self.provider_table.insertRow(row)
            self.provider_table.setItem(row, 0, QTableWidgetItem(p['name']))
            self.provider_table.setItem(row, 1, QTableWidgetItem(p['status']))
            self.provider_table.setItem(row, 2, QTableWidgetItem(", ".join(p['capabilities'])))
            self.provider_table.setItem(row, 3, QTableWidgetItem(str(p['health'])))
