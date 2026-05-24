class RepositoryRelationships:
    """
    Tracks dependencies and links between different repositories.
    """
    def __init__(self):
        self.links = []

    def add_link(self, repo_a: str, repo_b: str, relation: str):
        self.links.append({"source": repo_a, "target": repo_b, "relation": relation})
