from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class SelfImprovementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Self-Improvement Timeline")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.timeline = QTextEdit()
        self.timeline.setReadOnly(True)
        self.layout.addWidget(self.timeline)
