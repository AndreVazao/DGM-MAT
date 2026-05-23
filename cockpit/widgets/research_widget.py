from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

class ResearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Autonomous Research Lab & Sandbox")
        self.layout.addWidget(self.label)

        self.experiment_progress = QProgressBar()
        self.layout.addWidget(self.experiment_progress)

        self.benchmark_panel = QLabel("Provider Benchmarks: ChatGPT (95%), Claude (92%)")
        self.layout.addWidget(self.benchmark_panel)
