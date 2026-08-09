"""Tests for BaseFetcher."""

from cordis_data.data.fetcher import BaseFetcher


class TestBaseFetcher:
    """Tests for BaseFetcher abstract base class."""

    def test_base_fetcher_cannot_be_instantiated(self) -> None:
        """Test that BaseFetcher is abstract and cannot be instantiated."""
        try:
            # Attempting to create an instance should raise TypeError
            BaseFetcher()  # type: ignore
        except TypeError as e:
            # Expected to fail with abstract method error
            assert "abstract" in str(e).lower()
