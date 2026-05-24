from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class TechnicalDebtWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Technical Debt Dashboard"))
