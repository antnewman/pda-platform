"""Tests for Task model."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from pm_data_tools.models import (
    Task,
    TaskStatus,
    ConstraintType,
    Duration,
    Money,
    SourceInfo,
    CustomField,
)


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_enum_values(self) -> None:
        """Test TaskStatus enum values."""
        assert TaskStatus.NOT_STARTED.value == "not_started"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.ON_HOLD.value == "on_hold"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestConstraintType:
    """Tests for ConstraintType enum."""

    def test_enum_values(self) -> None:
        """Test ConstraintType enum values."""
        assert ConstraintType.ASAP.value == "ASAP"
        assert ConstraintType.ALAP.value == "ALAP"
        assert ConstraintType.SNET.value == "SNET"
        assert ConstraintType.MSO.value == "MSO"


class TestTask:
    """Tests for Task model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Task creation with minimal required fields."""
        task = Task(
            id=uuid4(),
            name="Test Task",
            source=source_info,
        )

        assert task.name == "Test Task"
        assert task.source == source_info
        assert task.status == TaskStatus.NOT_STARTED
        assert task.percent_complete == 0.0
        assert task.outline_level == 1
        assert task.is_milestone is False
        assert task.is_summary is False
        assert task.is_critical is False

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Task creation with all fields."""
        task_id = uuid4()
        parent_id = uuid4()
        start = datetime(2025, 1, 1, 9, 0)
        finish = datetime(2025, 1, 10, 17, 0)

        task = Task(
            id=task_id,
            name="Complete Task",
            source=source_info,
            wbs_code="1.2.3",
            outline_level=3,
            parent_id=parent_id,
            start_date=start,
            finish_date=finish,
            duration=Duration(72.0, "hours"),
            percent_complete=50.0,
            status=TaskStatus.IN_PROGRESS,
            is_milestone=False,
            is_critical=True,
            budgeted_cost=Money(Decimal("10000"), "GBP"),
        )

        assert task.id == task_id
        assert task.wbs_code == "1.2.3"
        assert task.outline_level == 3
        assert task.parent_id == parent_id
        assert task.start_date == start
        assert task.finish_date == finish
        assert task.duration == Duration(72.0, "hours")
        assert task.percent_complete == 50.0
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_critical is True

    def test_immutable(self, source_info: SourceInfo) -> None:
        """Test that Task is immutable."""
        task = Task(id=uuid4(), name="Test", source=source_info)

        with pytest.raises(AttributeError):
            task.name = "Modified"  # type: ignore

    def test_is_complete_with_100_percent(self, source_info: SourceInfo) -> None:
        """Test is_complete property with 100% progress."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            percent_complete=100.0,
        )

        assert task.is_complete is True

    def test_is_complete_with_actual_finish(self, source_info: SourceInfo) -> None:
        """Test is_complete property with actual finish date."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            actual_finish=datetime(2025, 1, 10),
            percent_complete=80.0,  # Even if not 100%
        )

        assert task.is_complete is True

    def test_is_complete_false(self, source_info: SourceInfo) -> None:
        """Test is_complete property returns False."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            percent_complete=50.0,
        )

        assert task.is_complete is False

    def test_is_started_with_progress(self, source_info: SourceInfo) -> None:
        """Test is_started property with progress."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            percent_complete=10.0,
        )

        assert task.is_started is True

    def test_is_started_with_actual_start(self, source_info: SourceInfo) -> None:
        """Test is_started property with actual start date."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            actual_start=datetime(2025, 1, 1),
        )

        assert task.is_started is True

    def test_is_started_false(self, source_info: SourceInfo) -> None:
        """Test is_started property returns False."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
        )

        assert task.is_started is False

    def test_cost_variance(self, source_info: SourceInfo) -> None:
        """Test cost_variance property."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            budgeted_cost=Money(Decimal("10000"), "GBP"),
            actual_cost=Money(Decimal("8000"), "GBP"),
        )

        variance = task.cost_variance
        assert variance is not None
        assert variance.amount == Decimal("2000")

    def test_cost_variance_none_when_missing(self, source_info: SourceInfo) -> None:
        """Test cost_variance returns None when data missing."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            budgeted_cost=Money(Decimal("10000"), "GBP"),
        )

        assert task.cost_variance is None

    def test_schedule_variance_days(self, source_info: SourceInfo) -> None:
        """Test schedule_variance_days property."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            finish_date=datetime(2025, 1, 10),
            actual_finish=datetime(2025, 1, 8),
        )

        variance = task.schedule_variance_days
        assert variance is not None
        assert variance == 2.0  # 2 days early

    def test_schedule_variance_none_when_missing(self, source_info: SourceInfo) -> None:
        """Test schedule_variance_days returns None when finish date missing."""
        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
        )

        assert task.schedule_variance_days is None

    def test_str_representation_basic(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        task = Task(
            id=uuid4(),
            name="My Task",
            source=source_info,
        )

        result = str(task)
        assert "My Task" in result
        assert "0.0% complete" in result

    def test_str_representation_with_wbs(self, source_info: SourceInfo) -> None:
        """Test string representation with WBS code."""
        task = Task(
            id=uuid4(),
            name="My Task",
            source=source_info,
            wbs_code="1.2.3",
        )

        result = str(task)
        assert "WBS=1.2.3" in result

    def test_str_representation_milestone(self, source_info: SourceInfo) -> None:
        """Test string representation for milestone."""
        task = Task(
            id=uuid4(),
            name="Milestone",
            source=source_info,
            is_milestone=True,
        )

        result = str(task)
        assert "Milestone" in result

    def test_str_representation_critical(self, source_info: SourceInfo) -> None:
        """Test string representation for critical task."""
        task = Task(
            id=uuid4(),
            name="Critical",
            source=source_info,
            is_critical=True,
        )

        result = str(task)
        assert "Critical" in result

    def test_str_representation_summary(self, source_info: SourceInfo) -> None:
        """Test string representation for summary task."""
        task = Task(
            id=uuid4(),
            name="Summary Task",
            source=source_info,
            is_summary=True,
        )

        result = str(task)
        assert "Summary" in result

    def test_custom_fields(self, source_info: SourceInfo) -> None:
        """Test task with custom fields."""
        custom = CustomField(
            name="Priority",
            value="High",
            field_type="choice",
            source_tool="jira",
        )

        task = Task(
            id=uuid4(),
            name="Test",
            source=source_info,
            custom_fields=[custom],
        )

        assert len(task.custom_fields) == 1
        assert task.custom_fields[0].name == "Priority"
