"""Configuration management for committee monitoring."""

import json
from pathlib import Path
from typing import Any, Optional

from cordis_data.data.committees.client import CommitteeDocumentsClient


class CommitteeConfig:
    """Manage committee monitoring configuration."""

    CONFIG_PATH = Path.home() / ".cordis-data" / "committees-config.json"
    DEFAULT_CONFIG = {
        "committees": [],
        "alerts": {"enabled": True, "slack_webhook": None, "email": None, "github_issues": False},
        "last_check": None,
    }

    @classmethod
    def load(cls) -> dict[str, Any]:
        """Load config from disk."""
        if cls.CONFIG_PATH.exists():
            with open(cls.CONFIG_PATH) as f:
                return json.load(f)
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, config: dict[str, Any]) -> None:
        """Save config to disk."""
        cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    @classmethod
    def add_committee(cls, code: str, name: str) -> None:
        """Add committee to config."""
        config = cls.load()
        if not any(c["code"] == code for c in config["committees"]):
            config["committees"].append({"code": code, "name": name, "enabled": True})
            cls.save(config)

    @classmethod
    def remove_committee(cls, code: str) -> None:
        """Remove committee from config."""
        config = cls.load()
        config["committees"] = [c for c in config["committees"] if c["code"] != code]
        cls.save(config)

    @classmethod
    def validate_committees(cls, client: Optional[CommitteeDocumentsClient] = None) -> bool:
        """Validate all configured committees exist."""
        client = client or CommitteeDocumentsClient()
        config = cls.load()

        available_codes = {c["code"] for c in client.list_committees()}

        for committee in config["committees"]:
            if committee["code"] not in available_codes:
                return False

        return True
