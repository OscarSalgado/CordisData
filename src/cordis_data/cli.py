"""Command-line interface for CORDIS data collection."""

import sys
from pathlib import Path

import click

from cordis_data.cli.explorer import explorer_cli
from cordis_data.data.calls import CallsFetcher
from cordis_data.data.metadata import load_metadata
from cordis_data.data.projects import ProjectsFetcher


@click.group()
def main() -> None:
    """CORDIS Data: Collect and manage EU research funding data."""
    pass


@main.command()
@click.option(
    "--full-history",
    is_flag=True,
    help="Fetch complete dataset with no date limit (replaces existing)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip freshness check and fetch unconditionally",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/calls.json)",
)
def fetch_calls(full_history: bool, force: bool, output: str | None) -> None:
    """Fetch open/forthcoming/closed EU grant calls from SEDIA API.

    By default, fetches calls published in the last 90 days and merges into
    existing data. Use --full-history to fetch complete dataset and replace.
    Use --force to skip freshness check and fetch unconditionally.

    Also writes a daily changelog to data/changelog/YYYY-MM-DD.json recording
    NEW/STATUS_CHANGED/FIELD_CHANGED/METADATA_UPDATED events, and prunes
    changelog files older than 90 days.

    Args:
        full_history: If True, fetch complete dataset (no date limit)
        force: If True, skip freshness check and always fetch
        output: Output file path (default: data/calls.json)

    Exits with code 1 if fetch fails.
    """
    try:
        fetcher = CallsFetcher()
        output_path = Path(output) if output else None
        fetcher.main(output_path=output_path, full_history=full_history, force=force)
    except Exception as e:
        click.echo(f"Error fetching calls: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--years",
    type=int,
    default=None,
    help="Only fetch projects for calls closed in last N years",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/projects.json)",
)
@click.option(
    "--calls",
    type=click.Path(),
    default=None,
    help="Path to calls.json (default: data/calls.json)",
)
def fetch_projects(
    years: int | None, output: str | None, calls: str | None
) -> None:
    """Fetch awarded projects for closed calls and enrich with CORDIS data.

    Fetches projects from SEDIA for all closed calls, then enriches with
    objective and DOI from CORDIS API using rate limiting (max 2 req/s).
    Checkpoints after every 500 projects to enable resumption on failure.

    Args:
        years: Limit to calls closed within last N years (optional)
        output: Output file path (default: data/projects.json)
        calls: Path to calls.json (default: data/calls.json)

    Exits with code 1 if fetch fails.
    """
    try:
        fetcher = ProjectsFetcher()
        output_path = Path(output) if output else None
        calls_path = Path(calls) if calls else None
        fetcher.main(
            output_path=output_path,
            calls_path=calls_path,
            years=years,
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

    Shows last fetch timestamps and TTL (time-to-live) for calls and projects
    data, allowing users to check if a fresh fetch is needed.

    Args:
        data_dir: Data directory path (default: ./data)

    Exits with code 1 if metadata cannot be read.
    """
    try:
        project_root = Path(data_dir or "data")
        metadata_path = project_root / ".metadata.json"
        metadata = load_metadata(metadata_path)

        click.echo("=== CORDIS Data Status ===")
        click.echo(f"Calls fetched: {metadata.get('calls_fetched_at', 'Never')}")
        click.echo(f"  Freshness TTL: {metadata.get('calls_freshness_ttl_days')} days")
        click.echo(f"Projects fetched: {metadata.get('projects_fetched_at', 'Never')}")
        click.echo(f"  CORDIS enrichment TTL: {metadata.get('projects_freshness_ttl_days')} days")
    except Exception as e:
        click.echo(f"Error reading status: {e}", err=True)
        sys.exit(1)


# Add explorer commands as subgroup
main.add_command(explorer_cli, name="explore")


if __name__ == "__main__":  # pragma: no cover
    main()
