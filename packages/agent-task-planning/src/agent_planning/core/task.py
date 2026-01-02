"""Task data structures for agent planning."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the planning system."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class Task(BaseModel):
    """
    A single task in the agent's plan.

    Attributes:
        id: Unique identifier for the task
        content: Description of what needs to be done
        status: Current status of the task
        created_at: When the task was created
        updated_at: When the task was last updated
        attempts: Number of times execution was attempted
        error: Error message if task failed
        result: Result of task execution if completed
        dependencies: List of task IDs this task depends on
    """

    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    content: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    attempts: int = 0
    error: Optional[str] = None
    result: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)

    def mark_in_progress(self) -> "Task":
        """Mark task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()
        self.attempts += 1
        return self

    def mark_completed(self, result: Optional[str] = None) -> "Task":
        """Mark task as completed with optional result."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now()
        self.result = result
        return self

    def mark_failed(self, error: str) -> "Task":
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()
        self.error = error
        return self

    def mark_blocked(self, reason: Optional[str] = None) -> "Task":
        """Mark task as blocked."""
        self.status = TaskStatus.BLOCKED
        self.updated_at = datetime.now()
        if reason:
            self.error = reason
        return self

    def mark_skipped(self, reason: Optional[str] = None) -> "Task":
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.updated_at = datetime.now()
        if reason:
            self.result = f"[skipped] {reason}"
        return self

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        }

    def to_display(self) -> str:
        """Format task for display."""
        symbols = {
            TaskStatus.PENDING: "☐",
            TaskStatus.IN_PROGRESS: "◐",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "✗",
            TaskStatus.BLOCKED: "⊘",
            TaskStatus.SKIPPED: "⊘",
        }
        return f"{symbols[self.status]} {self.content}"
