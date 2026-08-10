"""Performance tests for committee monitoring."""

import time
from unittest.mock import Mock, patch

from cordis_data.data.committees.fetcher import CommitteeDocumentsFetcher


class TestCommitteePerformance:
    """Performance benchmarks for committee monitoring."""

    def test_fetch_single_committee(self) -> None:
        """Benchmark fetch for single committee."""
        with patch("cordis_data.data.committees.fetcher.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock response with 100 documents
            mock_client.fetch_documents.return_value = {
                "content": [
                    {
                        "documentReference": f"doc-{i}",
                        "title": f"Document {i}",
                        "creationDate": "2026-07-01T00:00:00Z",
                    }
                    for i in range(100)
                ],
                "totalPages": 1,
            }

            fetcher = CommitteeDocumentsFetcher(mock_client)

            start = time.time()
            fetcher.main(["C70408"])
            elapsed = time.time() - start

            # Single committee should complete in < 1 second
            assert elapsed < 1.0
            print(f"Single committee fetch: {elapsed:.2f}s")

    def test_fetch_many_committees_simulated(self) -> None:
        """Simulate fetch for many committees.

        This doesn't actually call the API 624 times, but measures
        the processing overhead with realistic document counts.
        """
        with patch("cordis_data.data.committees.fetcher.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Simulate 624 committees with average 5 documents each
            # This is ~3120 documents total
            total_docs = 3120

            mock_client.fetch_documents.return_value = {
                "content": [
                    {
                        "documentReference": f"doc-{i}",
                        "title": f"Document {i}",
                        "creationDate": "2026-07-01T00:00:00Z",
                    }
                    for i in range(total_docs)
                ],
                "totalPages": 1,
            }

            fetcher = CommitteeDocumentsFetcher(mock_client)

            # Test with simulated 624 committees
            start = time.time()
            fetcher.main([f"C{70000+i}" for i in range(624)])
            elapsed = time.time() - start

            # Processing 3120 documents should complete in < 5 seconds
            assert elapsed < 5.0
            print(f"624 committees (3120 docs) fetch: {elapsed:.2f}s")

    def test_change_detection_performance(self) -> None:
        """Benchmark change detection with many documents."""
        fetcher = CommitteeDocumentsFetcher()

        # Create 1000 existing documents
        existing = [
            {
                "documentReference": f"doc-{i}",
                "title": f"Document {i}",
                "updateDate": "2026-07-01T00:00:00Z",
            }
            for i in range(1000)
        ]

        # Fetch with 10% new, 10% updated, 80% unchanged
        fetched = [
            {
                "documentReference": f"doc-{i}",
                "title": f"Document {i}",
                "updateDate": (
                    "2026-07-02T00:00:00Z" if i < 100  # 10% updated
                    else "2026-07-01T00:00:00Z"
                ),
            }
            for i in range(1000)
        ] + [
            {
                "documentReference": f"doc-new-{i}",
                "title": f"New Document {i}",
                "updateDate": "2026-07-02T00:00:00Z",
            }
            for i in range(100)  # 10% new
        ]

        start = time.time()
        new_docs, events = fetcher.detect_changes(existing, fetched)
        elapsed = time.time() - start

        # Change detection on 1100 documents should be < 100ms
        assert elapsed < 0.1
        assert len(new_docs) == 100  # 10% new
        print(f"Change detection (1100 docs): {elapsed*1000:.1f}ms")

    def test_rate_limiter_throughput(self) -> None:
        """Benchmark rate limiter throughput."""
        from cordis_data.api.rate_limiter import TokenBucket

        limiter = TokenBucket(rate=2)

        start = time.time()
        for _ in range(100):
            limiter.acquire()
        elapsed = time.time() - start

        # 100 requests at 2 req/sec should take ~50 seconds
        expected = 50.0
        tolerance = 5.0  # Allow ±5 second variance

        assert expected - tolerance < elapsed < expected + tolerance
        print(f"Rate limiter 100 requests: {elapsed:.1f}s (expected ~{expected}s)")
