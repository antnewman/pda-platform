"""Date and duration utilities for PM data tools.

This module provides utilities for parsing and converting dates and durations
across different PM tool formats, with special support for ISO 8601 and
MSPDI-style duration formats.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

from dateutil import parser as dateutil_parser

from ..models.base import Duration


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 datetime string.

    Args:
        value: ISO 8601 datetime string (e.g., "2025-01-01T09:00:00").

    Returns:
        Parsed datetime, or None if value is None or invalid.
    """
    if not value:
        return None

    try:
        return dateutil_parser.isoparse(value)
    except (ValueError, TypeError):
        return None


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse datetime string in various formats.

    Tries ISO 8601 first, then falls back to dateutil parser for
    flexible date format handling.

    Args:
        value: Datetime string in various formats.

    Returns:
        Parsed datetime, or None if value is None or invalid.
    """
    if not value:
        return None

    # Try ISO 8601 first (fastest)
    result = parse_iso_datetime(value)
    if result:
        return result

    # Fall back to dateutil for flexible parsing
    try:
        return dateutil_parser.parse(value)
    except (ValueError, TypeError):
        return None


def parse_mspdi_duration(duration_str: str) -> Duration:
    """Parse MSPDI ISO 8601 duration format.

    MSPDI uses ISO 8601 duration format: PT[nH][nM][nS]
    Example: "PT8H0M0S" = 8 hours

    Args:
        duration_str: ISO 8601 duration string.

    Returns:
        Duration object in hours.

    Raises:
        ValueError: If duration string is invalid.
    """
    if not duration_str:
        return Duration(0.0, "hours")

    # Pattern: PT[nH][nM][nS]
    pattern = r"PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?"
    match = re.match(pattern, duration_str)

    if not match:
        raise ValueError(f"Invalid MSPDI duration format: {duration_str}")

    hours = float(match.group(1) or 0)
    minutes = float(match.group(2) or 0)
    seconds = float(match.group(3) or 0)

    total_hours = hours + (minutes / 60.0) + (seconds / 3600.0)
    return Duration(total_hours, "hours")


def format_mspdi_duration(duration: Duration) -> str:
    """Format Duration as MSPDI ISO 8601 duration string.

    Args:
        duration: Duration to format.

    Returns:
        ISO 8601 duration string (e.g., "PT8H0M0S").
    """
    hours = int(duration.to_hours())
    remaining_seconds = (duration.to_hours() - hours) * 3600
    minutes = int(remaining_seconds / 60)
    seconds = int(remaining_seconds % 60)

    return f"PT{hours}H{minutes}M{seconds}S"


def duration_to_timedelta(duration: Duration) -> timedelta:
    """Convert Duration to Python timedelta.

    Args:
        duration: Duration to convert.

    Returns:
        Equivalent timedelta.
    """
    return timedelta(hours=duration.to_hours())


def timedelta_to_duration(td: timedelta) -> Duration:
    """Convert Python timedelta to Duration.

    Args:
        td: Timedelta to convert.

    Returns:
        Duration in hours.
    """
    hours = td.total_seconds() / 3600.0
    return Duration(hours, "hours")


def calculate_working_days(
    start: datetime, end: datetime, hours_per_day: float = 8.0
) -> float:
    """Calculate number of working days between two dates.

    Args:
        start: Start datetime.
        end: End datetime.
        hours_per_day: Working hours per day (default: 8.0).

    Returns:
        Number of working days (decimal).
    """
    delta = end - start
    hours = delta.total_seconds() / 3600.0
    return hours / hours_per_day


def add_working_days(
    start: datetime, days: float, hours_per_day: float = 8.0
) -> datetime:
    """Add working days to a datetime.

    Args:
        start: Start datetime.
        days: Number of working days to add.
        hours_per_day: Working hours per day (default: 8.0).

    Returns:
        New datetime after adding working days.
    """
    hours = days * hours_per_day
    return start + timedelta(hours=hours)


def format_iso_datetime(dt: datetime) -> str:
    """Format datetime as ISO 8601 string.

    Args:
        dt: Datetime to format.

    Returns:
        ISO 8601 datetime string.
    """
    return dt.isoformat()
