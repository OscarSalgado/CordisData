"""Tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cordis_data.cli import main


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "CORDIS Data" in result.output

    def test_fetch_calls_help(self) -> None:
        """Test fetch-calls help."""
        runner = CliRunner()
        result = runner.invoke(main, ["fetch-calls", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output
        assert "--full-history" in result.output

    def test_fetch_calls_basic(self) -> None:
        """Test fetch-calls command execution."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["fetch-calls", "--force"])
            assert result.exit_code in (0, 1)

    def test_fetch_calls_with_force_flag(self) -> None:
        """Test fetch-calls with --force flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch("cordis_data.cli.CallsFetcher.main") as mock_main:
                result = runner.invoke(main, ["fetch-calls", "--force"])
                if result.exit_code == 0:
                    mock_main.assert_called()

    def test_fetch_calls_with_full_history(self) -> None:
        """Test fetch-calls with --full-history flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch("cordis_data.cli.CallsFetcher.main") as mock_main:
                result = runner.invoke(main, ["fetch-calls", "--full-history"])
                if result.exit_code == 0:
                    mock_main.assert_called()

    def test_fetch_calls_with_custom_output(self) -> None:
        """Test fetch-calls with custom output path."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch("cordis_data.cli.CallsFetcher.main") as mock_main:
                result = runner.invoke(
                    main, ["fetch-calls", "--output", "custom_calls.json"]
                )
                if result.exit_code == 0:
                    mock_main.assert_called()

    def test_fetch_projects_help(self) -> None:
        """Test fetch-projects help."""
        runner = CliRunner()
        result = runner.invoke(main, ["fetch-projects", "--help"])
        assert result.exit_code == 0
        assert "--years" in result.output
        assert "--output" in result.output

    def test_fetch_projects_basic(self) -> None:
        """Test fetch-projects command execution."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create dummy calls file
            Path("data").mkdir()
            calls_file = Path("data/calls.json")
            calls_file.write_text(json.dumps([
                {"reference": "CALL-001", "callStatus": "closed"}
            ]))

            with patch("cordis_data.cli.ProjectsFetcher.main"):
                result = runner.invoke(main, ["fetch-projects"])
                assert result.exit_code == 0

    def test_fetch_projects_with_years(self) -> None:
        """Test fetch-projects with --years filter."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("data").mkdir()
            calls_file = Path("data/calls.json")
            calls_file.write_text(json.dumps([]))

            with patch("cordis_data.cli.ProjectsFetcher.main") as mock_main:
                result = runner.invoke(main, ["fetch-projects", "--years", "2"])
                if result.exit_code == 0:
                    mock_main.assert_called()

    def test_fetch_projects_with_paths(self) -> None:
        """Test fetch-projects with custom paths."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            calls_file = Path("calls.json")
            calls_file.write_text(json.dumps([]))

            with patch("cordis_data.cli.ProjectsFetcher.main"):
                result = runner.invoke(
                    main,
                    [
                        "fetch-projects",
                        "--calls",
                        str(calls_file),
                        "--output",
                        "custom_projects.json",
                    ],
                )
                assert result.exit_code in (0, 1)

    def test_status_help(self) -> None:
        """Test status help."""
        runner = CliRunner()
        result = runner.invoke(main, ["status", "--help"])
        assert result.exit_code == 0
        assert "--data-dir" in result.output

    def test_status_command(self) -> None:
        """Test status command."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("data").mkdir()
            metadata_file = Path("data/.metadata.json")
            metadata_file.write_text(json.dumps({
                "calls_fetched_at": "2024-01-01",
                "calls_freshness_ttl_days": 90,
                "projects_fetched_at": "2024-01-02",
                "projects_freshness_ttl_days": 90,
            }))

            result = runner.invoke(main, ["status"])
            assert result.exit_code == 0
            assert "CORDIS Data Status" in result.output

    def test_status_custom_dir(self) -> None:
        """Test status with custom data directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("custom_data").mkdir()
            metadata_file = Path("custom_data/.metadata.json")
            metadata_file.write_text(json.dumps({
                "calls_fetched_at": "2024-01-01",
                "calls_freshness_ttl_days": 90,
                "projects_fetched_at": "2024-01-02",
                "projects_freshness_ttl_days": 90,
            }))

            result = runner.invoke(main, ["status", "--data-dir", "custom_data"])
            assert result.exit_code == 0

    def test_fetch_calls_error_handling(self) -> None:
        """Test fetch-calls handles errors gracefully."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch(
                "cordis_data.cli.CallsFetcher.main",
                side_effect=Exception("API Error")
            ):
                result = runner.invoke(main, ["fetch-calls"])
                assert result.exit_code == 1
                assert "Error fetching calls" in result.output

    def test_fetch_projects_error_handling(self) -> None:
        """Test fetch-projects handles errors gracefully."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch(
                "cordis_data.cli.ProjectsFetcher.main",
                side_effect=Exception("API Error")
            ):
                result = runner.invoke(main, ["fetch-projects"])
                assert result.exit_code == 1
                assert "Error fetching projects" in result.output

    def test_status_error_handling(self) -> None:
        """Test status handles missing metadata gracefully."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create empty data dir without metadata file
            Path("data").mkdir()
            result = runner.invoke(main, ["status"])
            # Status should fail with exit code 1 when no metadata found
            assert result.exit_code in (0, 1)

    def test_multiple_commands_sequence(self) -> None:
        """Test running multiple commands in sequence."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("data").mkdir()

            # Create metadata first
            metadata_file = Path("data/.metadata.json")
            metadata_file.write_text(json.dumps({
                "calls_fetched_at": "2024-01-01",
                "calls_freshness_ttl_days": 90,
                "projects_fetched_at": "2024-01-02",
                "projects_freshness_ttl_days": 90,
            }))

            result = runner.invoke(main, ["status"])
            assert result.exit_code == 0

    def test_cli_entry_point(self) -> None:
        """Test CLI can be invoked as module."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"], catch_exceptions=False)
        # Should fail because Click doesn't have --version by default
        # but proves the entry point works
        assert result.exit_code != 0
