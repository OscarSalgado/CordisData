"""CordisData: Python module for EU research funding data collection and management.

Provides APIs for fetching and managing data from CORDIS and SEDIA funding portals.
"""

__version__ = "0.1.0"

from cordis_data.api import CordisClient, SediaClient, TokenBucket
from cordis_data.models import Call, Project

__all__ = [
    "CordisClient",
    "SediaClient",
    "TokenBucket",
    "Call",
    "Project",
]
