from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget
from PySide6.QtCore import Qt

class OperationalSearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("OPERATIONAL SEMANTIC SEARCH"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for projects, concepts, or failures...")
        layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        layout.addStretch()

    def set_results(self, results: list):
        self.results_list.clear()
        self.results_list.addItems(results)
