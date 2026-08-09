"""Tests for committee alerts system."""

from unittest.mock import Mock, patch

import pytest

from cordis_data.data.committees.alerts import (
    AlertDispatcher,
    EmailAlertSender,
    GitHubIssueAlertSender,
    SlackAlertSender,
)


class TestSlackAlertSender:
    """Test Slack alert sender."""

    def test_send_success(self) -> None:
        """Test successful Slack alert."""
        sender = SlackAlertSender("https://hooks.slack.com/test")
        with patch("cordis_data.data.committees.alerts.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            result = sender.send(
                [{"title": "Test", "committeeCoding": "C70408", "documentReference": "123"}]
            )
            assert result is True

    def test_send_failure(self) -> None:
        """Test failed Slack alert."""
        sender = SlackAlertSender("https://hooks.slack.com/test")
        with patch("cordis_data.data.committees.alerts.requests.post") as mock_post:
            mock_post.return_value.status_code = 500
            result = sender.send([{"title": "Test"}])
            assert result is False

    def test_send_empty(self) -> None:
        """Test sending empty list."""
        sender = SlackAlertSender("https://hooks.slack.com/test")
        result = sender.send([])
        assert result is True


class TestEmailAlertSender:
    """Test Email alert sender (stub)."""

    def test_send_stub(self) -> None:
        """Test email sender stub."""
        sender = EmailAlertSender("test@example.com")
        result = sender.send([{"title": "Test"}])
        assert result is True


class TestGitHubIssueAlertSender:
    """Test GitHub issue alert sender."""

    def test_send_success(self) -> None:
        """Test successful GitHub issue creation."""
        sender = GitHubIssueAlertSender("owner/repo", "token123")
        with patch("cordis_data.data.committees.alerts.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            result = sender.send(
                [
                    {
                        "title": "Test Doc",
                        "committeeCoding": "C70408",
                        "documentReference": "123",
                        "creationDate": "2026-08-01",
                    }
                ]
            )
            assert result is True

    def test_send_failure(self) -> None:
        """Test failed GitHub issue creation."""
        sender = GitHubIssueAlertSender("owner/repo", "token123")
        with patch("cordis_data.data.committees.alerts.requests.post") as mock_post:
            mock_post.return_value.status_code = 401
            result = sender.send([{"title": "Test"}])
            assert result is False


class TestAlertDispatcher:
    """Test alert dispatcher."""

    def test_dispatcher_with_slack(self) -> None:
        """Test dispatcher with Slack."""
        dispatcher = AlertDispatcher(slack_webhook="https://hooks.slack.com/test")
        assert len(dispatcher.senders) == 1

    def test_dispatcher_with_all(self) -> None:
        """Test dispatcher with all senders."""
        dispatcher = AlertDispatcher(
            slack_webhook="https://hooks.slack.com/test",
            email="test@example.com",
            github_issues=True,
            github_repo="owner/repo",
            github_token="token123",
        )
        assert len(dispatcher.senders) == 3

    def test_dispatcher_send(self) -> None:
        """Test dispatcher send."""
        dispatcher = AlertDispatcher(slack_webhook="https://hooks.slack.com/test")
        with patch.object(dispatcher.senders[0], "send", return_value=True):
            results = dispatcher.send([{"title": "Test"}])
            assert "SlackAlertSender" in results
            assert results["SlackAlertSender"] is True

    def test_dispatcher_empty_sends(self) -> None:
        """Test dispatcher with no senders."""
        dispatcher = AlertDispatcher()
        results = dispatcher.send([{"title": "Test"}])
        assert len(results) == 0
