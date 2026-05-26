from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QLabel, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

class ApprovalQueueWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pending Approvals Queue"))

        self.queue_list = QListWidget()
        layout.addWidget(self.queue_list)

        btn_layout = QHBoxLayout()
        self.approve_btn = QPushButton("Approve Selected")
        self.reject_btn = QPushButton("Reject Selected")

        btn_layout.addWidget(self.approve_btn)
        btn_layout.addWidget(self.reject_btn)
        layout.addLayout(btn_layout)

    def add_item(self, request_id: str, description: str):
        self.queue_list.addItem(f"[{request_id}] {description}")
