"""Format and create GitHub issues for committee discoveries."""

import subprocess
from datetime import datetime, timezone
from typing import Any, Optional


def format_issue_body(new_committees: list[dict]) -> str:
    """Format committee discoveries as GitHub issue body.

    Args:
        new_committees: List of newly discovered committees

    Returns:
        Formatted markdown for GitHub issue
    """
    if not new_committees:
        return "No new committees to report."

    # Build markdown table
    table = "| Code | Title | EU Register |\n"
    table += "|------|-------|-------------|\n"

    for committee in new_committees:
        code = committee.get("code", "")
        title = committee.get("title", "Unknown")
        register_url = f"https://ec.europa.eu/transparency/comitology-register/screen/committees/{code}"
        table += f"| {code} | {title} | [Link]({register_url}) |\n"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    body = f"""# New EU Committees Discovered

Found {len(new_committees)} new committee(ies) in the EU comitology register:

{table}

## How to Add to Monitoring

To start monitoring a discovered committee, use:

```bash
cordis-data monitor add-committee <CODE> "<TITLE>"
```

**Example:**

```bash
cordis-data monitor add-committee {new_committees[0].get('code', 'C70409')} "{new_committees[0].get('title', 'Example')}"
```

Then run the monitoring fetch:

```bash
cordis-data monitor fetch
```

## More Information

- [EU Comitology Register](https://ec.europa.eu/transparency/comitology-register)
- [Committee Monitoring Guide](https://github.com/OscarSalgado/CordisData/blob/main/docs/committee-monitoring.md)

---
*Discovered: {timestamp}*
*Job: Discovery*
"""

    return body


def create_github_issue(
    title: str,
    body: str,
    labels: Optional[list[str]] = None,
) -> Optional[int]:
    """Create a GitHub issue for discovered committees.

    Args:
        title: Issue title
        body: Issue body (markdown)
        labels: Optional list of labels to apply

    Returns:
        Issue number if successful, None otherwise
    """
    if labels is None:
        labels = ["discovery", "committees", "automated"]

    try:
        # Build gh command
        cmd = ["gh", "issue", "create", "--title", title, "--body", body]

        for label in labels:
            cmd.extend(["--label", label])

        # Create issue
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"Error creating GitHub issue: {result.stderr}")
            return None

        # Extract issue number from output
        # gh returns: https://github.com/owner/repo/issues/123
        output = result.stdout.strip()
        if output.startswith("https://"):
            issue_number = int(output.split("/")[-1])
            return issue_number

        return None

    except subprocess.TimeoutExpired:
        print("Timeout creating GitHub issue")
        return None
    except Exception as e:
        print(f"Exception creating GitHub issue: {e}")
        return None


def mark_discoveries_as_reported(
    discovery_instance: Any,
    committee_codes: list[str],
) -> None:
    """Mark discoveries as reported in GitHub issue.

    Args:
        discovery_instance: CommitteeDiscovery instance
        committee_codes: List of committee codes that were reported
    """
    discovery_instance.mark_as_reported(committee_codes)
