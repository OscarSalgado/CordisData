"""CLI explorer for researchers to search and view funding calls and projects."""

import json
from pathlib import Path
from typing import Any, Optional

import click


class DataExplorer:
    """In-memory explorer for calls and projects data."""

    def __init__(self, data_dir: Path) -> None:
        """Initialize explorer with data directory."""
        self.data_dir = Path(data_dir)
        self.calls: list[dict[str, Any]] = []
        self.projects: list[dict[str, Any]] = []
        self.calls_by_id = {}
        self.projects_by_id = {}
        self.calls_by_cluster: dict[str, list[dict[str, Any]]] = {}

    def load(self) -> bool:
        """Load calls and projects data into memory."""
        try:
            calls_file = self.data_dir / "calls.json"
            projects_file = self.data_dir / "projects.json"

            if calls_file.exists():
                with open(calls_file) as f:
                    self.calls = json.load(f)
                    for call in self.calls:
                        self.calls_by_id[call.get("topicId", "")] = call
                        cluster = call.get("cluster", "")
                        if cluster not in self.calls_by_cluster:
                            self.calls_by_cluster[cluster] = []
                        self.calls_by_cluster[cluster].append(call)

            if projects_file.exists():
                with open(projects_file) as f:
                    self.projects = json.load(f)
                    for proj in self.projects:
                        self.projects_by_id[proj.get("projectId", "")] = proj

            return len(self.calls) > 0 and len(self.projects) > 0
        except Exception:
            return False

    def search_calls(
        self,
        cluster: Optional[str] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        budget_min: Optional[int] = None,
        deadline_after: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Search calls with AND logic for all filters."""
        results = self.calls

        if cluster:
            results = [c for c in results if c.get("cluster") == cluster]

        if keyword:
            keyword_lower = keyword.lower()
            results = [
                c
                for c in results
                if keyword_lower in (c.get("title", "").lower() or "")
                or keyword_lower in (c.get("keywords", "").lower() or "")
                or keyword_lower in (c.get("description", "").lower() or "")
            ]

        if status:
            results = [c for c in results if c.get("callStatus") == status]

        if budget_min:
            results = [c for c in results if (c.get("budgetMax") or 0) >= budget_min]

        if deadline_after:
            results = [c for c in results if (c.get("deadline") or "") >= deadline_after]

        return results

    def search_projects(self, team: Optional[str] = None) -> list[dict[str, Any]]:
        """Search projects by team."""
        if not team:
            return self.projects

        team_lower = team.lower()
        return [
            p
            for p in self.projects
            if any(
                team_lower in (ent.get("name", "").lower() or "")
                for ent in p.get("legalEntityNames", [])
            )
        ]

    def get_call(self, call_id: str) -> Optional[dict[str, Any]]:
        """Get call by topicId."""
        return self.calls_by_id.get(call_id)

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Get project by projectId."""
        return self.projects_by_id.get(project_id)

    def get_call_winners(self, call_id: str) -> list[dict[str, Any]]:
        """Get projects that won a specific call."""
        return [p for p in self.projects if p.get("topicId") == call_id]

    def format_table(self, data: list[dict[str, Any]], columns: list[str]) -> str:
        """Format data as simple text table."""
        if not data:
            return "No results"
        rows = [[str(row.get(col, "")) for col in columns] for row in data]
        header = " | ".join(columns)
        lines = [header, "-" * len(header)]
        for row in rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)

    def format_json(self, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, ensure_ascii=False)


# Global explorer instance
explorer: Optional[DataExplorer] = None


def get_explorer() -> DataExplorer:
    """Get or create explorer instance."""
    global explorer
    if explorer is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        explorer = DataExplorer(project_root / "data")
        if not explorer.load():
            click.echo("Error: Could not load data files", err=True)
            raise click.Abort()
    return explorer


@click.group()
def explorer_cli() -> None:
    """Data explorer for researchers."""
    pass


@explorer_cli.command()
@click.option("--cluster", help="Filter by cluster (e.g., CL1, CL2)")
@click.option("--keyword", help="Filter by keyword in title/description")
@click.option("--status", help="Filter by status (open, closed, etc)")
@click.option("--budget-min", type=int, help="Minimum budget")
@click.option("--deadline-after", help="Deadline after date (YYYY-MM-DD)")
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
@click.option("--limit", type=int, default=50)
def search_calls(
    cluster: Optional[str],
    keyword: Optional[str],
    status: Optional[str],
    budget_min: Optional[int],
    deadline_after: Optional[str],
    format: str,
    limit: int,
) -> None:
    """Search calls by criteria."""
    exp = get_explorer()
    results = exp.search_calls(cluster, keyword, status, budget_min, deadline_after)

    if format == "json":
        click.echo(exp.format_json(results[:limit]))
    else:
        columns = ["topicId", "title", "cluster", "deadline", "callStatus", "budgetMax"]
        click.echo(exp.format_table(results[:limit], columns))
        if len(results) > limit:
            click.echo(f"\n[Showing {limit}/{len(results)} results]")


@explorer_cli.command()
@click.argument("call_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="json")
def view_call(call_id: str, format: str) -> None:
    """View call details."""
    exp = get_explorer()
    call = exp.get_call(call_id)

    if not call:
        click.echo(f"Call not found: {call_id}", err=True)
        return

    if format == "json":
        click.echo(exp.format_json(call))
    else:
        click.echo(f"Topic ID: {call.get('topicId')}")
        click.echo(f"Title: {call.get('title')}")
        click.echo(f"Status: {call.get('callStatus')}")
        click.echo(f"Deadline: {call.get('deadline')}")
        click.echo(f"Budget: €{call.get('budgetMin')}-{call.get('budgetMax')}")
        click.echo(f"Cluster: {call.get('cluster')}")

        # Winners
        winners = exp.get_call_winners(call_id)
        if winners:
            click.echo(f"\nWinners ({len(winners)} projects):")
            for proj in winners[:5]:
                click.echo(f"  - {proj.get('acronym')} ({proj.get('projectId')})")
            if len(winners) > 5:
                click.echo(f"  ... and {len(winners) - 5} more")


@explorer_cli.command()
@click.option("--team", help="Filter by team/organisation")
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
@click.option("--limit", type=int, default=50)
def search_projects(team: Optional[str], format: str, limit: int) -> None:
    """Search projects."""
    exp = get_explorer()
    results = exp.search_projects(team)

    if format == "json":
        click.echo(exp.format_json(results[:limit]))
    else:
        columns = ["projectId", "acronym", "topicId", "status", "euContributionAmount"]
        click.echo(exp.format_table(results[:limit], columns))
        if len(results) > limit:
            click.echo(f"\n[Showing {limit}/{len(results)} results]")


@explorer_cli.command()
@click.argument("project_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="json")
def view_project(project_id: str, format: str) -> None:
    """View project details with H2020 lineage."""
    exp = get_explorer()
    proj = exp.get_project(project_id)

    if not proj:
        click.echo(f"Project not found: {project_id}", err=True)
        return

    if format == "json":
        click.echo(exp.format_json(proj))
    else:
        click.echo(f"Project ID: {proj.get('projectId')}")
        click.echo(f"Acronym: {proj.get('acronym')}")
        click.echo(f"Status: {proj.get('status')}")
        click.echo(f"Budget: €{proj.get('euContributionAmount')}")

        # H2020 lineage
        h2020_rel = proj.get("h2020_related")
        if h2020_rel:
            click.echo(f"\nH2020 Related (confidence: {h2020_rel.get('matchConfidence')}):")
            click.echo(f"  Project: {h2020_rel.get('acronym')} ({h2020_rel.get('projectId')})")
            click.echo(f"  Strategy: {h2020_rel.get('matchStrategy')}")
