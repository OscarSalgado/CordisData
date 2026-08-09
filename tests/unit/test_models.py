"""Tests for cordis_data.models."""

from cordis_data.models import Call, Project

class TestCall:
    """Tests for Call model."""

    def test_call_creation(self, sample_call_record: dict) -> None:
        """Test creating a Call instance."""
        call = Call(**sample_call_record)
        assert call.topicId == sample_call_record["topicId"]
        assert call.title == sample_call_record["title"]

    def test_call_with_minimal_fields(self) -> None:
        """Test creating a Call with minimal required fields."""
        call = Call(reference="REF-123", topicId="TOPIC-123", title="Test Call")
        assert call.reference == "REF-123"
        assert call.topicId == "TOPIC-123"

class TestProject:
    """Tests for Project model."""

    def test_project_creation(self, sample_project_record: dict) -> None:
        """Test creating a Project instance."""
        project = Project(**sample_project_record)
        assert project.projectId == sample_project_record["projectId"]
        assert project.acronym == sample_project_record["acronym"]

    def test_project_with_minimal_fields(self) -> None:
        """Test creating a Project with minimal required fields."""
        project = Project(topicId="TOPIC-123", projectId="PROJ-123")
        assert project.topicId == "TOPIC-123"
        assert project.projectId == "PROJ-123"
