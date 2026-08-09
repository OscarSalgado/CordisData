"""Alert senders for committee documents."""

import json
from abc import ABC, abstractmethod
from typing import Optional

import requests


class AlertSender(ABC):
    """Base class for alert senders."""

    @abstractmethod
    def send(self, documents: list[dict]) -> bool:
        """Send alert for new documents.

        Args:
            documents: List of new document dicts

        Returns:
            True if successful, False otherwise
        """
        pass


class SlackAlertSender(AlertSender):
    """Send alerts via Slack webhook."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize Slack sender.

        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url

    def send(self, documents: list[dict]) -> bool:
        """Send Slack message for new documents."""
        if not documents:
            return True

        try:
            blocks = []
            for doc in documents[:5]:  # Limit to 5 per message
                title = doc.get("title", "Unknown")
                committee = doc.get("committeeCoding", "N/A")
                doc_type = doc.get("documentType", "Unknown")

                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title}*\n"
                            f"Committee: {committee}\n"
                            f"Type: {doc_type}\n"
                            f"Ref: {doc.get('documentReference')}",
                        },
                    }
                )

            payload = {
                "text": f"🆕 {len(documents)} new committee document(s)",
                "blocks": blocks,
            }

            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False


class EmailAlertSender(AlertSender):
    """Send alerts via email (stub for Phase 2)."""

    def __init__(self, email_address: str) -> None:
        """Initialize email sender.

        Args:
            email_address: Recipient email address
        """
        self.email_address = email_address

    def send(self, documents: list[dict]) -> bool:
        """Send email alert."""
        # Stub: to be implemented in Phase 2
        return True


class GitHubIssueAlertSender(AlertSender):
    """Create GitHub issues for new documents."""

    def __init__(self, repo: str, token: str) -> None:
        """Initialize GitHub issue sender.

        Args:
            repo: GitHub repo in format 'owner/repo'
            token: GitHub API token
        """
        self.repo = repo
        self.token = token
        self.api_base = "https://api.github.com"

    def send(self, documents: list[dict]) -> bool:
        """Create GitHub issues for new documents."""
        if not documents:
            return True

        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }

            for doc in documents:
                title = f"[{doc.get('committeeCoding', 'COMMITTEE')}] {doc.get('title', 'New Document')}"
                body = (
                    f"**Committee:** {doc.get('committeeCoding')}\n"
                    f"**Type:** {doc.get('documentType')}\n"
                    f"**Reference:** {doc.get('documentReference')}\n"
                    f"**Date:** {doc.get('creationDate')}\n\n"
                    f"Language: {doc.get('language', 'EN')}\n"
                )

                payload = {"title": title[:255], "body": body}

                resp = requests.post(
                    f"{self.api_base}/repos/{self.repo}/issues",
                    json=payload,
                    headers=headers,
                    timeout=10,
                )

                if resp.status_code != 201:
                    return False

            return True
        except Exception:
            return False


class AlertDispatcher:
    """Dispatch alerts to configured senders."""

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        email: Optional[str] = None,
        github_issues: bool = False,
        github_repo: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> None:
        """Initialize dispatcher.

        Args:
            slack_webhook: Slack webhook URL
            email: Email address
            github_issues: Enable GitHub issues
            github_repo: GitHub repo (owner/repo)
            github_token: GitHub API token
        """
        self.senders: list[AlertSender] = []

        if slack_webhook:
            self.senders.append(SlackAlertSender(slack_webhook))

        if email:
            self.senders.append(EmailAlertSender(email))

        if github_issues and github_repo and github_token:
            self.senders.append(GitHubIssueAlertSender(github_repo, github_token))

    def send(self, documents: list[dict]) -> dict[str, bool]:
        """Send alerts to all configured senders.

        Args:
            documents: List of new documents

        Returns:
            Dict mapping sender type to success status
        """
        results = {}

        for sender in self.senders:
            try:
                success = sender.send(documents)
                sender_name = sender.__class__.__name__
                results[sender_name] = success
            except Exception:
                results[sender.__class__.__name__] = False

        return results
