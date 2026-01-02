"""Tests for Assignment model."""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from pm_data_tools.models import Assignment, Duration, Money, SourceInfo


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestAssignment:
    """Tests for Assignment model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Assignment creation with minimal fields."""
        task_id = uuid4()
        resource_id = uuid4()

        assignment = Assignment(
            id=uuid4(),
            task_id=task_id,
            resource_id=resource_id,
            source=source_info,
        )

        assert assignment.task_id == task_id
        assert assignment.resource_id == resource_id
        assert assignment.units == 1.0

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Assignment creation with all fields."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            units=0.5,
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 10),
            budgeted_work=Duration(40.0, "hours"),
            actual_work=Duration(20.0, "hours"),
            budgeted_cost=Money(Decimal("5000"), "GBP"),
            actual_cost=Money(Decimal("2500"), "GBP"),
        )

        assert assignment.units == 0.5
        assert assignment.budgeted_work == Duration(40.0, "hours")

    def test_allocation_percent(self, source_info: SourceInfo) -> None:
        """Test allocation_percent property."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            units=0.75,
        )

        assert assignment.allocation_percent == 75.0

    def test_work_complete_percent(self, source_info: SourceInfo) -> None:
        """Test work_complete_percent property."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            budgeted_work=Duration(40.0, "hours"),
            actual_work=Duration(20.0, "hours"),
        )

        assert assignment.work_complete_percent == 50.0

    def test_work_complete_percent_none(self, source_info: SourceInfo) -> None:
        """Test work_complete_percent returns None when data missing."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
        )

        assert assignment.work_complete_percent is None

    def test_work_complete_percent_zero_budgeted(self, source_info: SourceInfo) -> None:
        """Test work_complete_percent returns None when budgeted work is zero."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            budgeted_work=Duration(0.0, "hours"),
            actual_work=Duration(10.0, "hours"),
        )

        assert assignment.work_complete_percent is None

    def test_cost_variance(self, source_info: SourceInfo) -> None:
        """Test cost_variance property."""
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            budgeted_cost=Money(Decimal("5000"), "GBP"),
            actual_cost=Money(Decimal("4500"), "GBP"),
        )

        variance = assignment.cost_variance
        assert variance is not None
        assert variance.amount == Decimal("500")

    def test_cost_variance_none_when_missing(self, source_info: SourceInfo) -> None:
        """Test cost_variance returns None when cost data is incomplete."""
        # Only budgeted cost, no actual cost
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),
            resource_id=uuid4(),
            source=source_info,
            budgeted_cost=Money(Decimal("5000"), "GBP"),
        )

        assert assignment.cost_variance is None

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        task_id = uuid4()
        resource_id = uuid4()

        assignment = Assignment(
            id=uuid4(),
            task_id=task_id,
            resource_id=resource_id,
            source=source_info,
            units=0.5,
        )

        result = str(assignment)
        assert "50.0%" in result
