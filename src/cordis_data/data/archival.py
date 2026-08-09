"""Cleanup of old changelog files beyond the retention window."""

import datetime
from pathlib import Path

RETENTION_DAYS = 90


def cleanup_old_changelogs(
    changelog_dir: Path, today: datetime.date, retention_days: int = RETENTION_DAYS
) -> list[str]:
    """Delete changelog files older than the retention window.

    Args:
        changelog_dir: Directory containing YYYY-MM-DD.json changelog files
        today: Current date, used to compute the cutoff
        retention_days: Number of days to retain (default 90)

    Returns:
        List of deleted file names (for audit logging)
    """
    if not changelog_dir.is_dir():
        return []

    cutoff = today - datetime.timedelta(days=retention_days)
    deleted: list[str] = []

    for log_file in sorted(changelog_dir.glob("*.json")):
        try:
            file_date = datetime.date.fromisoformat(log_file.stem)
        except ValueError:
            continue

        if file_date < cutoff:
            log_file.unlink()
            deleted.append(log_file.name)

    return deleted
