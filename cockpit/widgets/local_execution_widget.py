from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LocalExecutionWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Local Execution Console"))
