"""Assignment model for task-resource relationships.

Assignments represent the allocation of resources to tasks, including
work allocation, schedule, and cost tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from .base import Duration, Money, SourceInfo


@dataclass(frozen=True)
class Assignment:
    """Task-resource assignment model.

    Represents the allocation of a resource to a task, with work units,
    schedule, and cost tracking.
    """

    # Identity
    id: UUID
    task_id: UUID
    resource_id: UUID
    source: SourceInfo

    # Allocation
    units: float = 1.0  # 1.0 = 100% allocation

    # Schedule
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None

    # Work
    budgeted_work: Optional[Duration] = None
    actual_work: Optional[Duration] = None
    remaining_work: Optional[Duration] = None

    # Cost
    budgeted_cost: Optional[Money] = None
    actual_cost: Optional[Money] = None

    def __str__(self) -> str:
        """String representation."""
        return f"Assignment(task={self.task_id}, resource={self.resource_id}, {self.units * 100}% allocation)"

    @property
    def allocation_percent(self) -> float:
        """Get allocation as percentage.

        Returns:
            Allocation percentage (100 = full-time on this task).
        """
        return self.units * 100.0

    @property
    def work_complete_percent(self) -> Optional[float]:
        """Calculate work completion percentage.

        Returns:
            Percentage of work complete, or None if budgeted work is missing.
        """
        if not self.budgeted_work or not self.actual_work:
            return None

        budgeted_hours = self.budgeted_work.to_hours()
        actual_hours = self.actual_work.to_hours()

        if budgeted_hours == 0:
            return None

        return (actual_hours / budgeted_hours) * 100.0

    @property
    def cost_variance(self) -> Optional[Money]:
        """Calculate cost variance (budgeted - actual).

        Returns:
            Cost variance, or None if either budgeted or actual cost is missing.
        """
        if self.budgeted_cost and self.actual_cost:
            return self.budgeted_cost - self.actual_cost
        return None
