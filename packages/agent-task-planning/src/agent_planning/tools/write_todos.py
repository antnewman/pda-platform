"""write_todos tool for LLM function calling."""

from typing import Literal
from pydantic import BaseModel, Field

from agent_planning.core.task import Task, TaskStatus
from agent_planning.core.state import TaskState


class TodoItem(BaseModel):
    """A single todo item for the write_todos tool."""

    content: str = Field(description="Description of the task")
    status: Literal["pending", "in_progress", "completed", "failed", "blocked", "skipped"] = Field(
        default="pending",
        description="Current status of the task"
    )


class WriteTodosInput(BaseModel):
    """Input schema for the write_todos tool."""

    todos: list[TodoItem] = Field(
        description="Complete list of tasks. This replaces the existing list."
    )


def write_todos_tool(input_data: WriteTodosInput, state: TaskState) -> TaskState:
    """
    Update the task list.

    This tool is designed for LLM function calling. It replaces the entire
    task list with the provided todos.

    Args:
        input_data: The new todo list
        state: Current task state

    Returns:
        Updated TaskState
    """
    # Map input status to TaskStatus
    status_map = {
        "pending": TaskStatus.PENDING,
        "in_progress": TaskStatus.IN_PROGRESS,
        "completed": TaskStatus.COMPLETED,
        "failed": TaskStatus.FAILED,
        "blocked": TaskStatus.BLOCKED,
        "skipped": TaskStatus.SKIPPED,
    }

    # Create new tasks
    new_tasks = []
    for item in input_data.todos:
        task = Task(
            content=item.content,
            status=status_map[item.status],
        )
        new_tasks.append(task)

    state.tasks = new_tasks
    return state


# Tool definition for function calling
WRITE_TODOS_TOOL_DEF = {
    "name": "write_todos",
    "description": """Update your to-do list. Use this when:
- Starting a new multi-step task (create initial plan)
- Completing a task (mark as completed)
- A task fails (mark as failed)
- You need to add new tasks discovered during execution
- You need to reorder or reprioritise tasks

Always include ALL tasks, not just changed ones. This replaces the full list.""",
    "input_schema": WriteTodosInput.model_json_schema(),
}
