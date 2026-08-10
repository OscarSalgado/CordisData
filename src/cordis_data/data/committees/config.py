"""Configuration management for committee monitoring."""

import copy
import json
from pathlib import Path
from typing import Any, Optional

from cordis_data.data.committees.client import CommitteeDocumentsClient


class CommitteeConfig:
    """Manage committee monitoring configuration."""

    @staticmethod
    def _get_config_path() -> Path:
        """Get config path relative to project root."""
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "data").exists():
                return current / "data" / "committees" / "config.json"
            current = current.parent
        # Fallback to ~/.cordis-data if data/ not found
        return Path.home() / ".cordis-data" / "committees-config.json"

    CONFIG_PATH = _get_config_path()
    DEFAULT_CONFIG: dict[str, Any] = {
        "committees": [],
        "alerts": {"enabled": True, "slack_webhook": None, "email": None, "github_issues": False},
        "last_check": None,
    }

    @classmethod
    def _get_current_config_path(cls) -> Path:
        """Get config path relative to project root."""
        current = Path(__file__).resolve().parent
        # Go up to project root (5 levels from this file)
        project_root = current.parent.parent.parent.parent
        data_path = project_root / "data" / "committees" / "config.json"
        if data_path.exists() or (project_root / "data").exists():
            return data_path
        # Fallback to ~/.cordis-data if data/ not found
        return Path.home() / ".cordis-data" / "committees-config.json"

    @classmethod
    def load(cls) -> dict[str, Any]:
        """Load config from disk."""
        config_path = cls._get_current_config_path()
        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                return json.load(f)
        return copy.deepcopy(cls.DEFAULT_CONFIG)

    @classmethod
    def save(cls, config: dict[str, Any]) -> None:
        """Save config to disk."""
        config_path = cls._get_current_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

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
