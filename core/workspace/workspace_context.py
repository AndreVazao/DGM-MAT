class WorkspaceContext:
    """
    Maintains the active cognitive context of the workspace.
    """
    def __init__(self):
        self.active_project = None
        self.recent_files = []
        self.current_goals = []

    def set_active_project(self, project_name: str):
        self.active_project = project_name
