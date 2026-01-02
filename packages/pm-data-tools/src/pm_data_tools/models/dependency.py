"""Dependency model for task relationships.

Dependencies represent predecessor-successor relationships between tasks,
including dependency types (FS, FF, SS, SF) and lag/lead time.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

from .base import Duration, SourceInfo


class DependencyType(Enum):
    """Task dependency types."""

    FINISH_TO_START = "FS"  # Predecessor must finish before successor starts
    START_TO_START = "SS"  # Predecessor must start before successor starts
    FINISH_TO_FINISH = "FF"  # Predecessor must finish before successor finishes
    START_TO_FINISH = "SF"  # Predecessor must start before successor finishes


@dataclass(frozen=True)
class Dependency:
    """Task dependency/predecessor relationship.

    Represents a logical relationship between two tasks, constraining when
    the successor can start or finish based on the predecessor's schedule.
    """

    # Identity
    id: UUID
    predecessor_id: UUID
    successor_id: UUID
    source: SourceInfo

    # Type
    dependency_type: DependencyType = DependencyType.FINISH_TO_START

    # Lag (positive = delay, negative = lead)
    lag: Optional[Duration] = None

    def __str__(self) -> str:
        """String representation."""
        lag_str = ""
        if self.lag:
            sign = "+" if self.lag.value >= 0 else ""
            lag_str = f" {sign}{self.lag}"

        return f"Dependency({self.predecessor_id} {self.dependency_type.value} {self.successor_id}{lag_str})"

    @property
    def has_lag(self) -> bool:
        """Check if dependency has lag/lead time.

        Returns:
            True if lag is specified and non-zero.
        """
        return self.lag is not None and self.lag.value != 0.0

    @property
    def is_lead(self) -> bool:
        """Check if dependency has lead time (negative lag).

        Returns:
            True if lag is negative.
        """
        return self.lag is not None and self.lag.value < 0.0

    @property
    def is_lag(self) -> bool:
        """Check if dependency has lag time (positive lag).

        Returns:
            True if lag is positive.
        """
        return self.lag is not None and self.lag.value > 0.0
