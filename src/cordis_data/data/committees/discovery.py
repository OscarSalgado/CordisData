"""Committee discovery - detect new committees from EU API."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from cordis_data.data.committees.client import CommitteeDocumentsClient
from cordis_data.data.committees.config import CommitteeConfig


class DiscoveryResult:
    """Result of a discovery run."""

    def __init__(
        self,
        new_committees: list[dict],
        total_committees: int,
        currently_monitored: int,
        discovery_log_path: Path,
    ) -> None:
        """Initialize discovery result.

        Args:
            new_committees: List of newly discovered committees
            total_committees: Total committees available in API
            currently_monitored: Number of committees in local config
            discovery_log_path: Path to discovery.json file
        """
        self.new_committees = new_committees
        self.total_committees = total_committees
        self.currently_monitored = currently_monitored
        self.discovery_log_path = discovery_log_path

    def has_new(self) -> bool:
        """Check if new committees were found."""
        return len(self.new_committees) > 0


class CommitteeDiscovery:
    """Discover new committees from EU commitology register."""

    def __init__(self, client: Optional[CommitteeDocumentsClient] = None) -> None:
        """Initialize discovery engine.

        Args:
            client: CommitteeDocumentsClient instance
        """
        self.client = client or CommitteeDocumentsClient()
        # Set discovery log path relative to project root (5 levels up)
        current = Path(__file__).resolve().parent
        project_root = current.parent.parent.parent.parent
        data_path = project_root / "data" / "committees" / "discovery.json"
        if (project_root / "data").exists():
            self.discovery_log_path = data_path
        else:
            # Fallback to ~/.cordis-data if data/ not found
            self.discovery_log_path = Path.home() / ".cordis-data" / "discovery.json"

    @property
    def DISCOVERY_LOG_PATH(self) -> Path:
        """Get discovery log path."""
        return self.discovery_log_path

    @DISCOVERY_LOG_PATH.setter
    def DISCOVERY_LOG_PATH(self, path: Path) -> None:
        """Set discovery log path (for testing)."""
        self.discovery_log_path = path

    def discover(self) -> DiscoveryResult:
        """Discover new committees not in local config.

        Returns:
            DiscoveryResult with new committees and metadata
        """
        # Fetch all committees from API
        all_committees = self._fetch_all_committees()

        # Get monitored committees from config
        config = CommitteeConfig.load()
        monitored_codes = {c["code"] for c in config.get("committees", [])}

        # Detect new ones
        new_committees = self._detect_new(all_committees, monitored_codes)

        # Deduplicate (remove ones already reported)
        new_committees = self._deduplicate(new_committees)

        # Save to discovery log
        self._save_discovery_log(new_committees)

        return DiscoveryResult(
            new_committees=new_committees,
            total_committees=len(all_committees),
            currently_monitored=len(monitored_codes),
            discovery_log_path=self.DISCOVERY_LOG_PATH,
        )

    def _fetch_all_committees(self) -> list[dict]:
        """Fetch all committees from EU API.

        Returns:
            List of dicts with 'code' and 'title' fields
        """
        return self.client.list_committees()

    def _detect_new(
        self, all_committees: list[dict], monitored_codes: set[str]
    ) -> list[dict]:
        """Detect committees not in monitored set.

        Args:
            all_committees: List of all available committees
            monitored_codes: Set of monitored committee codes

        Returns:
            List of new committees
        """
        new = []
        for committee in all_committees:
            if committee["code"] not in monitored_codes:
                new.append(committee)
        return new

    def _load_discovery_log(self) -> dict[str, Any]:
        """Load discovery log from disk.

        Returns:
            Discovery log dict, or empty if not exists
        """
        if not self.DISCOVERY_LOG_PATH.exists():
            return self._create_empty_log()

        try:
            with open(self.DISCOVERY_LOG_PATH, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self._create_empty_log()

    def _create_empty_log(self) -> dict[str, Any]:
        """Create empty discovery log structure.

        Returns:
            Empty log dict
        """
        return {
            "metadata": {
                "version": "1.0",
                "last_run": None,
            },
            "discoveries": [],
            "history": {
                "total_discovered": 0,
                "issues_created": [],
            },
        }

    def _save_discovery_log(self, new_committees: list[dict]) -> None:
        """Save new discoveries to log.

        Args:
            new_committees: List of new committees to log
        """
        log = self._load_discovery_log()

        # Update last run
        log["metadata"]["last_run"] = datetime.now(timezone.utc).isoformat()

        # Add new discoveries
        for committee in new_committees:
            log["discoveries"].append(
                {
                    "code": committee["code"],
                    "title": committee.get("title", ""),
                    "discovered_at": datetime.now(timezone.utc).isoformat(),
                    "reported": False,
                }
            )

        # Update counter
        log["history"]["total_discovered"] = len(log["discoveries"])

        # Ensure parent directory exists
        self.DISCOVERY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write to disk
        with open(self.DISCOVERY_LOG_PATH, "w", encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    def _deduplicate(self, new_committees: list[dict]) -> list[dict]:
        """Remove committees already reported in discovery log.

        Args:
            new_committees: List of potentially new committees

        Returns:
            Filtered list of truly new committees (not in log)
        """
        log = self._load_discovery_log()
        known_codes = {d["code"] for d in log.get("discoveries", [])}

        filtered = []
        for committee in new_committees:
            if committee["code"] not in known_codes:
                filtered.append(committee)

        return filtered

    def mark_as_reported(self, committee_codes: list[str]) -> None:
        """Mark committees as reported in GitHub issue.

        Args:
            committee_codes: List of committee codes to mark
        """
        log = self._load_discovery_log()

        for discovery in log.get("discoveries", []):
            if discovery["code"] in committee_codes:
                discovery["reported"] = True

        # Record issue creation
        issue_record = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "count": len(committee_codes),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if "issues_created" not in log.get("history", {}):
            log["history"]["issues_created"] = []
        log["history"]["issues_created"].append(issue_record)

        # Write back
        with open(self.DISCOVERY_LOG_PATH, "w", encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    def cleanup_old_discoveries(self, days: int = 90) -> None:
        """Remove discoveries older than specified days.

        Args:
            days: Number of days to keep (default: 90)
        """
        log = self._load_discovery_log()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        filtered = []
        for discovery in log.get("discoveries", []):
            try:
                discovered_at = datetime.fromisoformat(
                    discovery["discovered_at"].replace("Z", "+00:00")
                )
                if discovered_at >= cutoff:
                    filtered.append(discovery)
            except (ValueError, KeyError):
                filtered.append(discovery)

        log["discoveries"] = filtered
        log["history"]["total_discovered"] = len(filtered)

        with open(self.DISCOVERY_LOG_PATH, "w", encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
