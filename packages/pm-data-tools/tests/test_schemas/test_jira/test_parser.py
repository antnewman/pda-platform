"""Tests for Jira parser."""

from pathlib import Path

import pytest

from pm_data_tools.models import DependencyType, TaskStatus
from pm_data_tools.schemas.jira import JiraParser


@pytest.fixture
def simple_jira_file() -> Path:
    """Path to simple Jira JSON test file."""
    return (
        Path(__file__).parent.parent.parent
        / "fixtures"
        / "jira"
        / "simple_project.json"
    )


class TestJiraParser:
    """Tests for Jira issue parser."""

    def test_parse_project_from_file(self, simple_jira_file: Path) -> None:
        """Test parsing Jira project from JSON file."""
        parser = JiraParser(project_key="PROJ", project_name="Test Project")
        project = parser.parse_from_file(simple_jira_file)

        # Check project metadata
        assert project.name == "Test Project"
        assert project.source.tool == "jira"
        assert project.source.original_id == "PROJ"

    def test_parse_tasks_from_issues(self, simple_jira_file: Path) -> None:
        """Test parsing tasks from Jira issues."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        assert len(project.tasks) == 3

        # Check Epic (completed)
        epic = project.tasks[0]
        assert epic.name == "Epic: Project Setup"
        assert epic.status == TaskStatus.COMPLETED
        assert epic.percent_complete == 100.0
        assert epic.source.original_id == "PROJ-1"

        # Check Story 1 (in progress, has parent)
        story1 = project.tasks[1]
        assert story1.name == "Story: Design Database Schema"
        assert story1.status == TaskStatus.IN_PROGRESS
        assert story1.percent_complete == 50.0
        assert story1.parent_id is not None  # Has parent Epic
        assert story1.source.original_id == "PROJ-2"

        # Check Story 2 (not started, has parent)
        story2 = project.tasks[2]
        assert story2.name == "Story: Implement API Endpoints"
        assert story2.status == TaskStatus.NOT_STARTED
        assert story2.percent_complete == 0.0
        assert story2.parent_id is not None  # Has parent Epic
        assert story2.source.original_id == "PROJ-3"

    def test_parse_issue_hierarchy(self, simple_jira_file: Path) -> None:
        """Test parsing parent-child relationships."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        # Epic should have no parent
        epic = next(t for t in project.tasks if t.source.original_id == "PROJ-1")
        assert epic.parent_id is None

        # Stories should have Epic as parent
        story1 = next(t for t in project.tasks if t.source.original_id == "PROJ-2")
        story2 = next(t for t in project.tasks if t.source.original_id == "PROJ-3")

        assert story1.parent_id == epic.id
        assert story2.parent_id == epic.id

    def test_parse_dependencies_from_blocks(
        self, simple_jira_file: Path
    ) -> None:
        """Test parsing dependencies from 'blocks' issue links."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        # Should have one dependency (PROJ-2 blocks PROJ-3)
        assert len(project.dependencies) == 1

        dep = project.dependencies[0]
        assert dep.dependency_type == DependencyType.FINISH_TO_START

        # Verify predecessor and successor
        proj2 = next(t for t in project.tasks if t.source.original_id == "PROJ-2")
        proj3 = next(t for t in project.tasks if t.source.original_id == "PROJ-3")

        assert dep.predecessor_id == proj2.id
        assert dep.successor_id == proj3.id

    def test_parse_dates(self, simple_jira_file: Path) -> None:
        """Test parsing issue dates."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        epic = next(t for t in project.tasks if t.source.original_id == "PROJ-1")

        # Check start date (created date)
        assert epic.start_date is not None
        assert epic.start_date.year == 2025
        assert epic.start_date.month == 1
        assert epic.start_date.day == 1

        # Check finish date (due date)
        assert epic.finish_date is not None
        assert epic.finish_date.year == 2025
        assert epic.finish_date.month == 1
        assert epic.finish_date.day == 15

    def test_status_mapping(self, simple_jira_file: Path) -> None:
        """Test Jira status to canonical status mapping."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        # "Done" -> COMPLETED
        done_task = next(
            t for t in project.tasks if t.source.original_id == "PROJ-1"
        )
        assert done_task.status == TaskStatus.COMPLETED

        # "In Progress" -> IN_PROGRESS
        in_progress_task = next(
            t for t in project.tasks if t.source.original_id == "PROJ-2"
        )
        assert in_progress_task.status == TaskStatus.IN_PROGRESS

        # "To Do" -> NOT_STARTED
        todo_task = next(
            t for t in project.tasks if t.source.original_id == "PROJ-3"
        )
        assert todo_task.status == TaskStatus.NOT_STARTED

    def test_no_resources(self, simple_jira_file: Path) -> None:
        """Test that Jira parser doesn't create resources."""
        parser = JiraParser(project_key="PROJ")
        project = parser.parse_from_file(simple_jira_file)

        # Jira integration doesn't map assignees to resources
        assert len(project.resources) == 0
        assert len(project.assignments) == 0

    def test_default_project_name(self) -> None:
        """Test that project key is used as name if name not provided."""
        parser = JiraParser(project_key="MYPROJ")
        assert parser.project_name == "MYPROJ"

    def test_parse_issue_with_parent_no_key(self) -> None:
        """Test parsing issue where parent exists but has no key."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "parent": {},  # Parent exists but no key
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert len(project.tasks) == 1
        assert project.tasks[0].parent_id is None

    def test_parse_dependencies_non_blocking_link(self) -> None:
        """Test that non-blocking issue links are ignored."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task 1",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuelinks": [
                        {
                            "type": {"name": "Relates"},  # Not "blocks"
                            "outwardIssue": {"key": "PROJ-2"},
                        }
                    ],
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Task 2",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                },
            },
        ]
        project = parser.parse_issues(issues)
        assert len(project.dependencies) == 0

    def test_parse_dependencies_no_inward_or_outward(self) -> None:
        """Test dependency with neither inward nor outward issue."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuelinks": [
                        {
                            "type": {"name": "Blocks"},
                            # Neither inwardIssue nor outwardIssue
                        }
                    ],
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert len(project.dependencies) == 0

    def test_parse_dependencies_missing_keys(self) -> None:
        """Test dependency parsing when issue keys are missing."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuelinks": [
                        {
                            "type": {"name": "Blocks"},
                            "outwardIssue": {},  # No key
                        }
                    ],
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert len(project.dependencies) == 0

    def test_parse_inward_blocking_dependency(self) -> None:
        """Test parsing inward blocking dependency."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Blocked Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuelinks": [
                        {
                            "type": {"name": "Blocks"},
                            "inwardIssue": {"key": "PROJ-2"},  # PROJ-1 is blocked by PROJ-2
                        }
                    ],
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Blocking Task",
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                },
            },
        ]
        project = parser.parse_issues(issues)
        assert len(project.dependencies) == 1
        # PROJ-2 (predecessor) -> PROJ-1 (successor)
        dep = project.dependencies[0]
        task_1 = next(t for t in project.tasks if t.source.original_id == "PROJ-1")
        task_2 = next(t for t in project.tasks if t.source.original_id == "PROJ-2")
        assert dep.predecessor_id == task_2.id
        assert dep.successor_id == task_1.id

    def test_parse_status_unknown_fallback(self) -> None:
        """Test status mapping falls back to IN_PROGRESS for unknown statuses."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {
                        "name": "Unknown Status",
                        "statusCategory": {"key": "unknown"},
                    },
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert project.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_parse_date_empty_string(self) -> None:
        """Test date parsing with empty string."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "created": "",  # Empty string
                    "duedate": None,
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert project.tasks[0].start_date is None
        assert project.tasks[0].finish_date is None

    def test_parse_date_invalid_format(self) -> None:
        """Test date parsing with invalid date format."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "created": "not-a-date",
                    "duedate": "invalid",
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert project.tasks[0].start_date is None
        assert project.tasks[0].finish_date is None

    def test_parse_status_by_name_when_category_missing(self) -> None:
        """Test status mapping uses name when category is invalid (line 261)."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {
                        "name": "Backlog",  # In STATUS_NAME_TO_TASK_STATUS
                        "statusCategory": {"key": "invalid"},  # Not in mapping
                    },
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert project.tasks[0].status == TaskStatus.NOT_STARTED

    def test_parse_parent_with_none_key(self) -> None:
        """Test parsing parent that returns None for key (line 129->133)."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "parent": {"key": None},  # key exists but is None
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert project.tasks[0].parent_id is None

    def test_parse_dependencies_with_none_keys(self) -> None:
        """Test dependency parsing when keys are explicitly None (line 212)."""
        parser = JiraParser(project_key="PROJ")
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task",
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "issuelinks": [
                        {
                            "type": {"name": "Blocks"},
                            "inwardIssue": {"key": None},  # key is None
                        }
                    ],
                },
            }
        ]
        project = parser.parse_issues(issues)
        assert len(project.dependencies) == 0
