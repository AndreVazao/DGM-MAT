from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
)

class AgentWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.agent_list = QListWidget()
        self.agent_list.addItem(
            "repo-agent → healthy"
        )
        layout.addWidget(
            self.agent_list
        )
        self.setLayout(layout)
