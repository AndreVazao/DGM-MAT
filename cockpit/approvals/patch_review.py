from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class PatchReviewPanel(QWidget):
    """
    Enhanced Patch Review System with risk indicators and mandatory approval.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>PATCH REVIEW SYSTEM</b>"), alignment=Qt.AlignCenter)

        self.risk_panel = QFrame()
        self.risk_panel.setFrameShape(QFrame.StyledPanel)
        risk_layout = QHBoxLayout(self.risk_panel)
        self.risk_label = QLabel("RISK LEVEL: UNKNOWN")
        self.risk_score_label = QLabel("SCORE: 0.0")
        risk_layout.addWidget(self.risk_label)
        risk_layout.addWidget(self.risk_score_label)
        layout.addWidget(self.risk_panel)

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFontFamily("Courier")
        self.diff_view.setPlaceholderText("Select a patch to review...")
        layout.addWidget(self.diff_view)

        self.warnings_label = QLabel("")
        self.warnings_label.setStyleSheet("color: orange;")
        self.warnings_label.setWordWrap(True)
        layout.addWidget(self.warnings_label)

        btn_layout = QHBoxLayout()
        self.approve_btn = QPushButton("APPROVE & APPLY")
        self.approve_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")

        self.reject_btn = QPushButton("REJECT")
        self.reject_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")

        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.reject_btn)
        layout.addLayout(btn_layout)

    def display_patch(self, diff_text: str, risk_data: dict):
        self.diff_view.setPlainText(diff_text)
        level = risk_data.get("level", "UNKNOWN")
        score = risk_data.get("score", 0.0)
        self.risk_label.setText(f"RISK LEVEL: {level}")
        self.risk_score_label.setText(f"SCORE: {score:.2f}")

        warnings = risk_data.get("warnings", [])
        self.warnings_label.setText("\n".join(warnings) if warnings else "")

        color_map = {"CRITICAL": "#ffcccc", "HIGH": "#fff3cd", "MEDIUM": "#d4edda", "LOW": "#d4edda"}
        self.risk_panel.setStyleSheet(f"background-color: {color_map.get(level, '#f8f9fa')};")
