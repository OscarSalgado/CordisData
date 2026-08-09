"""Utility functions for data transformation and merging."""

import datetime
import json
import re
from typing import Any, Optional


def normalize_date(d: Optional[str]) -> str:
    """Normalize date strings to YYYY-MM-DD format.

    Args:
        d: Date string in various formats or None

    Returns:
        Normalized YYYY-MM-DD string, or empty string if invalid
    """
    if not d:
        return ""
    if "T" in d:
        d = d.split("T")[0]
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    for fmt in ["%d %B %Y", "%d %b %Y", "%B %d, %Y"]:
        try:
            return datetime.datetime.strptime(d.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return d


def extract_budget(
    metadata: dict[str, Any], identifier: str
) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Extract budget info for a topic from its call's budgetOverview.

    The budgetOverview describes every topic/action under the call, keyed by an
    internal id unrelated to the topic's own identifier. The only reliable way
    to find the right entry is matching its "action" text, which starts with
    "<identifier> - ". Returns (min, max, expected_grants), each None if the
    field is absent, unparseable, has no matching entry, or the matched entry
    has all-zero min/max (observed on ~43% of calls, treated as "not specified").

    Args:
        metadata: Metadata dict from API response
        identifier: Topic identifier to search for

    Returns:
        Tuple of (budget_min, budget_max, expected_grants) or (None, None, None)
    """
    bo_str = (metadata.get("budgetOverview") or [""])[0]
    if not bo_str:
        return None, None, None
    try:
        overview = json.loads(bo_str)
        action_map = overview.get("budgetTopicActionMap", {})
        prefix = f"{identifier} - "
        for entries in action_map.values():
            for entry in entries:
                if entry.get("action", "").startswith(prefix):
                    budget_min = entry.get("minContribution")
                    budget_max = entry.get("maxContribution")
                    if not budget_min and not budget_max:
                        return None, None, None
                    return budget_min, budget_max, entry.get("expectedGrants")
    except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
        pass
    return None, None, None


def parse_action_type(toa: Optional[str]) -> str:
    """Parse action type string into a normalized code.

    Args:
        toa: Type of action string from API

    Returns:
        Normalized action type code (RIA, IA, CSA, etc.) or empty string
    """
    if not toa:
        return ""
    if "RIA" in toa or "Research and Innovation" in toa:
        return "RIA"
    if "Innovation Action" in toa and "Research" not in toa:
        return "IA"
    if "CSA" in toa or "Coordination and Support" in toa:
        return "CSA"
    if "PPI" in toa or "Pre-Commercial" in toa:
        return "PPI"
    if any(x in toa.lower() for x in ["cofund", "co-fund"]):
        return "CoFund"
    if "Prize" in toa or "PRIZE" in toa:
        return "Prize"
    if "MSCA" in toa and "SE" in toa:
        return "MSCA-SE"
    if "MSCA" in toa:
        return "MSCA"
    if "Lump Sum" in toa or "lump" in toa.lower():
        return "Grant"
    if "Grant" in toa:
        return "Grant"
    return toa.split()[0] if toa else ""


def merge_calls(
    existing_calls: list[dict[str, Any]],
    new_calls: list[dict[str, Any]],
    full_history: bool = False,
) -> dict[str, dict[str, Any]]:
    """Merge new_calls into existing_calls by reference (topicId fallback).

    When full_history is true, existing_calls is ignored entirely (a full
    replace). Otherwise, existing records are kept and new records are overlaid.

    Args:
        existing_calls: Previously fetched calls
        new_calls: Newly fetched calls
        full_history: If True, replace existing entirely

    Returns:
        Dict keyed by reference or topicId
    """
    def merge_key(c: dict[str, Any]) -> str:
        return c.get("reference") or c["topicId"]

    if full_history:
        return {merge_key(c): c for c in new_calls}

    merged = {merge_key(c): c for c in existing_calls}
    merged.update({merge_key(c): c for c in new_calls})
    return merged


def merge_projects(
    existing_projects: list[dict[str, Any]],
    new_projects: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Merge new_projects into existing_projects by projectId.

    New data wins on matching key. Re-running the script overlays freshly-
    fetched records onto what's already stored, so a project whose CORDIS
    enrichment failed on one run can self-heal on a later run.

    Args:
        existing_projects: Previously fetched projects
        new_projects: Newly fetched projects

    Returns:
        Dict keyed by projectId
    """
    merged = {p["projectId"]: p for p in existing_projects}
    merged.update({p["projectId"]: p for p in new_projects})
    return merged


def summarize_changes(
    existing_by_key: dict[str, dict[str, Any]],
    merged_by_key: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """Count added/changed/unchanged records between existing and merged.

    Args:
        existing_by_key: Keyed collection of existing records
        merged_by_key: Keyed collection after merge

    Returns:
        Dict with 'added', 'changed', 'unchanged' counts
    """
    added = changed = unchanged = 0
    for key, record in merged_by_key.items():
        if key not in existing_by_key:
            added += 1
        elif existing_by_key[key] != record:
            changed += 1
        else:
            unchanged += 1
    return {"added": added, "changed": changed, "unchanged": unchanged}
