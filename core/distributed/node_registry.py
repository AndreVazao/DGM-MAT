class NodeRegistry:
    def __init__(self):
        self.nodes = {}

    def register_node(self, node_id, node_info):
        self.nodes[node_id] = node_info
