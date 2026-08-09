"""Tests for metadata management."""

import datetime

import tempfile
from pathlib import Path

from cordis_data.data.metadata import (
    is_stale,
    load_metadata,
    save_metadata,
    update_timestamp,
)


class TestMetadata:
    """Tests for metadata functions."""

    def test_load_metadata_default(self) -> None:
        """Test loading metadata when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.json"
            metadata = load_metadata(metadata_path)
            assert metadata["calls_fetched_at"] is None
            assert metadata["calls_freshness_ttl_days"] == 90

    def test_save_and_load_metadata(self) -> None:
        """Test saving and loading metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.json"
            original = {
                "calls_fetched_at": "2024-08-09",
                "calls_freshness_ttl_days": 30,
            }
            save_metadata(original, metadata_path)
            loaded = load_metadata(metadata_path)
            assert loaded["calls_fetched_at"] == "2024-08-09"

    def test_is_stale_never_fetched(self) -> None:
        """Test stale check for data never fetched."""
        assert is_stale(None, 90) is True

    def test_is_stale_fresh_data(self) -> None:
        """Test fresh data is not stale."""
        today = datetime.date.today().isoformat()
        assert is_stale(today, 90) is False

    def test_is_stale_old_data(self) -> None:
        """Test old data is stale."""
        old_date = (datetime.date.today() - datetime.timedelta(days=100)).isoformat()
        assert is_stale(old_date, 90) is True

    def test_update_timestamp(self) -> None:
        """Test updating timestamp."""
        metadata = {"calls_fetched_at": None}
        updated = update_timestamp(metadata, "calls_fetched_at")
        assert updated["calls_fetched_at"] == datetime.date.today().isoformat()

    def test_is_stale_invalid_date_format(self) -> None:
        """Test stale check with invalid date format."""
        # Invalid ISO format should return True (treat as stale)
        assert is_stale("not-a-valid-date", 90) is True

    def test_is_stale_with_none_value(self) -> None:
        """Test stale check with None timestamp."""
        assert is_stale(None, 90) is True

    def test_is_stale_boundary(self) -> None:
        """Test stale check at exact boundary."""
        # Exactly 90 days old should be stale
        old_date = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        assert is_stale(old_date, 90) is True

    def test_is_stale_one_day_fresh(self) -> None:
        """Test stale check for 1 day old with 90 day TTL."""
        old_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        assert is_stale(old_date, 90) is False
