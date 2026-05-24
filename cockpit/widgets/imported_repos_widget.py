from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

class ImportedReposWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Imported Repositories")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.repo_list = QListWidget()
        self.layout.addWidget(self.repo_list)

    def update_repos(self, repos: list):
        self.repo_list.clear()
        for repo in repos:
            item = QListWidgetItem(repo)
            self.repo_list.addItem(item)
