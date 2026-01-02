"""Constants for Smartsheet schema mapping."""

from ...models import TaskStatus


def get_status_from_percent_complete(percent: float) -> TaskStatus:
    """Map Smartsheet percent complete to canonical TaskStatus.

    Args:
        percent: Percent complete (0-100)

    Returns:
        TaskStatus based on percent complete
    """
    if percent == 100.0:
        return TaskStatus.COMPLETED
    elif percent == 0.0:
        return TaskStatus.NOT_STARTED
    else:
        return TaskStatus.IN_PROGRESS
