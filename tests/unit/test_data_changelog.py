"""Tests for change detection and changelog generation."""

from cordis_data.data.changelog import (
    detect_changes,
    generate_changelog,
    generate_compact_changelog_calls,
    generate_compact_changelog_documents,
)


class TestDetectChanges:
    """Tests for detect_changes()."""

    def test_all_new(self) -> None:
        """All merged calls are new when existing_calls is empty."""
        merged = {
            "A": {"reference": "A", "topicId": "T-A", "callStatus": "open"},
            "B": {"reference": "B", "topicId": "T-B", "callStatus": "open"},
        }
        events = detect_changes([], merged)
        assert len(events) == 2
        assert all(e.event_type == "NEW" for e in events)

    def test_no_change(self) -> None:
        """No events when merged calls match existing calls exactly."""
        call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "deadline": "2026-01-01"}
        events = detect_changes([call], {"A": dict(call)})
        assert events == []

    def test_mixed_new_and_unchanged(self) -> None:
        """Mix of new and unchanged calls only produces events for new ones."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged = {
            "A": dict(existing_call),
            "B": {"reference": "B", "topicId": "T-B", "callStatus": "open"},
        }
        events = detect_changes([existing_call], merged)
        assert len(events) == 1
        assert events[0].event_type == "NEW"
        assert events[0].reference == "B"

    def test_status_changed(self) -> None:
        """Single callStatus change is classified as STATUS_CHANGED."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged_call = {"reference": "A", "topicId": "T-A", "callStatus": "closed"}
        events = detect_changes([existing_call], {"A": merged_call})
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "STATUS_CHANGED"
        assert event.old_value == "open"
        assert event.new_value == "closed"

    def test_single_field_changed(self) -> None:
        """Single non-status field change is classified as FIELD_CHANGED."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "budgetMin": 1000}
        merged_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "budgetMin": 2000}
        events = detect_changes([existing_call], {"A": merged_call})
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "FIELD_CHANGED"
        assert event.field == "budgetMin"
        assert event.old_value == 1000
        assert event.new_value == 2000

    def test_multiple_fields_changed(self) -> None:
        """Multiple field changes are classified as METADATA_UPDATED."""
        existing_call = {
            "reference": "A", "topicId": "T-A", "callStatus": "open",
            "budgetMin": 1000, "title": "Old Title",
        }
        merged_call = {
            "reference": "A", "topicId": "T-A", "callStatus": "open",
            "budgetMin": 2000, "title": "New Title",
        }
        events = detect_changes([existing_call], {"A": merged_call})
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "METADATA_UPDATED"
        assert set(event.changed_fields) == {"budgetMin", "title"}
        assert event.changes["budgetMin"] == {"old_value": 1000, "new_value": 2000}
        assert event.changes["title"] == {"old_value": "Old Title", "new_value": "New Title"}

    def test_irrelevant_field_change_ignored(self) -> None:
        """Changes to fields outside RELEVANT_FIELDS produce no event."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "portalUrl": "old"}
        merged_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "portalUrl": "new"}
        events = detect_changes([existing_call], {"A": merged_call})
        assert events == []

    def test_missing_field_treated_as_none(self) -> None:
        """A field missing from one side is compared against None."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "deadline": "2026-01-01"}
        events = detect_changes([existing_call], {"A": merged_call})
        assert len(events) == 1
        assert events[0].field == "deadline"
        assert events[0].old_value is None
        assert events[0].new_value == "2026-01-01"

    def test_whitespace_difference_counts_as_change(self) -> None:
        """Whitespace-only differences are treated as changes."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "keywords": "AI, ML"}
        merged_call = {"reference": "A", "topicId": "T-A", "callStatus": "open", "keywords": "AI,ML"}
        events = detect_changes([existing_call], {"A": merged_call})
        assert len(events) == 1
        assert events[0].field == "keywords"


class TestGenerateChangelog:
    """Tests for generate_changelog()."""

    def test_structure_keys(self) -> None:
        """Changelog dict contains all expected top-level keys."""
        merged = {"A": {"reference": "A", "topicId": "T-A", "callStatus": "open"}}
        changelog = generate_changelog([], merged, marked_closed=0)

        assert set(changelog.keys()) == {
            "fetch_date", "fetch_timestamp", "total_calls", "summary", "events",
        }
        assert set(changelog["summary"].keys()) == {"total_calls", "new", "changed", "auto_closed"}

    def test_counts_new_and_changed(self) -> None:
        """Summary counts reflect NEW vs. other event types."""
        existing_call = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged = {
            "A": {"reference": "A", "topicId": "T-A", "callStatus": "closed"},
            "B": {"reference": "B", "topicId": "T-B", "callStatus": "open"},
        }
        changelog = generate_changelog([existing_call], merged, marked_closed=1)

        assert changelog["summary"]["new"] == 1
        assert changelog["summary"]["changed"] == 1
        assert changelog["summary"]["auto_closed"] == 1
        assert changelog["total_calls"] == 2

    def test_snapshot_after_only_relevant_fields(self) -> None:
        """snapshot_after in events only includes RELEVANT_FIELDS."""
        merged = {
            "A": {
                "reference": "A", "topicId": "T-A", "callStatus": "open",
                "portalUrl": "https://example.com", "programmeId": "43108390",
            }
        }
        changelog = generate_changelog([], merged, marked_closed=0)
        event = changelog["events"][0]

        assert "snapshot" in event
        assert "portalUrl" not in event["snapshot"]
        assert "programmeId" not in event["snapshot"]
        assert event["snapshot"]["callStatus"] == "open"

    def test_events_exclude_none_values(self) -> None:
        """to_dict() output excludes None-valued fields."""
        merged = {"A": {"reference": "A", "topicId": "T-A", "callStatus": "open"}}
        changelog = generate_changelog([], merged, marked_closed=0)
        event = changelog["events"][0]

        assert "old_value" not in event
        assert "new_value" not in event
        assert "field" not in event


class TestCompactCallsChangelog:
    """Tests for generate_compact_changelog_calls()."""

    def test_compact_structure(self) -> None:
        """Compact changelog has date, summary, events (no snapshots)."""
        merged = {"A": {"reference": "A", "topicId": "T-A", "callStatus": "open"}}
        changelog = generate_compact_changelog_calls([], merged, marked_closed=0)

        assert set(changelog.keys()) == {"date", "summary", "events"}
        assert set(changelog["summary"].keys()) == {"new", "changed", "auto_closed"}
        assert "fetch_timestamp" not in changelog
        assert "total_calls" not in changelog

    def test_compact_new_event(self) -> None:
        """NEW event contains type, topicId, name (no snapshot)."""
        merged = {"A": {"reference": "A", "topicId": "T-A", "callStatus": "open"}}
        changelog = generate_compact_changelog_calls([], merged, marked_closed=0)
        event = changelog["events"][0]

        assert event["type"] == "NEW"
        assert event["topicId"] == "T-A"
        assert event["name"] == "A"
        assert "snapshot" not in event
        assert "detected_at" not in event

    def test_compact_status_changed_event(self) -> None:
        """STATUS_CHANGED event includes from/to values."""
        existing = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged = {"A": {"reference": "A", "topicId": "T-A", "callStatus": "closed"}}
        changelog = generate_compact_changelog_calls([existing], merged, marked_closed=0)
        event = changelog["events"][0]

        assert event["type"] == "STATUS_CHANGED"
        assert event["from"] == "open"
        assert event["to"] == "closed"
        assert "snapshot" not in event

    def test_compact_counts(self) -> None:
        """Summary counts are accurate."""
        existing = {"reference": "A", "topicId": "T-A", "callStatus": "open"}
        merged = {
            "A": {"reference": "A", "topicId": "T-A", "callStatus": "closed"},
            "B": {"reference": "B", "topicId": "T-B", "callStatus": "open"},
        }
        changelog = generate_compact_changelog_calls([existing], merged, marked_closed=1)

        assert changelog["summary"]["new"] == 1
        assert changelog["summary"]["changed"] == 1
        assert changelog["summary"]["auto_closed"] == 1


class TestCompactDocumentsChangelog:
    """Tests for generate_compact_changelog_documents()."""

    def test_compact_structure(self) -> None:
        """Compact changelog has date, summary, events."""
        merged = {
            "115416": {
                "documentReference": "115416",
                "title": "Test Doc",
                "committeeCode": "C70407",
                "attachments": [],
            }
        }
        changelog = generate_compact_changelog_documents([], merged)

        assert set(changelog.keys()) == {"date", "summary", "events"}
        assert set(changelog["summary"].keys()) == {"new", "changed"}

    def test_compact_new_document(self) -> None:
        """NEW document event includes documentReference, title, committee."""
        merged = {
            "115416": {
                "documentReference": "115416",
                "title": "Commission Implementing Decision",
                "committeeCode": "C70407",
                "attachments": [],
            }
        }
        changelog = generate_compact_changelog_documents([], merged)
        event = changelog["events"][0]

        assert event["type"] == "NEW"
        assert event["documentReference"] == "115416"
        assert event["title"] == "Commission Implementing Decision"
        assert event["committee"] == "C70407"
        assert "snapshot" not in event
