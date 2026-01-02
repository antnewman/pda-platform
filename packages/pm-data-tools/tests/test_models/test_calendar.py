"""Tests for Calendar model."""

import pytest
from datetime import date
from uuid import uuid4

from pm_data_tools.models import Calendar, SourceInfo


@pytest.fixture
def source_info() -> SourceInfo:
    """Test source info."""
    return SourceInfo(tool="test")


class TestCalendar:
    """Tests for Calendar model."""

    def test_creation_minimal(self, source_info: SourceInfo) -> None:
        """Test Calendar creation with minimal fields."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
        )

        assert calendar.name == "Standard"
        assert calendar.hours_per_day == 8.0
        assert calendar.hours_per_week == 40.0
        assert calendar.working_days == [0, 1, 2, 3, 4]

    def test_creation_complete(self, source_info: SourceInfo) -> None:
        """Test Calendar creation with all fields."""
        base_id = uuid4()
        holidays = [date(2025, 12, 25), date(2025, 12, 26)]

        calendar = Calendar(
            id=uuid4(),
            name="UK Calendar",
            source=source_info,
            hours_per_day=7.5,
            hours_per_week=37.5,
            working_days=[0, 1, 2, 3, 4],
            holidays=holidays,
            base_calendar_id=base_id,
        )

        assert calendar.hours_per_day == 7.5
        assert calendar.hours_per_week == 37.5
        assert len(calendar.holidays) == 2
        assert calendar.base_calendar_id == base_id

    def test_is_weekday_working_true(self, source_info: SourceInfo) -> None:
        """Test is_weekday_working property returns True."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
            working_days=[0, 1, 2, 3, 4],
        )

        assert calendar.is_weekday_working is True

    def test_is_weekday_working_false(self, source_info: SourceInfo) -> None:
        """Test is_weekday_working property returns False."""
        calendar = Calendar(
            id=uuid4(),
            name="Custom",
            source=source_info,
            working_days=[0, 1, 2, 3],  # Missing Friday
        )

        assert calendar.is_weekday_working is False

    def test_is_weekend_working_false(self, source_info: SourceInfo) -> None:
        """Test is_weekend_working property returns False."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
            working_days=[0, 1, 2, 3, 4],
        )

        assert calendar.is_weekend_working is False

    def test_is_weekend_working_true(self, source_info: SourceInfo) -> None:
        """Test is_weekend_working property returns True."""
        calendar = Calendar(
            id=uuid4(),
            name="24/7",
            source=source_info,
            working_days=[0, 1, 2, 3, 4, 5, 6],
        )

        assert calendar.is_weekend_working is True

    def test_working_days_per_week(self, source_info: SourceInfo) -> None:
        """Test working_days_per_week property."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
            working_days=[0, 1, 2, 3, 4],
        )

        assert calendar.working_days_per_week == 5

    def test_is_working_day(self, source_info: SourceInfo) -> None:
        """Test is_working_day method."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
            working_days=[0, 1, 2, 3, 4],
        )

        assert calendar.is_working_day(0) is True  # Monday
        assert calendar.is_working_day(4) is True  # Friday
        assert calendar.is_working_day(5) is False  # Saturday
        assert calendar.is_working_day(6) is False  # Sunday

    def test_is_holiday(self, source_info: SourceInfo) -> None:
        """Test is_holiday method."""
        christmas = date(2025, 12, 25)

        calendar = Calendar(
            id=uuid4(),
            name="UK Calendar",
            source=source_info,
            holidays=[christmas],
        )

        assert calendar.is_holiday(christmas) is True
        assert calendar.is_holiday(date(2025, 12, 24)) is False

    def test_str_representation(self, source_info: SourceInfo) -> None:
        """Test string representation."""
        calendar = Calendar(
            id=uuid4(),
            name="Standard",
            source=source_info,
            hours_per_day=8.0,
            working_days=[0, 1, 2, 3, 4],
        )

        result = str(calendar)
        assert "Standard" in result
        assert "8.0h/day" in result
        assert "5 working days" in result
