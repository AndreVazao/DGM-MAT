from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Slot
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.agent_widget import AgentWidget
from cockpit.widgets.knowledge_feed_widget import KnowledgeFeedWidget

class OperationalDashboard(QWidget):
    """
    Main operational dashboard (Mission Control) for DGM-MAT.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.title = QLabel("MISSION CONTROL")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)

        content = QHBoxLayout()

        # LEFT: Missions & Feed
        left = QVBoxLayout()
        self.mission_widget = MissionWidget()
        self.knowledge_feed = KnowledgeFeedWidget()
        left.addWidget(self.mission_widget, 1)
        left.addWidget(self.knowledge_feed, 1)

        # RIGHT: Agents & Resources
        right = QVBoxLayout()
        self.agent_widget = AgentWidget()
        right.addWidget(self.agent_widget, 2)

        res_frame = QFrame()
        res_frame.setFrameShape(QFrame.StyledPanel)
        res_layout = QVBoxLayout(res_frame)
        res_layout.addWidget(QLabel("<b>RESOURCE PULSE</b>"))
        self.cpu_bar = QProgressBar()
        self.mem_bar = QProgressBar()
        res_layout.addWidget(self.cpu_bar)
        res_layout.addWidget(self.mem_bar)
        right.addWidget(res_frame, 1)

        content.addLayout(left, 2)
        content.addLayout(right, 1)
        self.layout.addLayout(content)

    @Slot(dict)
    def update_resources(self, data: dict):
        if "cpu" in data: self.cpu_bar.setValue(int(data["cpu"]))
        if "memory" in data: self.mem_bar.setValue(int(data["memory"]))
