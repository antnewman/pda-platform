"""Constants and mappings for Jira schema.

This module defines Jira-specific constants and mappings for converting
Jira issues to the canonical project data model.
"""

from pm_data_tools.models import TaskStatus


# Jira status categories to canonical task status
STATUS_CATEGORY_TO_TASK_STATUS = {
    "new": TaskStatus.NOT_STARTED,
    "indeterminate": TaskStatus.IN_PROGRESS,
    "done": TaskStatus.COMPLETED,
}

# Common Jira status names to canonical task status
STATUS_NAME_TO_TASK_STATUS = {
    "to do": TaskStatus.NOT_STARTED,
    "backlog": TaskStatus.NOT_STARTED,
    "selected for development": TaskStatus.NOT_STARTED,
    "in progress": TaskStatus.IN_PROGRESS,
    "in development": TaskStatus.IN_PROGRESS,
    "in review": TaskStatus.IN_PROGRESS,
    "done": TaskStatus.COMPLETED,
    "closed": TaskStatus.COMPLETED,
    "resolved": TaskStatus.COMPLETED,
}

# Jira issue link types that represent dependencies
DEPENDENCY_LINK_TYPES = {
    "Blocks",
    "Cloners",
    "Duplicate",
    "Relates",
    "Causes",
}

# Jira issue link directions
INWARD_LINKS = {
    "is blocked by": "predecessor",
    "is cloned by": "predecessor",
    "is duplicated by": "predecessor",
    "is caused by": "predecessor",
}

OUTWARD_LINKS = {
    "blocks": "successor",
    "clones": "successor",
    "duplicates": "successor",
    "causes": "successor",
}

# Jira API field names
JIRA_FIELDS = {
    "SUMMARY": "summary",
    "DESCRIPTION": "description",
    "STATUS": "status",
    "ASSIGNEE": "assignee",
    "REPORTER": "reporter",
    "CREATED": "created",
    "UPDATED": "updated",
    "DUE_DATE": "duedate",
    "PRIORITY": "priority",
    "ISSUE_TYPE": "issuetype",
    "PARENT": "parent",
    "SUBTASKS": "subtasks",
    "ISSUE_LINKS": "issuelinks",
    "TIME_TRACKING": "timetracking",
    "STORY_POINTS": "customfield_10016",  # Common story points field
}
