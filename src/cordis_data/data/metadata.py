"""Metadata management for data freshness tracking."""

import datetime
import json
from pathlib import Path
from typing import Any, Optional


def load_metadata(metadata_path: Path) -> dict[str, Any]:
    """Load metadata from file or return defaults."""
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "calls_fetched_at": None,
        "calls_freshness_ttl_days": 90,
        "projects_fetched_at": None,
        "projects_freshness_ttl_days": 30,
    }


def save_metadata(metadata: dict[str, Any], metadata_path: Path) -> None:
    """Save metadata to file."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def is_stale(
    last_fetch_timestamp: Optional[str],
    ttl_days: int,
) -> bool:
    """Check if data is stale based on last fetch timestamp and TTL.

    Args:
        last_fetch_timestamp: ISO date string (YYYY-MM-DD) or None
        ttl_days: Time-to-live in days

    Returns:
        True if stale or never fetched, False if fresh
    """
    if not last_fetch_timestamp:
        return True
    try:
        last_fetch = datetime.date.fromisoformat(last_fetch_timestamp)
        age = (datetime.date.today() - last_fetch).days
        return age >= ttl_days
    except (ValueError, TypeError):
        return True


def update_timestamp(
    metadata: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    """Update a timestamp field to today's date.

    Args:
        metadata: Metadata dict
        key: Field name to update (e.g., 'calls_fetched_at')

    Returns:
        Updated metadata dict
    """
    metadata[key] = datetime.date.today().isoformat()
    return metadata
