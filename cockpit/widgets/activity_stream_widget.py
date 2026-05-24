from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class ActivityStreamWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Continuous Activity Stream")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)

        self.stream_list = QListWidget()
        self.layout.addWidget(self.stream_list)
