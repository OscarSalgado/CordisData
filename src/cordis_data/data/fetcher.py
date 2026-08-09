"""Base fetcher class for common data fetching patterns."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class BaseFetcher(ABC):
    """Abstract base class for data fetchers.

    Provides common interface for fetchers that retrieve and transform
    data from remote APIs and write to local files.
    """

    @abstractmethod
    def main(self, output_path: Optional[Path] = None, **kwargs: Any) -> None:
        """Execute the fetch, transform, and write pipeline.

        Args:
            output_path: Path to output file
            **kwargs: Additional fetcher-specific arguments
        """
        pass
