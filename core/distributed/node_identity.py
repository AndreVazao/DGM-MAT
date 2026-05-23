import uuid

class NodeIdentity:
    def __init__(self):
        self.node_id = str(uuid.uuid4())
