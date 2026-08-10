"""CLI commands for committee monitoring."""

from pathlib import Path

import click

from cordis_data.data.committees.client import CommitteeDocumentsClient
from cordis_data.data.committees.config import CommitteeConfig
from cordis_data.data.committees.discovery import CommitteeDiscovery
from cordis_data.data.committees.fetcher import CommitteeDocumentsFetcher


@click.group()
def monitor() -> None:
    """Monitor EU committee documents."""
    pass


@monitor.command()
@click.argument("code")
@click.argument("name", default="")
def add_committee(code: str, name: str) -> None:
    """Add a committee to monitor."""
    try:
        client = CommitteeDocumentsClient()
        committees = client.list_committees()
        committee = next((c for c in committees if c.get("code") == code), None)
        if not committee:
            click.echo(f"❌ Committee {code} not found", err=True)
            raise click.Abort()

        actual_name = name or committee.get("title", code)
        CommitteeConfig.add_committee(code, actual_name)
        click.echo(f"✓ Added committee {code}: {actual_name}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@monitor.command()
def list_committees() -> None:
    """List monitored committees."""
    config = CommitteeConfig.load()
    committees = config.get("committees", [])

    if not committees:
        click.echo("No committees configured")
        return

    for c in committees:
        status = "✓" if c.get("enabled", True) else "✗"
        click.echo(f"{status} {c['code']}: {c.get('name', 'Unknown')}")


@monitor.command()
@click.argument("code")
def remove_committee(code: str) -> None:
    """Remove a committee from monitoring."""
    CommitteeConfig.remove_committee(code)
    click.echo(f"✓ Removed committee {code}")


@monitor.command()
def config_show() -> None:
    """Show current configuration."""
    config = CommitteeConfig.load()
    import json

    click.echo(json.dumps(config, indent=2, ensure_ascii=False))


@monitor.command()
@click.option("--slack", help="Slack webhook URL")
@click.option("--email", help="Email address")
@click.option("--github-issues", is_flag=True, help="Enable GitHub Issues alerts")
def config_set(slack: str, email: str, github_issues: bool) -> None:
    """Configure alert settings."""
    config = CommitteeConfig.load()

    if slack:
        config["alerts"]["slack_webhook"] = slack
        click.echo("✓ Slack webhook configured")

    if email:
        config["alerts"]["email"] = email
        click.echo("✓ Email configured")

    if github_issues:
        config["alerts"]["github_issues"] = True
        click.echo("✓ GitHub Issues alerts enabled")

    CommitteeConfig.save(config)


@monitor.command()
@click.option("--window", default=90, help="Days to look back (default: 90)")
def fetch(window: int) -> None:
    """Fetch committee documents now."""
    config = CommitteeConfig.load()
    committees = [c["code"] for c in config.get("committees", [])]

    if not committees:
        click.echo("❌ No committees configured. Use 'add-committee' first.", err=True)
        raise click.Abort()

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    output_path = project_root / "data" / "committees" / "documents.json"

    fetcher = CommitteeDocumentsFetcher()
    new_docs = fetcher.main(committees, output_path, window_days=window)
    click.echo(f"✓ Fetch complete: {len(new_docs)} new documents")


@monitor.command()
@click.option("--dry-run", is_flag=True, help="Show what would happen, don't update log")
@click.option("--clear-log", is_flag=True, help="Reset discovery log before running")
def discover(dry_run: bool, clear_log: bool) -> None:
    """Discover new EU committees from the register."""
    try:
        discovery = CommitteeDiscovery()

        if clear_log:
            click.echo("Clearing discovery log...")
            discovery.DISCOVERY_LOG_PATH.unlink(missing_ok=True)

        click.echo("Connecting to EU API...")
        result = discovery.discover()

        click.echo("Comparing with local config...")
        click.echo("\nResults:")
        click.echo(f"  Total committees: {result.total_committees}")
        click.echo(f"  Currently monitored: {result.currently_monitored}")
        click.echo(f"  New committees: {len(result.new_committees)}")

        if result.has_new():
            click.echo("\nNew committees found:")
            for committee in result.new_committees:
                click.echo(f"  {committee['code']}: {committee.get('title', 'Unknown')}")

            if not dry_run:
                click.echo("\nDiscovery log updated.")
                click.echo("Next steps:")
                click.echo("  1. Review new committees")
                click.echo("  2. Add relevant ones: cordis-data monitor add-committee <code> '<title>'")
        else:
            click.echo("No new committees found.")

        if result.has_new():
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
