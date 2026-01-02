"""Calendar model for working time definitions.

Calendars define working hours, working days, and exceptions (holidays)
for project scheduling calculations.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID

from .base import SourceInfo


@dataclass(frozen=True)
class Calendar:
    """Working calendar definition.

    Defines working time patterns for project scheduling, including
    standard working hours, working days, and holiday exceptions.
    """

    # Identity
    id: UUID
    name: str
    source: SourceInfo

    # Standard working time
    hours_per_day: float = 8.0
    hours_per_week: float = 40.0
    days_per_month: float = 20.0

    # Working days (0=Monday, 6=Sunday)
    working_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])

    # Exceptions
    holidays: list[date] = field(default_factory=list)

    # Base calendar
    base_calendar_id: Optional[UUID] = None

    def __str__(self) -> str:
        """String representation."""
        return f"Calendar({self.name}, {self.hours_per_day}h/day, {len(self.working_days)} working days)"

    @property
    def is_weekday_working(self) -> bool:
        """Check if all weekdays (Mon-Fri) are working days.

        Returns:
            True if Monday through Friday are all working days.
        """
        return all(day in self.working_days for day in range(5))

    @property
    def is_weekend_working(self) -> bool:
        """Check if any weekend days are working days.

        Returns:
            True if Saturday or Sunday are working days.
        """
        return 5 in self.working_days or 6 in self.working_days

    @property
    def working_days_per_week(self) -> int:
        """Get number of working days per week.

        Returns:
            Count of working days.
        """
        return len(self.working_days)

    def is_working_day(self, day_of_week: int) -> bool:
        """Check if a specific day of week is a working day.

        Args:
            day_of_week: Day of week (0=Monday, 6=Sunday).

        Returns:
            True if the day is a working day.
        """
        return day_of_week in self.working_days

    def is_holiday(self, check_date: date) -> bool:
        """Check if a specific date is a holiday.

        Args:
            check_date: Date to check.

        Returns:
            True if the date is in the holidays list.
        """
        return check_date in self.holidays
