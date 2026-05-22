from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
)

class EventStreamWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.events = QListWidget()
        layout.addWidget(self.events)
        self.setLayout(layout)

    def add_event(self, event: str):
        self.events.addItem(event)
