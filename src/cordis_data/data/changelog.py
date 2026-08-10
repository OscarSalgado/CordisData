"""Change detection and changelog generation for call updates."""

from dataclasses import dataclass, field as dataclass_field, asdict
from datetime import UTC, datetime
from typing import Any, Optional

RELEVANT_FIELDS = {
    "callStatus",
    "deadline",
    "title",
    "budgetMin",
    "budgetMax",
    "expectedGrants",
    "keywords",
    "actionType",
    "programme",
    "cluster",
    "description",
    "objectives",
    "submissionProcedure",
    "callTitle",
    "deadlineModel",
    "crossCuttingPriorities",
    "typesOfAction",
    "topicConditions",
    "supportInfo",
    "h2020_related",
}


@dataclass
class ChangeEvent:
    """Represents a single change event in the changelog."""

    reference: str
    topicId: str
    event_type: str
    detected_at: str
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    snapshot: Optional[dict[str, Any]] = None
    snapshot_after: Optional[dict[str, Any]] = None
    changed_fields: list[str] = dataclass_field(default_factory=list)
    changes: Optional[dict[str, dict[str, Any]]] = None
    reason: Optional[str] = None
    days_overdue: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


def _get_snapshot_subset(call: dict[str, Any]) -> dict[str, Any]:
    """Extract only relevant fields from a call record."""
    return {k: v for k, v in call.items() if k in RELEVANT_FIELDS}


def detect_changes(
    existing_calls: list[dict[str, Any]],
    merged_calls: dict[str, dict[str, Any]],
) -> list[ChangeEvent]:
    """Detect changes between existing and merged calls.

    Args:
        existing_calls: Previously fetched calls (list)
        merged_calls: Merged state (dict keyed by reference/topicId)

    Returns:
        List of ChangeEvent objects
    """
    def call_key(c: dict[str, Any]) -> str:
        """Get unique key for a call (reference or topicId)."""
        return c.get("reference") or c["topicId"]

    existing_by_key = {call_key(c): c for c in existing_calls}
    events: list[ChangeEvent] = []

    for key, merged_call in merged_calls.items():
        if key not in existing_by_key:
            # NEW call
            events.append(
                ChangeEvent(
                    reference=merged_call.get("reference", ""),
                    topicId=merged_call.get("topicId", ""),
                    event_type="NEW",
                    detected_at=datetime.now(UTC).isoformat() + "Z",
                    snapshot=_get_snapshot_subset(merged_call),
                )
            )
        else:
            existing_call = existing_by_key[key]

            # Detect specific field changes
            changed_fields = []
            changes: dict[str, dict[str, Any]] = {}

            for field_name in RELEVANT_FIELDS:
                old_val = existing_call.get(field_name)
                new_val = merged_call.get(field_name)

                if old_val != new_val:
                    changed_fields.append(field_name)
                    changes[field_name] = {"old_value": old_val, "new_value": new_val}

            if not changed_fields:
                continue  # No relevant changes

            # Categorize the change
            if "callStatus" in changed_fields and len(changed_fields) == 1:
                events.append(
                    ChangeEvent(
                        reference=merged_call.get("reference", ""),
                        topicId=merged_call.get("topicId", ""),
                        event_type="STATUS_CHANGED",
                        detected_at=datetime.now(UTC).isoformat() + "Z",
                        field="callStatus",
                        old_value=existing_call.get("callStatus"),
                        new_value=merged_call.get("callStatus"),
                        snapshot_after=_get_snapshot_subset(merged_call),
                    )
                )
            elif len(changed_fields) == 1:
                # Single field change
                field_name = changed_fields[0]
                events.append(
                    ChangeEvent(
                        reference=merged_call.get("reference", ""),
                        topicId=merged_call.get("topicId", ""),
                        event_type="FIELD_CHANGED",
                        detected_at=datetime.now(UTC).isoformat() + "Z",
                        field=field_name,
                        old_value=existing_call.get(field_name),
                        new_value=merged_call.get(field_name),
                        snapshot_after=_get_snapshot_subset(merged_call),
                    )
                )
            else:
                # Multiple fields changed
                events.append(
                    ChangeEvent(
                        reference=merged_call.get("reference", ""),
                        topicId=merged_call.get("topicId", ""),
                        event_type="METADATA_UPDATED",
                        detected_at=datetime.now(UTC).isoformat() + "Z",
                        changed_fields=changed_fields,
                        changes=changes,
                        snapshot_after=_get_snapshot_subset(merged_call),
                    )
                )

    return events


def generate_changelog(
    existing_calls: list[dict[str, Any]],
    merged_calls: dict[str, dict[str, Any]],
    marked_closed: int,
) -> dict[str, Any]:
    """Generate changelog dict from fetch results.

    Args:
        existing_calls: Previously fetched calls
        merged_calls: Merged state after fetch
        marked_closed: Number of calls auto-closed due to deadline

    Returns:
        Changelog dict with metadata and events
    """
    events = detect_changes(existing_calls, merged_calls)

    # Count event types
    new_count = sum(1 for e in events if e.event_type == "NEW")
    changed_count = sum(1 for e in events if e.event_type != "NEW")

    return {
        "fetch_date": datetime.now(UTC).date().isoformat(),
        "fetch_timestamp": datetime.now(UTC).isoformat() + "Z",
        "total_calls": len(merged_calls),
        "summary": {
            "total_calls": len(merged_calls),
            "new": new_count,
            "changed": changed_count,
            "auto_closed": marked_closed,
        },
        "events": [e.to_dict() for e in events],
    }


def generate_compact_changelog_calls(
    existing_calls: list[dict[str, Any]],
    merged_calls: dict[str, dict[str, Any]],
    marked_closed: int,
) -> dict[str, Any]:
    """Generate compact changelog for calls (no snapshots).

    Args:
        existing_calls: Previously fetched calls
        merged_calls: Merged state after fetch
        marked_closed: Number of calls auto-closed due to deadline

    Returns:
        Compact changelog dict with minimal event data
    """
    events = detect_changes(existing_calls, merged_calls)
    compact_events: list[dict[str, Any]] = []

    for event in events:
        if event.event_type == "NEW":
            compact_events.append({
                "type": "NEW",
                "topicId": event.topicId,
                "name": event.reference,
            })
        elif event.event_type == "STATUS_CHANGED":
            compact_events.append({
                "type": "STATUS_CHANGED",
                "topicId": event.topicId,
                "name": event.reference,
                "from": event.old_value,
                "to": event.new_value,
            })
        elif event.event_type in ("FIELD_CHANGED", "METADATA_UPDATED"):
            compact_events.append({
                "type": "METADATA_UPDATED",
                "topicId": event.topicId,
                "name": event.reference,
                "changed_fields": event.changed_fields,
            })

    new_count = sum(1 for e in events if e.event_type == "NEW")
    changed_count = sum(1 for e in events if e.event_type != "NEW")

    return {
        "date": datetime.now(UTC).date().isoformat(),
        "summary": {
            "new": new_count,
            "changed": changed_count,
            "auto_closed": marked_closed,
        },
        "events": compact_events,
    }


def generate_compact_changelog_documents(
    existing_docs: list[dict[str, Any]],
    merged_docs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Generate compact changelog for documents (no snapshots).

    Args:
        existing_docs: Previously fetched documents
        merged_docs: Merged state after fetch

    Returns:
        Compact changelog dict with minimal event data
    """
    existing_by_ref = {doc.get("documentReference"): doc for doc in existing_docs}
    compact_events: list[dict[str, Any]] = []
    new_count = 0
    changed_count = 0

    for doc_ref, merged_doc in merged_docs.items():
        if doc_ref not in existing_by_ref:
            # NEW document
            compact_events.append({
                "type": "NEW",
                "documentReference": doc_ref,
                "title": merged_doc.get("title", ""),
                "committee": merged_doc.get("committeeCode", ""),
            })
            new_count += 1
        else:
            # Check if attachments changed
            existing_doc = existing_by_ref[doc_ref]
            existing_attachments = {a["id"]: a for a in existing_doc.get("attachments", [])}
            merged_attachments = {a["id"]: a for a in merged_doc.get("attachments", [])}

            for att_id, att in merged_attachments.items():
                if att_id not in existing_attachments:
                    # NEW attachment
                    compact_events.append({
                        "type": "ATTACHMENT_ADDED",
                        "documentReference": doc_ref,
                        "title": merged_doc.get("title", ""),
                        "committee": merged_doc.get("committeeCode", ""),
                        "attachment_id": att_id,
                        "filename": att.get("filename", ""),
                    })
                    changed_count += 1
                    break  # Count document as changed once per session

            # Check for metadata changes (non-attachment)
            if not changed_count or doc_ref not in [e.get("documentReference") for e in compact_events if e["type"] == "ATTACHMENT_ADDED"]:
                for key in ["title", "updateDate"]:
                    if existing_doc.get(key) != merged_doc.get(key):
                        compact_events.append({
                            "type": "METADATA_UPDATED",
                            "documentReference": doc_ref,
                            "title": merged_doc.get("title", ""),
                            "committee": merged_doc.get("committeeCode", ""),
                            "changed_fields": [key],
                        })
                        changed_count += 1
                        break

    return {
        "date": datetime.now(UTC).date().isoformat(),
        "summary": {
            "new": new_count,
            "changed": changed_count,
        },
        "events": compact_events,
    }
