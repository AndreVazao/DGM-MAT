from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.runtime_label = QLabel(
            "Runtime: RUNNING"
        )
        self.agents_label = QLabel(
            "Agents: 1"
        )
        self.events_label = QLabel(
            "Events: 0"
        )
        card = QFrame()
        card_layout = QVBoxLayout()
        card_layout.addWidget(
            self.runtime_label
        )
        card_layout.addWidget(
            self.agents_label
        )
        card_layout.addWidget(
            self.events_label
        )
        card.setLayout(card_layout)
        layout.addWidget(card)
        self.setLayout(layout)
