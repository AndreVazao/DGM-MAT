from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PySide6.QtCore import Qt

class KnowledgeGraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("SEMANTIC KNOWLEDGE GRAPH"))

        self.graph_view = QTextEdit()
        self.graph_view.setReadOnly(True)
        self.graph_view.setPlaceholderText("Knowledge graph visualization placeholder...")
        layout.addWidget(self.graph_view)

        self.refresh_btn = QPushButton("Refresh Graph")
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

    def update_graph_data(self, summary: str):
        self.graph_view.setText(summary)
