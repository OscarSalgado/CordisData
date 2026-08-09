"""Thread-safe rate limiter using token bucket algorithm."""

import threading
import time


class TokenBucket:
    """Thread-safe rate limiter using token bucket algorithm.

    Permits a configurable maximum number of requests per second. All worker
    threads share a single TokenBucket instance; calling acquire() blocks until
    a token is available (regenerated at 'rate' tokens per second).

    Example:
        limiter = TokenBucket(rate=2.0)  # max 2 requests/second
        limiter.acquire()  # blocks if no token available
        # ... make request ...
    """

    def __init__(self, rate: float = 2.0) -> None:
        """Initialize with max requests per second.

        Args:
            rate: float, requests per second (e.g., 2.0 = max 2 req/s)
        """
        self.rate = rate
        self.tokens = rate  # start with full bucket
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Wait until a token is available, then consume it.

        Blocks if the bucket is empty; tokens regenerate at self.rate per
        second. Thread-safe: uses lock to protect shared state.
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Regenerate tokens (max self.rate per second)
            new_tokens = self.tokens + elapsed * self.rate
            self.tokens = min(self.rate, new_tokens)
            self.last_update = now

            if self.tokens >= 1:
                # Token available, consume and proceed
                self.tokens -= 1
                return

            # No token available; calculate wait time and sleep
            wait_time = (1 - self.tokens) / self.rate
            time.sleep(wait_time)
            self.tokens = 0
            self.last_update = time.time()
