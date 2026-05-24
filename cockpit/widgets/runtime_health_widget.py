from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

class RuntimeHealthWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Runtime Health Monitor")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.health_bar = QProgressBar()
        self.health_bar.setValue(100)
        self.layout.addWidget(self.health_bar)
