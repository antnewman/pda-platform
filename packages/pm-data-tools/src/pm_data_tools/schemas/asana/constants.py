"""Constants for Asana schema mapping."""

from ...models import TaskStatus

# Asana completed boolean to canonical TaskStatus mapping
def get_status_from_completed(completed: bool) -> TaskStatus:
    """Map Asana completed status to canonical TaskStatus.

    Args:
        completed: True if task is completed

    Returns:
        TaskStatus.COMPLETED if completed, else TaskStatus.IN_PROGRESS
    """
    return TaskStatus.COMPLETED if completed else TaskStatus.IN_PROGRESS
