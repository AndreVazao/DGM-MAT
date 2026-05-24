from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class EcosystemGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("External Ecosystem Graph")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.graph_placeholder = QLabel("Graph Visualization (NetworkX/Qt)")
        self.graph_placeholder.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.graph_placeholder)
