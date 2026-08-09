"""Command-line interface for CORDIS data collection."""

import sys
from pathlib import Path

import click

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
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: data/calls.json)",
)
def fetch_calls(full_history: bool, output: str | None) -> None:
    """Fetch open/forthcoming/closed EU grant calls."""
    try:
        fetcher = CallsFetcher()
        output_path = Path(output) if output else None
        fetcher.fetch(output_path=output_path, full_history=full_history)
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
def fetch_projects(years: int | None, output: str | None, calls: str | None) -> None:
    """Fetch awarded projects and enrich with CORDIS data."""
    try:
        fetcher = ProjectsFetcher()
        output_path = Path(output) if output else None
        calls_path = Path(calls) if calls else None
        fetcher.fetch(
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
    """Display metadata about fetched data."""
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


if __name__ == "__main__":  # pragma: no cover
    main()
