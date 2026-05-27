from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QProgressBar, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Slot

class OperationalDashboard(QWidget):
    """
    Real-time operational dashboard for DGM-MAT.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Operational Dashboard")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.title)

        # Runtime Status
        self.status_label = QLabel("System Status: DISCONNECTED")
        self.status_label.setStyleSheet("color: orange;")
        self.layout.addWidget(self.status_label)

        # Provider Health
        self.layout.addWidget(QLabel("Provider Health:"))
        self.provider_list = QListWidget()
        self.layout.addWidget(self.provider_list)

        # Resource Usage (Placeholder for now)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.layout.addWidget(self.cpu_bar)

        self.mem_bar = QProgressBar()
        self.mem_bar.setFormat("Memory: %p%")
        self.layout.addWidget(self.mem_bar)

    @Slot(dict)
    def update_status(self, data: dict):
        status = data.get("status", "unknown").upper()
        self.status_label.setText(f"System Status: {status}")
        if status == "RUNNING":
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setStyleSheet("color: red;")

        if "cpu" in data: self.cpu_bar.setValue(int(data["cpu"]))
        if "memory" in data: self.mem_bar.setValue(int(data["memory"]))

    @Slot(dict)
    def update_provider_health(self, data: dict):
        provider = data.get("name")
        status = data.get("status", "unknown")
        latency = data.get("latency", "N/A")

        item_text = f"{provider}: {status} (Latency: {latency}ms)"

        # Check if already in list
        items = self.provider_list.findItems(f"{provider}:", Qt.MatchStartsWith)
        if items:
            items[0].setText(item_text)
        else:
            self.provider_list.addItem(item_text)
