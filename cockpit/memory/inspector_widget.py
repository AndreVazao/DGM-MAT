from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QLineEdit, QPushButton
)

class MemoryInspector(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Long-Term Memory Inspector"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search memory semantic concepts...")
        layout.addWidget(self.search_input)

        self.memory_tree = QTreeWidget()
        self.memory_tree.setHeaderLabels(["Type", "Concept", "Importance"])
        layout.addWidget(self.memory_tree)

    def add_memory_node(self, m_type: str, concept: str, score: float):
        item = QTreeWidgetItem([m_type, concept, str(score)])
        self.memory_tree.addTopLevelItem(item)
