import queue

class LocalTaskQueue:
    """
    Manages a queue of tasks for local execution.
    """
    def __init__(self):
        self.queue = queue.Queue()

    def add_task(self, task):
        self.queue.put(task)

    def get_next_task(self):
        return self.queue.get() if not self.queue.empty() else None
