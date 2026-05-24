from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class ExecutionFeed(QWidget):
    """
    Displays real-time feed of autonomous execution tasks.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Autonomous Execution Feed"))
        self.feed_list = QListWidget()
        layout.addWidget(self.feed_list)

    def add_event(self, event_text: str):
        self.feed_list.addItem(event_text)
