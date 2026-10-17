class MergeGuard:
    @staticmethod
    def can_merge(branch: str):
        if branch in ["main", "master", "production"]:
            return False
        return True
