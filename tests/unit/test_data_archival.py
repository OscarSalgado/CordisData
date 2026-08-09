"""Tests for changelog archival/cleanup."""

import datetime
from pathlib import Path

from cordis_data.data.archival import cleanup_old_changelogs


class TestCleanupOldChangelogs:
    """Tests for cleanup_old_changelogs()."""

    def test_missing_directory_returns_empty(self, temp_dir: Path) -> None:
        """A non-existent changelog directory yields no deletions."""
        missing_dir = temp_dir / "changelog"
        deleted = cleanup_old_changelogs(missing_dir, datetime.date(2026, 8, 9))
        assert deleted == []

    def test_deletes_files_older_than_retention(self, temp_dir: Path) -> None:
        """Files older than the retention window are deleted."""
        changelog_dir = temp_dir / "changelog"
        changelog_dir.mkdir()

        old_file = changelog_dir / "2026-01-01.json"
        old_file.write_text("{}")
        recent_file = changelog_dir / "2026-08-01.json"
        recent_file.write_text("{}")

        today = datetime.date(2026, 8, 9)
        deleted = cleanup_old_changelogs(changelog_dir, today, retention_days=90)

        assert deleted == ["2026-01-01.json"]
        assert not old_file.exists()
        assert recent_file.exists()

    def test_keeps_files_within_retention(self, temp_dir: Path) -> None:
        """Files within the retention window are kept."""
        changelog_dir = temp_dir / "changelog"
        changelog_dir.mkdir()

        recent_file = changelog_dir / "2026-07-01.json"
        recent_file.write_text("{}")

        today = datetime.date(2026, 8, 9)
        deleted = cleanup_old_changelogs(changelog_dir, today, retention_days=90)

        assert deleted == []
        assert recent_file.exists()

    def test_ignores_non_date_filenames(self, temp_dir: Path) -> None:
        """Files that don't match YYYY-MM-DD.json are skipped, not errored on."""
        changelog_dir = temp_dir / "changelog"
        changelog_dir.mkdir()

        bogus_file = changelog_dir / "not-a-date.json"
        bogus_file.write_text("{}")

        deleted = cleanup_old_changelogs(changelog_dir, datetime.date(2026, 8, 9))

        assert deleted == []
        assert bogus_file.exists()

    def test_boundary_date_is_kept(self, temp_dir: Path) -> None:
        """A file exactly at the cutoff date is not deleted (< cutoff, not <=)."""
        changelog_dir = temp_dir / "changelog"
        changelog_dir.mkdir()

        today = datetime.date(2026, 8, 9)
        cutoff_file = changelog_dir / (today - datetime.timedelta(days=90)).isoformat()
        cutoff_file = cutoff_file.with_suffix(".json")
        cutoff_file.write_text("{}")

        deleted = cleanup_old_changelogs(changelog_dir, today, retention_days=90)

        assert deleted == []
        assert cutoff_file.exists()
