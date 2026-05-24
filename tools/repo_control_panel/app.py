import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QLabel, QMessageBox,
    QComboBox
)
from PySide6.QtCore import Qt

# Ensure local imports work if running from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools.repo_control_panel.repo_manager import RepoManager
from tools.repo_control_panel.github_client import GitHubClient

class RepoPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.manager = RepoManager()
        self.github = GitHubClient()

        self.setWindowTitle("DGM-MAT Repo Control Panel")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.layout = QVBoxLayout()

        self.header = QLabel("DGM-MAT Ecosystem Manager")
        self.header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.header)

        # Input Section
        input_layout = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Repo Name (e.g., DGM-MAT-X)")

        self.role_combo = QComboBox()
        self.role_combo.addItems(["core", "infra", "product", "data", "agents", "experimental"])

        input_layout.addWidget(QLabel("Name:"))
        input_layout.addWidget(self.input_name)
        input_layout.addWidget(QLabel("Role:"))
        input_layout.addWidget(self.role_combo)
        self.layout.addLayout(input_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Register Locally")
        self.create_btn = QPushButton("Create on GitHub")
        self.remove_btn = QPushButton("Deprecate")
        self.refresh_btn = QPushButton("Refresh List")

        self.add_btn.clicked.connect(self.add_repo)
        self.create_btn.clicked.connect(self.create_repo)
        self.remove_btn.clicked.connect(self.deprecate_repo)
        self.refresh_btn.clicked.connect(self.refresh)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(btn_layout)

        # List Section
        self.list_widget = QListWidget()
        self.layout.addWidget(QLabel("Registered Ecosystem Nodes:"))
        self.layout.addWidget(self.list_widget)

        self.setLayout(self.layout)
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        self.manager = RepoManager() # Reload from file
        repos = self.manager.repos
        for name, data in repos.items():
            status = data.get("status", "unknown")
            role = data.get("role", "unknown")
            self.list_widget.addItem(f"[{role.upper()}] {name} - Status: {status}")

    def add_repo(self):
        name = self.input_name.text().strip()
        role = self.role_combo.currentText()
        if name:
            self.manager.add_repo(name, role=role)
            self.refresh()
            self.input_name.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a repo name.")

    def create_repo(self):
        name = self.input_name.text().strip()
        role = self.role_combo.currentText()
        if not name:
            QMessageBox.warning(self, "Input Error", "Please enter a repo name.")
            return

        reply = QMessageBox.question(self, "Confirm Creation",
                                   f"Create '{name}' on GitHub?",
                                   QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            code, resp = self.github.create_repo(name)
            if code == 201:
                self.manager.add_repo(name, status="active", role=role)
                QMessageBox.information(self, "Success", f"Repo '{name}' created successfully!")
            else:
                QMessageBox.error(self, "GitHub Error", f"Failed to create repo: {resp.get('message', 'Unknown error')}")
            self.refresh()

    def deprecate_repo(self):
        selected = self.list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "Selection Error", "Please select a repo from the list.")
            return

        # Extract name from string "[ROLE] NAME - Status: STATUS"
        text = selected.text()
        name = text.split("] ")[1].split(" - ")[0]

        self.manager.remove_repo(name)
        self.refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RepoPanel()
    window.show()
    sys.exit(app.exec())
