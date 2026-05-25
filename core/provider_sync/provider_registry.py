class ProviderRegistry:
    def __init__(self): self.providers = {}
    def register(self, name, adapter): self.providers[name] = adapter
