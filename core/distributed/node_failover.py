class NodeFailover:
    def detect_loss(self, node_id):
        print(f"Node loss detected: {node_id}")

    def reassign_tasks(self, node_id):
        print(f"Reassigning tasks from {node_id}")
