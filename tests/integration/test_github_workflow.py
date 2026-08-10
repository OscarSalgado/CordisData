"""Tests for GitHub Actions workflow integration."""

from pathlib import Path


def test_workflow_file_exists() -> None:
    """Test that monitor-committees workflow file exists."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    assert workflow_file.exists(), "Workflow file not found"


def test_workflow_valid_yaml() -> None:
    """Test that workflow file is valid YAML."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    content = workflow_file.read_text()

    assert content, "Workflow file is empty"
    assert "name:" in content, "Workflow missing name"
    assert "jobs:" in content, "Workflow missing jobs"


def test_workflow_has_schedule() -> None:
    """Test that workflow has scheduled trigger."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    content = workflow_file.read_text()

    assert "schedule:" in content, "Workflow missing schedule trigger"
    assert "cron:" in content, "Workflow missing cron schedule"


def test_workflow_has_fetch_step() -> None:
    """Test that workflow has fetch-documents step."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    content = workflow_file.read_text()

    assert "monitor:" in content, "Workflow missing monitor job"
    assert "steps:" in content, "Workflow missing steps"
    assert "fetch" in content.lower(), "Workflow missing fetch step"


def test_workflow_has_commit_step() -> None:
    """Test that workflow has commit step."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    content = workflow_file.read_text()

    assert "commit" in content.lower(), "Workflow missing commit step"


def test_workflow_has_secret_references() -> None:
    """Test that workflow references secrets."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    with open(workflow_file) as f:
        content = f.read()

    # Check for secret references
    assert "secrets." in content or "SLACK_WEBHOOK" in content, "Workflow missing secret references"


def test_secrets_configuration_docs_exist() -> None:
    """Test that secrets setup documentation exists."""
    secrets_doc = Path("docs/committee-monitoring-secrets.md")
    assert secrets_doc.exists(), "Secrets configuration guide not found"

    content = secrets_doc.read_text()
    assert "CORDIS_SLACK_WEBHOOK" in content, "Secrets doc missing SLACK_WEBHOOK"
    assert "GH_TOKEN" in content, "Secrets doc missing GH_TOKEN"


def test_monitoring_guide_references_workflow() -> None:
    """Test that main guide references automated workflow."""
    guide = Path("docs/committee-monitoring.md")
    assert guide.exists(), "Committee monitoring guide not found"

    content = guide.read_text(encoding="utf-8")
    assert "GitHub Actions" in content or "workflow" in content, "Guide missing workflow reference"
    assert "06:00" in content or "scheduled" in content.lower(), "Guide missing schedule info"
