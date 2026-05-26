from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout
)

class PatchReviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Patch Review"))

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setPlaceholderText("Select a patch to review...")
        layout.addWidget(self.diff_view)

        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Patch")
        self.discard_btn = QPushButton("Discard")

        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.discard_btn)
        layout.addLayout(btn_layout)

    def set_diff(self, diff_text: str):
        self.diff_view.setPlainText(diff_text)
