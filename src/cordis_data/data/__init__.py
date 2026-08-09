"""Data fetching and management layer."""

from cordis_data.data.calls import CallsFetcher
from cordis_data.data.projects import ProjectsFetcher

__all__ = ["CallsFetcher", "ProjectsFetcher"]
