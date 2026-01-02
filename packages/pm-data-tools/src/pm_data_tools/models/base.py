"""Base classes and fundamental types for PM data models.

This module provides the core building blocks used across all PM entities:
- Duration: Time spans with units
- Money: Monetary values with currency
- SourceInfo: Data provenance tracking
- CustomField: Extensible custom fields
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class DurationType(Enum):
    """Duration unit types."""

    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


@dataclass(frozen=True)
class Duration:
    """Duration with unit conversion support.

    Represents a time span with explicit units, supporting conversion between
    hours, days, weeks, and months using standard PM conventions (8-hour days,
    40-hour weeks, 160-hour months).
    """

    value: float
    unit: str  # "hours", "days", "weeks", "months"

    def to_hours(self) -> float:
        """Convert duration to hours.

        Returns:
            Duration in hours.
        """
        multipliers = {
            "hours": 1.0,
            "days": 8.0,
            "weeks": 40.0,
            "months": 160.0,
        }
        return self.value * multipliers.get(self.unit, 1.0)

    def to_days(self) -> float:
        """Convert duration to working days (8 hours).

        Returns:
            Duration in working days.
        """
        return self.to_hours() / 8.0

    def to_weeks(self) -> float:
        """Convert duration to working weeks (40 hours).

        Returns:
            Duration in working weeks.
        """
        return self.to_hours() / 40.0

    def to_months(self) -> float:
        """Convert duration to working months (160 hours).

        Returns:
            Duration in working months.
        """
        return self.to_hours() / 160.0

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value} {self.unit}"


@dataclass(frozen=True)
class Money:
    """Monetary value with currency support.

    Uses Decimal for precision. All financial calculations should use this type
    to avoid floating-point errors.
    """

    amount: Decimal
    currency: str = "GBP"

    def __add__(self, other: "Money") -> "Money":
        """Add two Money values.

        Args:
            other: Money value to add.

        Returns:
            Sum of the two Money values.

        Raises:
            ValueError: If currencies don't match.
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money values.

        Args:
            other: Money value to subtract.

        Returns:
            Difference of the two Money values.

        Raises:
            ValueError: If currencies don't match.
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: float) -> "Money":
        """Multiply Money by a scalar.

        Args:
            scalar: Multiplication factor.

        Returns:
            Money value multiplied by scalar.
        """
        return Money(self.amount * Decimal(str(scalar)), self.currency)

    def __str__(self) -> str:
        """String representation."""
        if self.currency == "GBP":
            return f"£{self.amount}"
        return f"{self.currency} {self.amount}"


@dataclass(frozen=True)
class SourceInfo:
    """Data provenance information.

    Tracks where data originated from, enabling traceability and debugging.
    """

    tool: str  # "mspdi", "p6", "jira", etc.
    tool_version: Optional[str] = None
    file_path: Optional[str] = None
    extracted_at: Optional[datetime] = None
    original_id: Optional[str] = None  # ID in source system

    def __str__(self) -> str:
        """String representation."""
        parts = [f"tool={self.tool}"]
        if self.tool_version:
            parts.append(f"version={self.tool_version}")
        if self.file_path:
            parts.append(f"file={self.file_path}")
        return f"SourceInfo({', '.join(parts)})"


@dataclass(frozen=True)
class CustomField:
    """Extensible custom field for tool-specific data.

    Allows preservation of tool-specific fields that don't map to canonical model.
    """

    name: str
    value: str | int | float | bool | datetime | None
    field_type: str  # "text", "number", "date", "boolean", "choice"
    source_tool: str  # Which tool this came from
    source_field_id: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name}={self.value} ({self.field_type})"
