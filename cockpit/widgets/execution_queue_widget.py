from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class ExecutionQueueWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Execution Queue"))
        self.list = QListWidget()
        layout.addWidget(self.list)
