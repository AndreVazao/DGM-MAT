import time
class RetryManager:
    def __init__(self, max_retries=3, delay=60):
        self.max_retries = max_retries
        self.delay = delay
    def should_retry(self, count): return count < self.max_retries
    def next_retry(self, count): return time.time() + (self.delay * (2**count))
