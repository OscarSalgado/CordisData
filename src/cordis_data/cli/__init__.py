"""Command-line interface for CORDIS data collection."""

import sys
from pathlib import Path

import click

from cordis_data.cli.explorer import explorer_cli
from cordis_data.cli.monitor import monitor
from cordis_data.data.closed_calls import ClosedCallsFetcher
from cordis_data.data.metadata import load_metadata
from cordis_data.data.open_calls import OpenCallsFetcher
from cordis_data.data.projects import ProjectsFetcher


@click.group()
def main() -> None:
    """CORDIS Data: Collect and manage EU research funding data."""
    pass


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Skip freshness check and fetch unconditionally",
)
def fetch_calls(force: bool) -> None:
    """Fetch all EU grant calls (open and closed) from SEDIA API.

    Orchestrates both OpenCallsFetcher (active opportunities) and ClosedCallsFetcher
    (closed calls for project discovery), writing results to data/calls/open.jsonl.gz
    and data/calls/closed.jsonl.gz respectively.

    By default, fetches calls published in the relevant time windows (9 months for open,
    all history for closed) and merges into existing data. Use --force to skip freshness
    checks and fetch unconditionally.

    Also writes daily changelogs to data/changelog/open/YYYY-MM-DD.json and
    data/changelog/closed/YYYY-MM-DD.json recording changes, and prunes old entries.

    Args:
        force: If True, skip freshness checks and always fetch

    Exits with code 1 if either fetch fails.
    """
    try:
        open_fetcher = OpenCallsFetcher()
        closed_fetcher = ClosedCallsFetcher()

        click.echo("Fetching open/forthcoming calls...", err=True)
        open_fetcher.main(force=force)

        click.echo("Fetching closed calls...", err=True)
        closed_fetcher.main(force=force)

        click.echo("Done.", err=True)
    except Exception as e:
        click.echo(f"Error fetching calls: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Skip freshness check and fetch unconditionally",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/calls.open.json)",
)
def fetch_open_calls(force: bool, output: str | None) -> None:
    """Fetch open/forthcoming EU grant calls from SEDIA API.

    Fetches calls published in the last 9 months (rolling window) and merges
    into existing data. Use --force to skip freshness check and fetch
    unconditionally.

    Writes calls.open.json and daily changelog to data/changelog/open/YYYY-MM-DD.json

    Args:
        force: If True, skip freshness check and always fetch
        output: Output file path (default: data/calls.open.json)

    Exits with code 1 if fetch fails.
    """
    try:
        fetcher = OpenCallsFetcher()
        output_path = Path(output) if output else None
        fetcher.main(output_path=output_path, force=force)
    except Exception as e:
        click.echo(f"Error fetching open calls: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Skip freshness check and fetch unconditionally",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/calls.closed.json)",
)
def fetch_closed_calls(force: bool, output: str | None) -> None:
    """Fetch closed EU grant calls from SEDIA API (for project discovery).

    Fetches closed calls from dataset start to 3 months ago and merges
    into existing data. Use --force to skip freshness check and fetch
    unconditionally.

    Writes calls.closed.json and daily changelog to data/changelog/closed/YYYY-MM-DD.json

    Args:
        force: If True, skip freshness check and always fetch
        output: Output file path (default: data/calls.closed.json)

    Exits with code 1 if fetch fails.
    """
    try:
        fetcher = ClosedCallsFetcher()
        output_path = Path(output) if output else None
        fetcher.main(output_path=output_path, force=force)
    except Exception as e:
        click.echo(f"Error fetching closed calls: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/projects.json)",
)
@click.option(
    "--calls-closed",
    type=click.Path(),
    default=None,
    help="Path to calls.closed.json (default: data/calls.closed.json)",
)
def fetch_projects(
    output: str | None, calls_closed: str | None
) -> None:
    """Fetch awarded projects for closed calls and enrich with CORDIS data.

    Fetches projects from SEDIA for closed calls with deadline within last 1 year
    (rolling window), deduplicates by (topicId, projectId), and enriches with
    CORDIS data. Appends new projects to existing projects.json.

    Args:
        output: Output file path (default: data/projects.json)
        calls_closed: Path to calls.closed.json (default: data/calls.closed.json)

    Exits with code 1 if fetch fails.
    """
    try:
        fetcher = ProjectsFetcher()
        output_path = Path(output) if output else None
        calls_path = Path(calls_closed) if calls_closed else None
        fetcher.main(
            output_path=output_path,
            calls_path=calls_path,
        )
    except Exception as e:
        click.echo(f"Error fetching projects: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--data-dir",
    type=click.Path(),
    default=None,
    help="Data directory (default: ./data)",
)
def status(data_dir: str | None) -> None:
    """Display metadata about fetched data and freshness status.

    Shows last fetch timestamps and TTL (time-to-live) for open/closed calls
    and projects data, allowing users to check if a fresh fetch is needed.

    Args:
        data_dir: Data directory path (default: ./data)

    Exits with code 1 if metadata cannot be read.
    """
    try:
        project_root = Path(data_dir or "data")
        metadata_path = project_root / ".metadata.json"
        metadata = load_metadata(metadata_path)

        click.echo("=== CORDIS Data Status ===")
        click.echo("\nOpen Calls (active opportunities):")
        click.echo(f"  Last fetched: {metadata.get('calls_open_fetched_at', 'Never')}")
        click.echo(f"  Freshness TTL: {metadata.get('calls_open_freshness_ttl_days', 3)} days")

        click.echo("\nClosed Calls (for project discovery):")
        click.echo(f"  Last fetched: {metadata.get('calls_closed_fetched_at', 'Never')}")
        click.echo(f"  Freshness TTL: {metadata.get('calls_closed_freshness_ttl_days', 7)} days")

        click.echo("\nProjects:")
        click.echo(f"  Last fetched: {metadata.get('projects_fetched_at', 'Never')}")
        click.echo(f"  Topics processed: {metadata.get('projects_topics_processed_count', 0)}")
        click.echo(f"  Topics without projects: {metadata.get('projects_topics_without_projects_count', 0)}")
        click.echo(f"  Rolling window: {metadata.get('projects_rolling_window_days', 365)} days")
        click.echo(f"  Freshness TTL: {metadata.get('projects_freshness_ttl_days', 30)} days")
    except Exception as e:
        click.echo(f"Error reading status: {e}", err=True)
        sys.exit(1)


# Add subgroups
main.add_command(explorer_cli, name="explore")
main.add_command(monitor, name="monitor")


if __name__ == "__main__":  # pragma: no cover
    main()
