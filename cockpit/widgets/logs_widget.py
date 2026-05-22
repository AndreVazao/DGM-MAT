from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
)

class LogsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.append(
            "[SYSTEM] Cockpit initialized"
        )
        layout.addWidget(self.logs)
        self.setLayout(layout)

    def append_log(self, message: str):
        self.logs.append(message)
