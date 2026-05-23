from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

class GovernanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("GOVERNANCE MONITOR"))

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        layout.addWidget(QLabel("CPU Usage:"))
        layout.addWidget(self.cpu_bar)

        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        layout.addWidget(QLabel("Memory Usage:"))
        layout.addWidget(self.mem_bar)

        self.status_label = QLabel("Status: NOMINAL")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def update_metrics(self, cpu, mem, is_degraded=False):
        self.cpu_bar.setValue(int(cpu))
        self.mem_bar.setValue(int(mem))

        if is_degraded:
            self.status_label.setText("Status: DEGRADED")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setText("Status: NOMINAL")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
