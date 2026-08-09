"""Merge and summarization logic for fetched data."""

from collections import Counter
from typing import Any


def mark_expired_closed(calls: list[dict[str, Any]], today_str: str) -> int:
    """Mark open/forthcoming calls whose deadline has passed as closed.

    Mutates each call dict in place.

    Args:
        calls: List of call dicts
        today_str: Today's date as YYYY-MM-DD string

    Returns:
        Number of calls marked as closed
    """
    marked_closed = 0
    for c in calls:
        if c.get("deadline") and c["deadline"] < today_str:
            if c["callStatus"] in ("open", "forthcoming"):
                c["callStatus"] = "closed"
                marked_closed += 1
    return marked_closed


def get_programme_distribution(calls: list[dict[str, Any]]) -> dict[str, int]:
    """Get count of calls by programme.

    Args:
        calls: List of call dicts

    Returns:
        Dict mapping programme name to count, most common first
    """
    return dict(Counter(c["programme"] for c in calls).most_common())


def get_status_distribution(calls: list[dict[str, Any]]) -> dict[str, int]:
    """Get count of calls by status.

    Args:
        calls: List of call dicts

    Returns:
        Dict mapping status to count
    """
    return dict(Counter(c["callStatus"] for c in calls).items())
