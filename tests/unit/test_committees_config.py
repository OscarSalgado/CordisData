"""Tests for CommitteeConfig."""

from pathlib import Path
from unittest.mock import Mock, patch

from cordis_data.data.committees.config import CommitteeConfig


class TestCommitteeConfig:
    """Test CommitteeConfig."""

    def test_load_creates_default(self, tmp_path: Path) -> None:
        """Test loading creates default config."""
        with patch.object(CommitteeConfig, "CONFIG_PATH", tmp_path / "config.json"):
            config = CommitteeConfig.load()
            assert config["committees"] == []
            assert config["alerts"]["enabled"] is True

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test save/load roundtrip."""
        config_path = tmp_path / "config.json"
        with patch.object(CommitteeConfig, "CONFIG_PATH", config_path):
            config = {"committees": [{"code": "C70408", "name": "Test"}], "alerts": {}}
            CommitteeConfig.save(config)
            loaded = CommitteeConfig.load()
            assert loaded["committees"][0]["code"] == "C70408"

    def test_add_committee(self, tmp_path: Path) -> None:
        """Test adding committee."""
        with patch.object(CommitteeConfig, "CONFIG_PATH", tmp_path / "config.json"):
            CommitteeConfig.add_committee("C70408", "Test Committee")
            config = CommitteeConfig.load()
            assert len(config["committees"]) == 1
            assert config["committees"][0]["code"] == "C70408"

    def test_remove_committee(self, tmp_path: Path) -> None:
        """Test removing committee."""
        with patch.object(CommitteeConfig, "CONFIG_PATH", tmp_path / "config.json"):
            CommitteeConfig.add_committee("C70408", "Test")
            CommitteeConfig.remove_committee("C70408")
            config = CommitteeConfig.load()
            assert len(config["committees"]) == 0

    def test_validate_committees_success(self, tmp_path: Path) -> None:
        """Test committee validation succeeds."""
        with patch.object(CommitteeConfig, "CONFIG_PATH", tmp_path / "config.json"):
            CommitteeConfig.add_committee("C70408", "Test")
            with patch("cordis_data.data.committees.config.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [{"code": "C70408"}]
                result = CommitteeConfig.validate_committees()
                assert result is True

    def test_validate_committees_fails(self, tmp_path: Path) -> None:
        """Test committee validation fails on invalid code."""
        with patch.object(CommitteeConfig, "CONFIG_PATH", tmp_path / "config.json"):
            CommitteeConfig.add_committee("INVALID", "Test")
            with patch("cordis_data.data.committees.config.CommitteeDocumentsClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [{"code": "C70408"}]
                result = CommitteeConfig.validate_committees()
                assert result is False
