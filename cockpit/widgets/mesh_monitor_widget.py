from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class MeshMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Mesh Monitor"))
        self.list = QListWidget()
        layout.addWidget(self.list)
