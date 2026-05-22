from queue import Queue

from core.autonomy.models import (
    AutonomousTask,
)


class TaskQueue:

    def __init__(self):

        self.queue = Queue()

    def add_task(
        self,
        task: AutonomousTask,
    ):

        self.queue.put(task)

    def next_task(self):

        if self.queue.empty():
            return None

        return self.queue.get()
