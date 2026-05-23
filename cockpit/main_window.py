from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)
from cockpit.widgets.dashboard_widget import (
    DashboardWidget,
)
from cockpit.widgets.logs_widget import (
    LogsWidget,
)
from cockpit.widgets.event_stream_widget import (
    EventStreamWidget,
)
from cockpit.widgets.agent_widget import (
    AgentWidget,
)
from cockpit.widgets.execution_queue_widget import (
    ExecutionQueueWidget,
)
from cockpit.widgets.mesh_monitor_widget import (
    MeshMonitorWidget,
)
from cockpit.widgets.learning_dashboard_widget import (
    LearningDashboardWidget,
)
from cockpit.realtime_client import (
    RealtimeClient,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "DGM-MAT Cockpit"
        )
        self.resize(1400, 900)
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.dashboard = DashboardWidget()
        self.logs = LogsWidget()
        self.events = EventStreamWidget()
        self.agents = AgentWidget()
        self.execution_queue = ExecutionQueueWidget()
        self.mesh_monitor = MeshMonitorWidget()
        self.learning_dashboard = LearningDashboardWidget()

        left_layout.addWidget(
            self.dashboard
        )
        left_layout.addWidget(
            self.agents
        )
        left_layout.addWidget(
            self.mesh_monitor
        )

        right_layout.addWidget(
            self.events
        )
        right_layout.addWidget(
            self.execution_queue
        )
        right_layout.addWidget(
            self.learning_dashboard
        )
        right_layout.addWidget(
            self.logs
        )

        root_layout.addLayout(
            left_layout,
            1,
        )
        root_layout.addLayout(
            right_layout,
            2,
        )
        central.setLayout(root_layout)
        self.client = RealtimeClient(
            self.handle_message
        )
        QTimer.singleShot(
            1000,
            self.client.start,
        )

    def handle_message(
        self,
        message: dict,
    ):
        event_type = message.get(
            "event_type",
            "unknown",
        )
        source = message.get(
            "source",
            "unknown",
        )
        self.events.add_event(
            f"{event_type} ← {source}"
        )
        self.logs.append_log(
            f"[EVENT] {event_type}"
        )
