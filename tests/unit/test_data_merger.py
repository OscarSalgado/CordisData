"""Tests for merge and summarization logic."""

import datetime

from cordis_data.data.merger import (
    mark_expired_closed,
    get_programme_distribution,
    get_status_distribution,
)

class TestMarkExpiredClosed:
    """Tests for marking expired calls as closed."""

    def test_mark_expired_calls(self) -> None:
        """Test marking open calls with passed deadline as closed."""
        today = datetime.date.today()
        yesterday = (today - datetime.timedelta(days=1)).isoformat()
        calls = [
            {
                "topicId": "TOPIC-1",
                "deadline": yesterday,
                "callStatus": "open",
            }
        ]
        marked = mark_expired_closed(calls, today.isoformat())
        assert calls[0]["callStatus"] == "closed"
        assert marked == 1

    def test_skip_closed_calls(self) -> None:
        """Test that already closed calls are not re-marked."""
        today = datetime.date.today()
        yesterday = (today - datetime.timedelta(days=1)).isoformat()
        calls = [
            {
                "topicId": "TOPIC-1",
                "deadline": yesterday,
                "callStatus": "closed",
            }
        ]
        marked = mark_expired_closed(calls, today.isoformat())
        assert marked == 0

    def test_skip_future_deadlines(self) -> None:
        """Test that future deadline calls are not marked."""
        today = datetime.date.today()
        tomorrow = (today + datetime.timedelta(days=1)).isoformat()
        calls = [
            {
                "topicId": "TOPIC-1",
                "deadline": tomorrow,
                "callStatus": "open",
            }
        ]
        marked = mark_expired_closed(calls, today.isoformat())
        assert calls[0]["callStatus"] == "open"
        assert marked == 0

class TestProgrammeDistribution:
    """Tests for programme distribution counting."""

    def test_get_programme_distribution(self) -> None:
        """Test counting calls by programme."""
        calls = [
            {"programme": "Horizon Europe", "topicId": "T1"},
            {"programme": "Horizon Europe", "topicId": "T2"},
            {"programme": "Digital Europe", "topicId": "T3"},
        ]
        dist = get_programme_distribution(calls)
        assert dist["Horizon Europe"] == 2
        assert dist["Digital Europe"] == 1

class TestStatusDistribution:
    """Tests for status distribution counting."""

    def test_get_status_distribution(self) -> None:
        """Test counting calls by status."""
        calls = [
            {"callStatus": "open", "topicId": "T1"},
            {"callStatus": "open", "topicId": "T2"},
            {"callStatus": "closed", "topicId": "T3"},
        ]
        dist = get_status_distribution(calls)
        assert dist["open"] == 2
        assert dist["closed"] == 1
