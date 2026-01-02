"""Project model for project management data.

The Project model is the top-level container for all PM data, including
tasks, resources, assignments, dependencies, risks, and calendars.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from .assignment import Assignment
from .base import Money, SourceInfo, CustomField
from .calendar import Calendar
from .dependency import Dependency
from .resource import Resource
from .risk import Risk
from .task import Task


class DeliveryConfidence(Enum):
    """Delivery Confidence Assessment (GMPP standard)."""

    GREEN = "green"  # Highly likely to achieve
    AMBER = "amber"  # Feasible but significant issues
    RED = "red"  # Unachievable without intervention
    EXEMPT = "exempt"  # Not assessed


@dataclass(frozen=True)
class Project:
    """Canonical project container.

    Top-level container for all project management data, including
    tasks, resources, assignments, dependencies, risks, and calendars.
    Aligned with UK Government GMPP reporting standards.
    """

    # Identity
    id: UUID
    name: str
    source: SourceInfo

    # Description
    description: Optional[str] = None

    # Classification (GMPP categories)
    category: Optional[str] = None  # Infrastructure, Transformation, etc.
    department: Optional[str] = None

    # Schedule
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None
    status_date: Optional[datetime] = None  # Data date / time now

    # Status (GMPP DCA)
    delivery_confidence: Optional[DeliveryConfidence] = None

    # Financials
    whole_life_cost: Optional[Money] = None
    budgeted_cost: Optional[Money] = None
    actual_cost: Optional[Money] = None

    # Benefits
    monetised_benefits: Optional[Money] = None

    # Governance
    senior_responsible_owner: Optional[str] = None
    project_manager: Optional[str] = None

    # Calendars
    default_calendar_id: Optional[UUID] = None
    calendars: list[Calendar] = field(default_factory=list)

    # Core entities
    tasks: list[Task] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    assignments: list[Assignment] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)

    # Extended entities
    risks: list[Risk] = field(default_factory=list)

    # Extensions
    custom_fields: list[CustomField] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation."""
        return f"Project({self.name}, {self.task_count} tasks, {len(self.resources)} resources)"

    # Computed properties
    @property
    def task_count(self) -> int:
        """Get total number of tasks.

        Returns:
            Count of tasks in project.
        """
        return len(self.tasks)

    @property
    def milestone_count(self) -> int:
        """Get number of milestones.

        Returns:
            Count of tasks marked as milestones.
        """
        return len([t for t in self.tasks if t.is_milestone])

    @property
    def critical_path_tasks(self) -> list[Task]:
        """Get tasks on the critical path.

        Returns:
            List of tasks marked as critical.
        """
        return [t for t in self.tasks if t.is_critical]

    @property
    def summary_tasks(self) -> list[Task]:
        """Get summary tasks.

        Returns:
            List of tasks marked as summary tasks.
        """
        return [t for t in self.tasks if t.is_summary]

    @property
    def work_tasks(self) -> list[Task]:
        """Get work tasks (non-summary, non-milestone).

        Returns:
            List of regular work tasks.
        """
        return [t for t in self.tasks if not t.is_summary and not t.is_milestone]

    @property
    def completed_tasks(self) -> list[Task]:
        """Get completed tasks.

        Returns:
            List of tasks that are 100% complete.
        """
        return [t for t in self.tasks if t.is_complete]

    @property
    def completion_percent(self) -> float:
        """Calculate overall project completion percentage.

        Returns:
            Percentage of tasks completed (0-100).
        """
        if not self.tasks:
            return 0.0

        work_tasks = self.work_tasks
        if not work_tasks:
            return 0.0

        completed = len([t for t in work_tasks if t.is_complete])
        return (completed / len(work_tasks)) * 100.0

    @property
    def cost_variance(self) -> Optional[Money]:
        """Calculate cost variance (budgeted - actual).

        Returns:
            Cost variance, or None if either budgeted or actual cost is missing.
        """
        if self.budgeted_cost and self.actual_cost:
            return self.budgeted_cost - self.actual_cost
        return None

    @property
    def high_risks(self) -> list[Risk]:
        """Get high-severity risks (score >= 15).

        Returns:
            List of high-severity risks.
        """
        return [r for r in self.risks if r.is_high_risk]

    @property
    def open_risks(self) -> list[Risk]:
        """Get open risks (not closed or materialised).

        Returns:
            List of open risks.
        """
        from .risk import RiskStatus

        closed_statuses = {RiskStatus.CLOSED, RiskStatus.MATERIALISED}
        return [r for r in self.risks if r.status not in closed_statuses]
