"""State management for agent planning."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from agent_planning.core.task import Task, TaskStatus


class TaskState(BaseModel):
    """
    Manages the state of all tasks for an execution.

    Attributes:
        tasks: List of all tasks
        objective: The original objective/request
        created_at: When state was initialised
        iteration: Current iteration count
    """

    tasks: list[Task] = Field(default_factory=list)
    objective: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    iteration: int = 0

    def add_task(self, content: str, dependencies: Optional[list[str]] = None) -> Task:
        """Add a new task to the state."""
        task = Task(
            content=content,
            dependencies=dependencies or [],
        )
        self.tasks.append(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_next_pending(self) -> Optional[Task]:
        """Get the next pending task that has no unmet dependencies."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check dependencies
                deps_met = all(
                    self.get_task(dep_id) is not None
                    and self.get_task(dep_id).status == TaskStatus.COMPLETED  # type: ignore
                    for dep_id in task.dependencies
                )
                if deps_met:
                    return task
        return None

    def get_in_progress(self) -> list[Task]:
        """Get all in-progress tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS]

    def get_completed(self) -> list[Task]:
        """Get all completed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]

    def get_failed(self) -> list[Task]:
        """Get all failed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are in terminal states."""
        return all(task.is_terminal for task in self.tasks)

    @property
    def progress(self) -> tuple[int, int]:
        """Return (completed_count, total_count)."""
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        return completed, len(self.tasks)

    def to_display(self) -> str:
        """Format all tasks for display."""
        if not self.tasks:
            return "No tasks planned yet."
        return "\n".join(task.to_display() for task in self.tasks)

    def to_prompt_context(self) -> str:
        """Format state for inclusion in LLM prompt."""
        lines = [f"Objective: {self.objective}", "", "Current tasks:"]
        for i, task in enumerate(self.tasks, 1):
            lines.append(f"{i}. [{task.status.value}] {task.content}")
            if task.error:
                lines.append(f"   Error: {task.error}")
            if task.result and task.status == TaskStatus.COMPLETED:
                lines.append(f"   Result: {task.result[:100]}...")
        return "\n".join(lines)


class ExecutionResult(BaseModel):
    """
    Result of a planning execution.

    Attributes:
        success: Whether the execution completed successfully
        tasks: Final state of all tasks
        total_iterations: Number of iterations taken
        total_tokens: Total tokens used across all calls
        total_cost_usd: Estimated total cost in USD
        duration_seconds: Total execution time
        final_output: The final synthesised output
        error: Error message if execution failed
    """

    success: bool
    tasks: list[Task]
    total_iterations: int
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    duration_seconds: float = 0.0
    final_output: Optional[str] = None
    error: Optional[str] = None

    def summary(self) -> str:
        """Generate a human-readable summary."""
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.tasks if t.status == TaskStatus.FAILED])

        lines = [
            f"Execution {'succeeded' if self.success else 'failed'}",
            f"Tasks: {completed}/{len(self.tasks)} completed, {failed} failed",
            f"Iterations: {self.total_iterations}",
            f"Tokens: {self.total_tokens:,}",
            f"Cost: ${self.total_cost_usd:.4f}",
            f"Duration: {self.duration_seconds:.1f}s",
        ]

        if self.error:
            lines.append(f"Error: {self.error}")

        return "\n".join(lines)
