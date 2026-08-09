"""Tests for cordis_data.utils."""

from cordis_data.utils import (
    merge_calls,
    merge_projects,
    normalize_date,
    parse_action_type,
    summarize_changes,
)

class TestNormalizeDate:
    """Tests for normalize_date function."""

    def test_normalize_iso_date(self) -> None:
        """Test normalizing ISO 8601 date."""
        assert normalize_date("2024-08-09") == "2024-08-09"

    def test_normalize_iso_datetime(self) -> None:
        """Test normalizing ISO 8601 datetime."""
        assert normalize_date("2024-08-09T12:30:00") == "2024-08-09"

    def test_normalize_text_date(self) -> None:
        """Test normalizing text date format."""
        assert normalize_date("09 August 2024") == "2024-08-09"

    def test_normalize_empty_string(self) -> None:
        """Test normalizing empty string."""
        assert normalize_date("") == ""

    def test_normalize_none(self) -> None:
        """Test normalizing None."""
        assert normalize_date(None) == ""

class TestParseActionType:
    """Tests for parse_action_type function."""

    def test_parse_ria(self) -> None:
        """Test parsing RIA action type."""
        assert parse_action_type("Research and Innovation Action") == "RIA"

    def test_parse_innovation_action(self) -> None:
        """Test parsing Innovation Action."""
        assert parse_action_type("Innovation Action") == "IA"

    def test_parse_csa(self) -> None:
        """Test parsing CSA."""
        assert parse_action_type("Coordination and Support Action") == "CSA"

    def test_parse_empty(self) -> None:
        """Test parsing empty string."""
        assert parse_action_type("") == ""

class TestMergeCalls:
    """Tests for merge_calls function."""

    def test_merge_with_full_history(self) -> None:
        """Test merge with full_history flag replaces entirely."""
        existing = [{"reference": "REF-1", "title": "Call 1"}]
        new = [{"reference": "REF-2", "title": "Call 2"}]
        result = merge_calls(existing, new, full_history=True)
        assert len(result) == 1
        assert "REF-2" in result

    def test_merge_preserves_existing(self) -> None:
        """Test merge preserves existing records."""
        existing = [{"reference": "REF-1", "title": "Call 1"}]
        new = [{"reference": "REF-2", "title": "Call 2"}]
        result = merge_calls(existing, new, full_history=False)
        assert len(result) == 2
        assert "REF-1" in result
        assert "REF-2" in result

class TestMergeProjects:
    """Tests for merge_projects function."""

    def test_merge_projects_overlays_new(self) -> None:
        """Test that new projects overlay existing ones."""
        existing = [{"projectId": "PROJ-1", "acronym": "OLD"}]
        new = [{"projectId": "PROJ-1", "acronym": "NEW"}]
        result = merge_projects(existing, new)
        assert result["PROJ-1"]["acronym"] == "NEW"

class TestSummarizeChanges:
    """Tests for summarize_changes function."""

    def test_summarize_added(self) -> None:
        """Test counting added records."""
        existing = {"k1": {"v": 1}}
        merged = {"k1": {"v": 1}, "k2": {"v": 2}}
        summary = summarize_changes(existing, merged)
        assert summary["added"] == 1

    def test_summarize_changed(self) -> None:
        """Test counting changed records."""
        existing = {"k1": {"v": 1}}
        merged = {"k1": {"v": 2}}
        summary = summarize_changes(existing, merged)
        assert summary["changed"] == 1
