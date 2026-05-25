class PriorityRouter:
    def resolve(self, ttype, suggested):
        overrides = {"recovery": 100, "cleanup": 10}
        return overrides.get(ttype, suggested)
