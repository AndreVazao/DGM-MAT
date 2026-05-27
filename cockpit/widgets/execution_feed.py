from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from PySide6.QtCore import Slot
from datetime import datetime

class ExecutionFeed(QWidget):
    """
    Displays real-time feed of autonomous execution tasks.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Autonomous Execution Feed"))
        self.feed_list = QListWidget()
        self.feed_list.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: monospace;")
        layout.addWidget(self.feed_list)

    @Slot(dict)
    def add_execution_event(self, data: dict):
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_type = data.get("event", "INFO")
        message = data.get("message", "")
        task_id = data.get("task_id", "N/A")

        entry = f"[{timestamp}] {event_type} | Task: {task_id} | {message}"
        self.feed_list.insertItem(0, entry)

        # Keep list reasonably short
        if self.feed_list.count() > 500:
            self.feed_list.takeItem(self.feed_list.count() - 1)
