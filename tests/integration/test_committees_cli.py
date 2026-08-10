"""Integration tests for committee monitoring CLI."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from cordis_data.cli.monitor import monitor


class TestMonitorCLI:
    """Test monitor CLI commands."""

    def test_add_committee_success(self) -> None:
        """Test adding a committee via CLI."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeDocumentsClient") as mock_client_class:
            with patch("cordis_data.cli.monitor.CommitteeConfig"):
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.list_committees.return_value = [
                    {"code": "C70408", "title": "Digital Committee"}
                ]

                result = runner.invoke(monitor, ["add-committee", "C70408"])
                assert result.exit_code == 0
                assert "Added committee" in result.output

    def test_add_committee_not_found(self) -> None:
        """Test adding nonexistent committee fails."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeDocumentsClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.list_committees.return_value = []

            result = runner.invoke(monitor, ["add-committee", "INVALID"])
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_list_committees(self) -> None:
        """Test listing committees."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {
                "committees": [{"code": "C70408", "name": "Digital", "enabled": True}]
            }

            result = runner.invoke(monitor, ["list-committees"])
            assert result.exit_code == 0
            assert "C70408" in result.output

    def test_remove_committee(self) -> None:
        """Test removing a committee."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeConfig") as mock_config_class:
            result = runner.invoke(monitor, ["remove-committee", "C70408"])
            assert result.exit_code == 0
            mock_config_class.remove_committee.assert_called_with("C70408")

    def test_config_show(self) -> None:
        """Test showing config."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {
                "committees": [],
                "alerts": {"enabled": True},
            }

            result = runner.invoke(monitor, ["config-show"])
            assert result.exit_code == 0
            assert "committees" in result.output

    def test_fetch_no_committees(self) -> None:
        """Test fetch fails with no committees configured."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeConfig") as mock_config_class:
            mock_config_class.load.return_value = {"committees": []}

            result = runner.invoke(monitor, ["fetch"])
            assert result.exit_code == 1
            assert "No committees configured" in result.output

    def test_discover_no_new_committees(self) -> None:
        """Test discover when no new committees found."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeDiscovery") as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_result = Mock()
            mock_result.has_new.return_value = False
            mock_result.new_committees = []
            mock_result.total_committees = 100
            mock_result.currently_monitored = 5
            mock_discovery.discover.return_value = mock_result

            result = runner.invoke(monitor, ["discover"])
            assert result.exit_code == 0
            assert "No new committees" in result.output

    def test_discover_finds_new_committees(self) -> None:
        """Test discover when new committees found."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeDiscovery") as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_result = Mock()
            mock_result.has_new.return_value = True
            mock_result.new_committees = [
                {"code": "C70409", "title": "New Committee"}
            ]
            mock_result.total_committees = 100
            mock_result.currently_monitored = 5
            mock_discovery.discover.return_value = mock_result

            result = runner.invoke(monitor, ["discover"])
            assert result.exit_code == 1
            assert "New committees found" in result.output
            assert "C70409" in result.output

    def test_discover_dry_run(self) -> None:
        """Test discover with --dry-run option."""
        runner = CliRunner()
        with patch("cordis_data.cli.monitor.CommitteeDiscovery") as mock_discovery_class:
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_result = Mock()
            mock_result.has_new.return_value = False
            mock_result.new_committees = []
            mock_result.total_committees = 100
            mock_result.currently_monitored = 5
            mock_discovery.discover.return_value = mock_result

            result = runner.invoke(monitor, ["discover", "--dry-run"])
            assert result.exit_code == 0
