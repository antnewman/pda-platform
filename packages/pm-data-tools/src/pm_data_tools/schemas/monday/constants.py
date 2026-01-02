"""Constants for Monday.com schema mapping."""

from ...models import TaskStatus

# Monday.com status label to canonical TaskStatus mapping
STATUS_LABEL_TO_TASK_STATUS: dict[str, TaskStatus] = {
    # Common status labels
    "Done": TaskStatus.COMPLETED,
    "Complete": TaskStatus.COMPLETED,
    "Completed": TaskStatus.COMPLETED,
    "Finished": TaskStatus.COMPLETED,
    "Working on it": TaskStatus.IN_PROGRESS,
    "In Progress": TaskStatus.IN_PROGRESS,
    "In progress": TaskStatus.IN_PROGRESS,
    "Active": TaskStatus.IN_PROGRESS,
    "Started": TaskStatus.IN_PROGRESS,
    "Not Started": TaskStatus.NOT_STARTED,
    "Not started": TaskStatus.NOT_STARTED,
    "To Do": TaskStatus.NOT_STARTED,
    "Todo": TaskStatus.NOT_STARTED,
    "Backlog": TaskStatus.NOT_STARTED,
    "Stuck": TaskStatus.IN_PROGRESS,  # Blocked tasks still in progress
    "Waiting": TaskStatus.IN_PROGRESS,
}

# Monday.com column types
COLUMN_TYPE_STATUS = "status"
COLUMN_TYPE_DATE = "date"
COLUMN_TYPE_TIMELINE = "timeline"
COLUMN_TYPE_TEXT = "text"
COLUMN_TYPE_PEOPLE = "people"
COLUMN_TYPE_NUMBERS = "numbers"
COLUMN_TYPE_PROGRESS = "progress"
