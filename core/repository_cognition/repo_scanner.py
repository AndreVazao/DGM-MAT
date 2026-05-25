from core.repository_intelligence.scanner import RepositoryScanner
class CognitiveRepoScanner:
    def __init__(self): self.scanner = RepositoryScanner()
    def scan(self): return self.scanner.scan()
