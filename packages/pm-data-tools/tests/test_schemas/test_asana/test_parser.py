"""Tests for Asana parser."""

from pathlib import Path

import pytest

from pm_data_tools.models import TaskStatus
from pm_data_tools.schemas.asana import AsanaParser


class TestAsanaParser:
    """Tests for AsanaParser class."""

    @pytest.fixture
    def parser(self) -> AsanaParser:
        """Create parser instance."""
        return AsanaParser()

    @pytest.fixture
    def fixture_path(self) -> Path:
        """Get path to test fixtures."""
        return Path(__file__).parent.parent.parent / "fixtures" / "asana"

    def test_parse_from_file(self, parser: AsanaParser, fixture_path: Path) -> None:
        """Test parsing from file."""
        file_path = fixture_path / "simple_project.json"
        project = parser.parse_file(file_path)

        assert project.name == "Product Launch"
        assert len(project.tasks) > 0
        assert len(project.resources) > 0

    def test_parse_from_string(self, parser: AsanaParser) -> None:
        """Test parsing from JSON string."""
        json_string = """
        {
            "data": {
                "gid": "123",
                "name": "Test Project",
                "sections": []
            }
        }
        """

        project = parser.parse_string(json_string)
        assert project.name == "Test Project"

    def test_parse_sections_as_summary_tasks(
        self, parser: AsanaParser, fixture_path: Path
    ) -> None:
        """Test sections are parsed as summary tasks."""
        file_path = fixture_path / "simple_project.json"
        project = parser.parse_file(file_path)

        # Find summary tasks (sections)
        summary_tasks = [t for t in project.tasks if t.is_summary]
        assert len(summary_tasks) == 2  # Planning, Development

        planning_section = next(t for t in summary_tasks if t.name == "Planning")
        assert planning_section.is_summary
        assert planning_section.status == TaskStatus.IN_PROGRESS

    def test_parse_tasks(self, parser: AsanaParser, fixture_path: Path) -> None:
        """Test tasks are parsed correctly."""
        file_path = fixture_path / "simple_project.json"
        project = parser.parse_file(file_path)

        # Find non-summary tasks (excluding subtasks for now)
        tasks = [t for t in project.tasks if not t.is_summary]

        # Should have tasks at different levels
        market_research = next(t for t in tasks if t.name == "Market research")
        assert market_research.status == TaskStatus.COMPLETED
        assert market_research.percent_complete == 100.0
        assert market_research.start_date is not None
        assert market_research.finish_date is not None

    def test_parse_subtasks_with_parent(
        self, parser: AsanaParser, fixture_path: Path
    ) -> None:
        """Test subtasks are parsed with correct parent relationship."""
        file_path = fixture_path / "simple_project.json"
        project = parser.parse_file(file_path)

        # Find subtasks
        competitor_analysis = next(
            t for t in project.tasks if t.name == "Competitor analysis"
        )
        assert competitor_analysis.parent_id is not None
        assert competitor_analysis.status == TaskStatus.COMPLETED

        customer_surveys = next(
            t for t in project.tasks if t.name == "Customer surveys"
        )
        assert customer_surveys.parent_id is not None
        assert customer_surveys.status == TaskStatus.IN_PROGRESS

    def test_parse_completed_status(self, parser: AsanaParser) -> None:
        """Test completed field maps to status correctly."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Completed task",
                            "completed": True,
                            "subtasks": [],
                        },
                        {
                            "gid": "t2",
                            "name": "Incomplete task",
                            "completed": False,
                            "subtasks": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        completed_task = next(t for t in project.tasks if t.name == "Completed task")
        incomplete_task = next(
            t for t in project.tasks if t.name == "Incomplete task"
        )

        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.percent_complete == 100.0
        assert incomplete_task.status == TaskStatus.IN_PROGRESS
        assert incomplete_task.percent_complete == 0.0

    def test_parse_dates(self, parser: AsanaParser) -> None:
        """Test date parsing from start_on and due_on fields."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task with dates",
                            "completed": False,
                            "start_on": "2025-01-01",
                            "due_on": "2025-01-31",
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)

        assert task.start_date is not None
        assert task.start_date.year == 2025
        assert task.start_date.month == 1
        assert task.start_date.day == 1

        assert task.finish_date is not None
        assert task.finish_date.year == 2025
        assert task.finish_date.month == 1
        assert task.finish_date.day == 31

    def test_extract_resources_from_assignee(
        self, parser: AsanaParser, fixture_path: Path
    ) -> None:
        """Test resources are extracted from assignee field."""
        file_path = fixture_path / "simple_project.json"
        project = parser.parse_file(file_path)

        # Should have 2 unique users
        assert len(project.resources) == 2

        alice = next(r for r in project.resources if r.name == "Alice Johnson")
        assert alice.name == "Alice Johnson"
        assert alice.source.original_id == "user:user1"

        bob = next(r for r in project.resources if r.name == "Bob Smith")
        assert bob.name == "Bob Smith"
        assert bob.source.original_id == "user:user2"

    def test_custom_project_name(self, parser: AsanaParser) -> None:
        """Test custom project name override."""
        parser_with_name = AsanaParser(project_name="Custom Name")
        data = {
            "gid": "123",
            "name": "Original Name",
            "sections": [],
        }

        project = parser_with_name.parse(data)
        assert project.name == "Custom Name"

    def test_parse_section_without_gid(self, parser: AsanaParser) -> None:
        """Test section without gid is skipped."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {"name": "Section without gid", "tasks": []},
                {
                    "gid": "s1",
                    "name": "Valid section",
                    "tasks": [],
                },
            ],
        }

        project = parser.parse(data)
        summary_tasks = [t for t in project.tasks if t.is_summary]
        assert len(summary_tasks) == 1
        assert summary_tasks[0].name == "Valid section"

    def test_parse_task_without_gid(self, parser: AsanaParser) -> None:
        """Test task without gid is skipped."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {"name": "Task without gid", "completed": False},
                        {
                            "gid": "t1",
                            "name": "Valid task",
                            "completed": False,
                            "subtasks": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        non_summary = [t for t in project.tasks if not t.is_summary]
        assert len(non_summary) == 1
        assert non_summary[0].name == "Valid task"

    def test_parse_subtask_without_gid(self, parser: AsanaParser) -> None:
        """Test subtask without gid is skipped."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task",
                            "completed": False,
                            "subtasks": [
                                {"name": "Subtask without gid", "completed": False},
                                {
                                    "gid": "st1",
                                    "name": "Valid subtask",
                                    "completed": False,
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        subtasks = [
            t for t in project.tasks if t.source.original_id.startswith("subtask:")
        ]
        assert len(subtasks) == 1
        assert subtasks[0].name == "Valid subtask"

    def test_parse_task_without_assignee(self, parser: AsanaParser) -> None:
        """Test task without assignee doesn't create resource."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Unassigned task",
                            "completed": False,
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 0

    def test_parse_assignee_without_gid(self, parser: AsanaParser) -> None:
        """Test assignee without gid doesn't create resource."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task",
                            "completed": False,
                            "assignee": {"name": "User without gid"},
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 0

    def test_parse_duplicate_resources(self, parser: AsanaParser) -> None:
        """Test same user assigned to multiple tasks only creates one resource."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task 1",
                            "completed": False,
                            "assignee": {"gid": "u1", "name": "Alice"},
                            "subtasks": [],
                        },
                        {
                            "gid": "t2",
                            "name": "Task 2",
                            "completed": False,
                            "assignee": {"gid": "u1", "name": "Alice"},
                            "subtasks": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 1
        assert project.resources[0].name == "Alice"

    def test_parse_task_without_dates(self, parser: AsanaParser) -> None:
        """Test task without start_on/due_on has None dates."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task without dates",
                            "completed": False,
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.start_date is None
        assert task.finish_date is None

    def test_parse_invalid_date_format(self, parser: AsanaParser) -> None:
        """Test invalid date format returns None."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "Task",
                            "completed": False,
                            "start_on": "invalid-date",
                            "due_on": "not-a-date",
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.start_date is None
        assert task.finish_date is None

    def test_parse_default_values(self, parser: AsanaParser) -> None:
        """Test default values for missing fields."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            # No name, completed, dates
                            "subtasks": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.name == "Untitled Task"
        assert task.status == TaskStatus.IN_PROGRESS  # Default when completed is False
        assert task.percent_complete == 0.0

    def test_parse_date_formats(self, parser: AsanaParser) -> None:
        """Test parsing different date formats."""
        data = {
            "gid": "123",
            "name": "Test",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [
                        {
                            "gid": "t1",
                            "name": "ISO date",
                            "completed": False,
                            "start_on": "2025-01-15",
                            "subtasks": [],
                        },
                        {
                            "gid": "t2",
                            "name": "UK date",
                            "completed": False,
                            "start_on": "15/01/2025",
                            "subtasks": [],
                        },
                        {
                            "gid": "t3",
                            "name": "US date",
                            "completed": False,
                            "start_on": "01/15/2025",
                            "subtasks": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        tasks = [t for t in project.tasks if not t.is_summary]

        # All should parse to same date
        for task in tasks:
            assert task.start_date is not None
            assert task.start_date.year == 2025
            assert task.start_date.month == 1
            assert task.start_date.day == 15

    def test_parse_without_data_wrapper(self, parser: AsanaParser) -> None:
        """Test parsing data without 'data' wrapper."""
        data = {
            "gid": "123",
            "name": "Direct Project",
            "sections": [
                {
                    "gid": "s1",
                    "name": "Section",
                    "tasks": [],
                }
            ],
        }

        project = parser.parse(data)
        assert project.name == "Direct Project"
        assert len([t for t in project.tasks if t.is_summary]) == 1
