"""Tests for Project model."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from pm_data_tools.models import (
    Project,
    Task,
    Resource,
    Assignment,
    Dependency,
    Risk,
    Calendar,
    DeliveryConfidence,
    TaskStatus,
    RiskStatus,
    Money,
    SourceInfo,
)


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestDeliveryConfidence:
    """Tests for DeliveryConfidence enum."""

    def test_enum_values(self) -> None:
        """Test DeliveryConfidence enum values."""
        assert DeliveryConfidence.GREEN.value == "green"
        assert DeliveryConfidence.AMBER.value == "amber"
        assert DeliveryConfidence.RED.value == "red"
        assert DeliveryConfidence.EXEMPT.value == "exempt"


class TestProject:
    """Tests for Project model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Project creation with minimal fields."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            source=source_info,
        )

        assert project.name == "Test Project"
        assert len(project.tasks) == 0
        assert len(project.resources) == 0

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Project creation with all fields."""
        project = Project(
            id=uuid4(),
            name="Infrastructure Project",
            source=source_info,
            description="Major infrastructure project",
            category="Infrastructure",
            department="Department for Transport",
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 12, 31),
            delivery_confidence=DeliveryConfidence.AMBER,
            whole_life_cost=Money(Decimal("1000000000"), "GBP"),
            budgeted_cost=Money(Decimal("500000000"), "GBP"),
            senior_responsible_owner="Jane Smith",
            project_manager="John Doe",
        )

        assert project.category == "Infrastructure"
        assert project.delivery_confidence == DeliveryConfidence.AMBER
        assert project.senior_responsible_owner == "Jane Smith"

    def test_task_count(self, source_info: SourceInfo) -> None:
        """Test task_count property."""
        task1 = Task(id=uuid4(), name="Task 1", source=source_info)
        task2 = Task(id=uuid4(), name="Task 2", source=source_info)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, task2],
        )

        assert project.task_count == 2

    def test_milestone_count(self, source_info: SourceInfo) -> None:
        """Test milestone_count property."""
        task1 = Task(id=uuid4(), name="Task", source=source_info, is_milestone=False)
        milestone = Task(id=uuid4(), name="Milestone", source=source_info, is_milestone=True)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, milestone],
        )

        assert project.milestone_count == 1

    def test_critical_path_tasks(self, source_info: SourceInfo) -> None:
        """Test critical_path_tasks property."""
        task1 = Task(id=uuid4(), name="Task", source=source_info, is_critical=False)
        task2 = Task(id=uuid4(), name="Critical", source=source_info, is_critical=True)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, task2],
        )

        critical = project.critical_path_tasks
        assert len(critical) == 1
        assert critical[0].name == "Critical"

    def test_summary_tasks(self, source_info: SourceInfo) -> None:
        """Test summary_tasks property."""
        task1 = Task(id=uuid4(), name="Work", source=source_info, is_summary=False)
        task2 = Task(id=uuid4(), name="Summary", source=source_info, is_summary=True)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, task2],
        )

        summary = project.summary_tasks
        assert len(summary) == 1
        assert summary[0].name == "Summary"

    def test_work_tasks(self, source_info: SourceInfo) -> None:
        """Test work_tasks property."""
        work_task = Task(id=uuid4(), name="Work", source=source_info)
        summary = Task(id=uuid4(), name="Summary", source=source_info, is_summary=True)
        milestone = Task(id=uuid4(), name="Milestone", source=source_info, is_milestone=True)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[work_task, summary, milestone],
        )

        work = project.work_tasks
        assert len(work) == 1
        assert work[0].name == "Work"

    def test_completed_tasks(self, source_info: SourceInfo) -> None:
        """Test completed_tasks property."""
        task1 = Task(id=uuid4(), name="Incomplete", source=source_info, percent_complete=50.0)
        task2 = Task(id=uuid4(), name="Complete", source=source_info, percent_complete=100.0)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, task2],
        )

        completed = project.completed_tasks
        assert len(completed) == 1
        assert completed[0].name == "Complete"

    def test_completion_percent(self, source_info: SourceInfo) -> None:
        """Test completion_percent property."""
        task1 = Task(id=uuid4(), name="Complete", source=source_info, percent_complete=100.0)
        task2 = Task(id=uuid4(), name="Incomplete", source=source_info, percent_complete=0.0)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[task1, task2],
        )

        assert project.completion_percent == 50.0

    def test_completion_percent_empty_project(self, source_info: SourceInfo) -> None:
        """Test completion_percent for empty project."""
        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
        )

        assert project.completion_percent == 0.0

    def test_cost_variance(self, source_info: SourceInfo) -> None:
        """Test cost_variance property."""
        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            budgeted_cost=Money(Decimal("100000"), "GBP"),
            actual_cost=Money(Decimal("90000"), "GBP"),
        )

        variance = project.cost_variance
        assert variance is not None
        assert variance.amount == Decimal("10000")

    def test_cost_variance_none_when_missing(self, source_info: SourceInfo) -> None:
        """Test cost_variance returns None when cost data is missing."""
        # No cost data at all
        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
        )

        assert project.cost_variance is None

    def test_completion_percent_only_summary_tasks(self, source_info: SourceInfo) -> None:
        """Test completion_percent when project only has summary/milestone tasks (no work tasks)."""
        summary = Task(id=uuid4(), name="Summary", source=source_info, is_summary=True)
        milestone = Task(id=uuid4(), name="Milestone", source=source_info, is_milestone=True)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            tasks=[summary, milestone],
        )

        # Should return 0.0 when there are no work tasks (line 159)
        assert project.completion_percent == 0.0

    def test_high_risks(self, source_info: SourceInfo) -> None:
        """Test high_risks property."""
        low_risk = Risk(id=uuid4(), name="Low", source=source_info, probability=1, impact=2)
        high_risk = Risk(id=uuid4(), name="High", source=source_info, probability=5, impact=5)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            risks=[low_risk, high_risk],
        )

        high = project.high_risks
        assert len(high) == 1
        assert high[0].name == "High"

    def test_open_risks(self, source_info: SourceInfo) -> None:
        """Test open_risks property."""
        open_risk = Risk(id=uuid4(), name="Open", source=source_info, status=RiskStatus.IDENTIFIED)
        closed_risk = Risk(id=uuid4(), name="Closed", source=source_info, status=RiskStatus.CLOSED)

        project = Project(
            id=uuid4(),
            name="Test",
            source=source_info,
            risks=[open_risk, closed_risk],
        )

        open_risks = project.open_risks
        assert len(open_risks) == 1
        assert open_risks[0].name == "Open"

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        task = Task(id=uuid4(), name="Task", source=source_info)
        resource = Resource(id=uuid4(), name="Resource", source=source_info)

        project = Project(
            id=uuid4(),
            name="My Project",
            source=source_info,
            tasks=[task],
            resources=[resource],
        )

        result = str(project)
        assert "My Project" in result
        assert "1 tasks" in result
        assert "1 resources" in result
