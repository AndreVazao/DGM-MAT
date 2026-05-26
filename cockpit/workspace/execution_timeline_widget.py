from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame

class ExecutionTimelineWidget(QWidget):
    """Displays a visual timeline of autonomous execution events."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Execution Timeline"))

        self.timeline_area = QScrollArea()
        self.timeline_container = QFrame()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_area.setWidget(self.timeline_container)
        self.timeline_area.setWidgetResizable(True)
        layout.addWidget(self.timeline_area)

    def add_event(self, event_text: str):
        label = QLabel(event_text)
        self.timeline_layout.addWidget(label)
