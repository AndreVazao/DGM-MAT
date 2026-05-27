from PySide6.QtWidgets import QApplication
from cockpit.widgets.mission_widget import MissionWidget
from cockpit.widgets.knowledge_feed_widget import KnowledgeFeedWidget
from cockpit.approvals.patch_review import PatchReviewPanel
from cockpit.widgets.operational_dashboard import OperationalDashboard
import sys

app = QApplication(sys.argv)

def verify():
    try:
        m = MissionWidget()
        k = KnowledgeFeedWidget()
        p = PatchReviewPanel()
        d = OperationalDashboard()
        print("Widget instantiation successful")
        return True
    except Exception as e:
        print(f"Widget instantiation failed: {e}")
        return False

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
