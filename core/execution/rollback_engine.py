class RollbackEngine:
    def create_snapshot(self, task_id: str):
        print(f"Snapshot created for {task_id}")

    def rollback(self, task_id: str):
        print(f"Rolling back {task_id}")
