"""Tests for date utilities."""

import pytest
from datetime import datetime, timedelta

from pm_data_tools.utils.dates import (
    parse_iso_datetime,
    parse_datetime,
    parse_mspdi_duration,
    format_mspdi_duration,
    duration_to_timedelta,
    timedelta_to_duration,
    calculate_working_days,
    add_working_days,
    format_iso_datetime,
)
from pm_data_tools.models.base import Duration


class TestParseIsoDatetime:
    """Tests for parse_iso_datetime function."""

    def test_parse_valid_iso_datetime(self) -> None:
        """Test parsing valid ISO 8601 datetime."""
        result = parse_iso_datetime("2025-01-01T09:00:00")
        assert result == datetime(2025, 1, 1, 9, 0, 0)

    def test_parse_iso_datetime_with_timezone(self) -> None:
        """Test parsing ISO 8601 datetime with timezone."""
        result = parse_iso_datetime("2025-01-01T09:00:00+00:00")
        assert result is not None
        assert result.year == 2025

    def test_parse_none(self) -> None:
        """Test parsing None returns None."""
        assert parse_iso_datetime(None) is None

    def test_parse_invalid_returns_none(self) -> None:
        """Test parsing invalid string returns None."""
        assert parse_iso_datetime("not a date") is None


class TestParseDatetime:
    """Tests for parse_datetime function."""

    def test_parse_iso_format(self) -> None:
        """Test parsing ISO format."""
        result = parse_datetime("2025-01-01T09:00:00")
        assert result == datetime(2025, 1, 1, 9, 0, 0)

    def test_parse_flexible_format(self) -> None:
        """Test parsing flexible date format."""
        result = parse_datetime("January 1, 2025 9:00 AM")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1

    def test_parse_none(self) -> None:
        """Test parsing None returns None."""
        assert parse_datetime(None) is None

    def test_parse_invalid_returns_none(self) -> None:
        """Test parsing invalid string returns None."""
        assert parse_datetime("completely invalid") is None


class TestParseMspdiDuration:
    """Tests for parse_mspdi_duration function."""

    def test_parse_hours_only(self) -> None:
        """Test parsing hours only."""
        result = parse_mspdi_duration("PT8H0M0S")
        assert result.value == 8.0
        assert result.unit == "hours"

    def test_parse_hours_and_minutes(self) -> None:
        """Test parsing hours and minutes."""
        result = parse_mspdi_duration("PT8H30M0S")
        assert result.value == 8.5
        assert result.unit == "hours"

    def test_parse_with_seconds(self) -> None:
        """Test parsing with seconds."""
        result = parse_mspdi_duration("PT1H30M45S")
        expected = 1.0 + (30.0 / 60.0) + (45.0 / 3600.0)
        assert abs(result.value - expected) < 0.0001

    def test_parse_zero_duration(self) -> None:
        """Test parsing zero duration."""
        result = parse_mspdi_duration("PT0H0M0S")
        assert result.value == 0.0

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_mspdi_duration("")
        assert result.value == 0.0

    def test_parse_invalid_format_raises(self) -> None:
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid MSPDI duration"):
            parse_mspdi_duration("invalid")


class TestFormatMspdiDuration:
    """Tests for format_mspdi_duration function."""

    def test_format_whole_hours(self) -> None:
        """Test formatting whole hours."""
        duration = Duration(8.0, "hours")
        result = format_mspdi_duration(duration)
        assert result == "PT8H0M0S"

    def test_format_with_minutes(self) -> None:
        """Test formatting with minutes."""
        duration = Duration(8.5, "hours")
        result = format_mspdi_duration(duration)
        assert result == "PT8H30M0S"

    def test_format_days_to_hours(self) -> None:
        """Test formatting days converted to hours."""
        duration = Duration(1.0, "days")  # 8 hours
        result = format_mspdi_duration(duration)
        assert result == "PT8H0M0S"


class TestDurationConversion:
    """Tests for duration conversion functions."""

    def test_duration_to_timedelta(self) -> None:
        """Test converting Duration to timedelta."""
        duration = Duration(24.0, "hours")
        result = duration_to_timedelta(duration)
        assert result == timedelta(hours=24)

    def test_timedelta_to_duration(self) -> None:
        """Test converting timedelta to Duration."""
        td = timedelta(hours=16)
        result = timedelta_to_duration(td)
        assert result.value == 16.0
        assert result.unit == "hours"


class TestCalculateWorkingDays:
    """Tests for calculate_working_days function."""

    def test_calculate_one_day(self) -> None:
        """Test calculating one working day."""
        start = datetime(2025, 1, 1, 9, 0)
        end = datetime(2025, 1, 1, 17, 0)
        result = calculate_working_days(start, end)
        assert result == 1.0

    def test_calculate_multiple_days(self) -> None:
        """Test calculating multiple working days."""
        start = datetime(2025, 1, 1, 9, 0)
        end = datetime(2025, 1, 3, 9, 0)  # 48 hours = 6 days (8h each)
        result = calculate_working_days(start, end)
        assert result == 6.0

    def test_calculate_with_custom_hours(self) -> None:
        """Test calculating with custom hours per day."""
        start = datetime(2025, 1, 1, 9, 0)
        end = datetime(2025, 1, 1, 16, 30)  # 7.5 hours
        result = calculate_working_days(start, end, hours_per_day=7.5)
        assert result == 1.0


class TestAddWorkingDays:
    """Tests for add_working_days function."""

    def test_add_one_day(self) -> None:
        """Test adding one working day."""
        start = datetime(2025, 1, 1, 9, 0)
        result = add_working_days(start, 1.0)
        expected = datetime(2025, 1, 1, 17, 0)
        assert result == expected

    def test_add_multiple_days(self) -> None:
        """Test adding multiple working days."""
        start = datetime(2025, 1, 1, 9, 0)
        result = add_working_days(start, 5.0)
        expected = start + timedelta(hours=40)
        assert result == expected

    def test_add_with_custom_hours(self) -> None:
        """Test adding with custom hours per day."""
        start = datetime(2025, 1, 1, 9, 0)
        result = add_working_days(start, 1.0, hours_per_day=7.5)
        expected = start + timedelta(hours=7.5)
        assert result == expected


class TestFormatIsoDatetime:
    """Tests for format_iso_datetime function."""

    def test_format_datetime(self) -> None:
        """Test formatting datetime to ISO string."""
        dt = datetime(2025, 1, 1, 9, 0, 0)
        result = format_iso_datetime(dt)
        assert result == "2025-01-01T09:00:00"

    def test_format_with_microseconds(self) -> None:
        """Test formatting datetime with microseconds."""
        dt = datetime(2025, 1, 1, 9, 0, 0, 123456)
        result = format_iso_datetime(dt)
        assert "2025-01-01T09:00:00" in result
