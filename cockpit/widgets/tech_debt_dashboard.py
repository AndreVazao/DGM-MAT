from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem

class TechDebtDashboard(QWidget):
    """
    Dashboard for tracking and prioritizing technical debt.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Technical Debt Dashboard"))
        self.debt_table = QTableWidget(0, 3)
        self.debt_table.setHorizontalHeaderLabels(["Project", "Type", "Severity"])
        layout.addWidget(self.debt_table)

    def update_debt(self, project, debt_type, severity):
        row = self.debt_table.rowCount()
        self.debt_table.insertRow(row)
        self.debt_table.setItem(row, 0, QTableWidgetItem(project))
        self.debt_table.setItem(row, 1, QTableWidgetItem(debt_type))
        self.debt_table.setItem(row, 2, QTableWidgetItem(str(severity)))
