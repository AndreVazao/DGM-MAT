from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout

class PatchReviewUI(QWidget):
    """Specialized UI for reviewing and approving autonomous patches."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Patch Review & Validation"))

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        layout.addWidget(self.diff_view)

        self.safety_report = QLabel("Safety Status: PENDING")
        layout.addWidget(self.safety_report)

        btn_layout = QHBoxLayout()
        self.approve_btn = QPushButton("Approve & Promote")
        self.reject_btn = QPushButton("Reject")
        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.reject_btn)
        layout.addLayout(btn_layout)

    def set_patch(self, diff: str, safety_score: int):
        self.diff_view.setPlainText(diff)
        self.safety_report.setText(f"Safety Status: {safety_score}% SAFE")
