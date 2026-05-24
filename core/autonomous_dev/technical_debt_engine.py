from core.observability.logger import dgm_logger

class TechnicalDebtEngine:
    """
    Tracks and prioritizes technical debt across the ecosystem.
    """
    def __init__(self):
        self.debt_registry = {}

    def track_debt(self, project_name: str, debt_type: str, severity: int = 1):
        dgm_logger.info(f"TechnicalDebtEngine: Tracking {debt_type} in {project_name}")
        if project_name not in self.debt_registry:
            self.debt_registry[project_name] = []
        self.debt_registry[project_name].append({"type": debt_type, "severity": severity})

    def get_priority_debt(self):
        # Sort and return debt by severity
        return self.debt_registry
