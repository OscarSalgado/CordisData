"""Tests for TokenBucket rate limiter."""

import time
import threading

from cordis_data.api.rate_limiter import TokenBucket


class TestTokenBucket:
    """Tests for TokenBucket rate limiter."""

    def test_acquire_with_available_token(self) -> None:
        """Test acquiring a token when bucket is full."""
        limiter = TokenBucket(rate=1.0)
        # Should return immediately without blocking
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be nearly instant

    def test_acquire_blocks_when_empty(self) -> None:
        """Test that acquire blocks when no tokens available."""
        limiter = TokenBucket(rate=1.0)
        # Consume initial token
        limiter.acquire()
        # Next should block for ~1 second
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed >= 0.9  # Allow some margin

    def test_multiple_acquisitions_in_sequence(self) -> None:
        """Test acquiring multiple tokens in sequence."""
        limiter = TokenBucket(rate=2.0)  # 2 tokens per second
        # Should have 2 tokens initially
        limiter.acquire()
        limiter.acquire()
        # Third should block for ~0.5 seconds
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed >= 0.4

    def test_thread_safe_concurrent_access(self) -> None:
        """Test thread safety with concurrent acquire calls."""
        limiter = TokenBucket(rate=1.0)
        results = []

        def acquire_token() -> None:
            start = time.time()
            limiter.acquire()
            elapsed = time.time() - start
            results.append(elapsed)

        threads = [threading.Thread(target=acquire_token) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have 3 results
        assert len(results) == 3
        # Total elapsed time should be at least ~2 seconds for 3 sequential acquisitions
        total = sum(results)
        assert total >= 1.8
