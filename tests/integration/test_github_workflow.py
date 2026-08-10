"""Tests for GitHub Actions workflow integration."""

from pathlib import Path


def test_workflow_file_exists() -> None:
    """Test that monitor-committees workflow file exists."""
    workflow_file = Path(".github/workflows/monitor-committees.yml")
    assert workflow_file.exists(), "Workflow file not found"


def test_workflow_valid_yaml() -> None:
    """Test that workflow file is valid YAML."""
    import yaml

    workflow_file = Path(".github/workflows/monitor-committees.yml")
    with open(workflow_file) as f:
        config = yaml.safe_load(f)

    assert config is not None, "Workflow YAML is invalid"
    assert "name" in config, "Workflow missing name"
    assert "jobs" in config, "Workflow missing jobs"


def test_workflow_has_schedule() -> None:
    """Test that workflow has scheduled trigger."""
    import yaml

    workflow_file = Path(".github/workflows/monitor-committees.yml")
    with open(workflow_file) as f:
        config = yaml.safe_load(f)

    triggers = config.get("on", {})
    assert "schedule" in triggers, "Workflow missing schedule trigger"

    schedule = triggers["schedule"]
    assert len(schedule) > 0, "Workflow schedule is empty"


def test_workflow_has_fetch_step() -> None:
    """Test that workflow has fetch-documents step."""
    import yaml

    workflow_file = Path(".github/workflows/monitor-committees.yml")
    with open(workflow_file) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    assert "monitor" in jobs, "Workflow missing monitor job"

    job = jobs["monitor"]
    steps = job.get("steps", [])

    step_names = [step.get("name", "").lower() for step in steps]
    assert any("fetch" in name for name in step_names), "Workflow missing fetch step"


def test_workflow_has_commit_step() -> None:
    """Test that workflow has commit step."""
    import yaml

    workflow_file = Path(".github/workflows/monitor-committees.yml")
    with open(workflow_file) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    job = jobs["monitor"]
    steps = job.get("steps", [])

    step_names = [step.get("name", "").lower() for step in steps]
    assert any("commit" in name for name in step_names), "Workflow missing commit step"


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

    content = guide.read_text()
    assert "GitHub Actions" in content or "workflow" in content, "Guide missing workflow reference"
    assert "06:00" in content or "scheduled" in content.lower(), "Guide missing schedule info"
