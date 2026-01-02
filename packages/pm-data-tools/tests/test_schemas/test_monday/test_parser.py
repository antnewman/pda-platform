"""Tests for Monday.com parser."""

from pathlib import Path

import pytest

from pm_data_tools.models import TaskStatus
from pm_data_tools.schemas.monday import MondayParser


@pytest.fixture
def simple_board_file() -> Path:
    """Path to simple Monday.com board JSON test file."""
    return (
        Path(__file__).parent.parent.parent
        / "fixtures"
        / "monday"
        / "simple_board.json"
    )


@pytest.fixture
def parser() -> MondayParser:
    """Monday parser instance."""
    return MondayParser()


class TestMondayParser:
    """Tests for Monday.com board parser."""

    def test_parse_from_file(self, parser: MondayParser, simple_board_file: Path) -> None:
        """Test parsing Monday.com board from JSON file."""
        project = parser.parse_file(simple_board_file)

        # Check project metadata
        assert project.name == "Project Alpha"
        assert project.source.tool == "monday"
        assert project.source.original_id == "123456"

    def test_parse_from_string(self, parser: MondayParser, simple_board_file: Path) -> None:
        """Test parsing from JSON string."""
        json_string = simple_board_file.read_text()
        project = parser.parse_string(json_string)

        assert project.name == "Project Alpha"

    def test_parse_groups_as_summary_tasks(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing groups as summary tasks."""
        project = parser.parse_file(simple_board_file)

        # Should have 2 groups + 3 items + 2 subitems = 7 tasks
        assert len(project.tasks) == 7

        # Find group tasks
        group_tasks = [t for t in project.tasks if t.is_summary]
        assert len(group_tasks) == 2

        planning_phase = next(t for t in group_tasks if t.name == "Planning Phase")
        assert planning_phase.is_summary
        assert planning_phase.status == TaskStatus.IN_PROGRESS

        dev_phase = next(t for t in group_tasks if t.name == "Development Phase")
        assert dev_phase.is_summary

    def test_parse_items_as_tasks(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing items as tasks."""
        project = parser.parse_file(simple_board_file)

        # Find item tasks (not groups, not subitems)
        items = [
            t
            for t in project.tasks
            if not t.is_summary and "subitem:" not in t.source.original_id
        ]
        assert len(items) == 3

        # Check first item
        requirements = next(t for t in items if t.name == "Define requirements")
        assert requirements.status == TaskStatus.COMPLETED
        assert requirements.percent_complete == 100.0
        assert requirements.parent_id is not None

    def test_parse_subitems_with_parent(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing subitems with parent relationship."""
        project = parser.parse_file(simple_board_file)

        # Find subitems
        subitems = [t for t in project.tasks if "subitem:" in t.source.original_id]
        assert len(subitems) == 2

        wireframes = next(t for t in subitems if t.name == "Wireframes")
        assert wireframes.parent_id is not None
        assert wireframes.status == TaskStatus.COMPLETED

        # Parent should be "Create design mockups"
        parent = next(t for t in project.tasks if t.id == wireframes.parent_id)
        assert parent.name == "Create design mockups"

    def test_parse_status_from_column(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing status from status column."""
        project = parser.parse_file(simple_board_file)

        # Check various status mappings
        done_task = next(t for t in project.tasks if t.name == "Define requirements")
        assert done_task.status == TaskStatus.COMPLETED

        in_progress_task = next(
            t for t in project.tasks if t.name == "Create design mockups"
        )
        assert in_progress_task.status == TaskStatus.IN_PROGRESS

        not_started_task = next(
            t for t in project.tasks if t.name == "Implement frontend"
        )
        assert not_started_task.status == TaskStatus.NOT_STARTED

    def test_parse_timeline_dates(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing dates from timeline column."""
        project = parser.parse_file(simple_board_file)

        requirements = next(t for t in project.tasks if t.name == "Define requirements")
        assert requirements.start_date is not None
        assert requirements.start_date.year == 2025
        assert requirements.start_date.month == 1
        assert requirements.start_date.day == 1

        assert requirements.finish_date is not None
        assert requirements.finish_date.year == 2025
        assert requirements.finish_date.month == 1
        assert requirements.finish_date.day == 15

    def test_parse_single_date_column(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing single date column (not timeline)."""
        project = parser.parse_file(simple_board_file)

        frontend_task = next(t for t in project.tasks if t.name == "Implement frontend")
        # Should have finish date from "Due Date" column
        assert frontend_task.finish_date is not None
        assert frontend_task.finish_date.year == 2025
        assert frontend_task.finish_date.month == 2
        assert frontend_task.finish_date.day == 15

    def test_parse_percent_complete_from_progress(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test parsing percent complete from progress column."""
        project = parser.parse_file(simple_board_file)

        requirements = next(t for t in project.tasks if t.name == "Define requirements")
        assert requirements.percent_complete == 100.0

        mockups = next(t for t in project.tasks if t.name == "Create design mockups")
        assert mockups.percent_complete == 50.0

    def test_extract_resources_from_people_column(
        self, parser: MondayParser, simple_board_file: Path
    ) -> None:
        """Test extracting resources from people columns."""
        project = parser.parse_file(simple_board_file)

        # Should have 3 unique people
        assert len(project.resources) == 3

        names = {r.name for r in project.resources}
        assert "Alice Smith" in names
        assert "Bob Jones" in names
        assert "Carol White" in names

    def test_custom_board_name(self, simple_board_file: Path) -> None:
        """Test overriding board name."""
        parser = MondayParser(board_name="Custom Project Name")
        project = parser.parse_file(simple_board_file)

        assert project.name == "Custom Project Name"

    def test_status_derived_from_percent_complete(self, parser: MondayParser) -> None:
        """Test status derived from percent complete when not set."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Task at 0%",
                            "column_values": [
                                {
                                    "type": "progress",
                                    "value": "{\"value\": 0}",
                                }
                            ],
                            "subitems": [],
                        },
                        {
                            "id": "i2",
                            "name": "Task at 100%",
                            "column_values": [
                                {
                                    "type": "progress",
                                    "value": "{\"value\": 100}",
                                }
                            ],
                            "subitems": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)

        task_zero = next(t for t in project.tasks if t.name == "Task at 0%")
        assert task_zero.status == TaskStatus.NOT_STARTED

        task_hundred = next(t for t in project.tasks if t.name == "Task at 100%")
        assert task_hundred.status == TaskStatus.COMPLETED

    def test_parse_with_null_values(self, parser: MondayParser) -> None:
        """Test parsing with null/empty column values."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Task with nulls",
                            "column_values": [
                                {
                                    "type": "timeline",
                                    "value": "null",
                                },
                                {
                                    "type": "progress",
                                    "value": "null",
                                },
                                {
                                    "type": "people",
                                    "value": "null",
                                },
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)

        # Should handle nulls gracefully
        assert task.start_date is None
        assert task.finish_date is None
        assert task.percent_complete == 0.0

    def test_parse_group_without_id(self, parser: MondayParser) -> None:
        """Test handling group without ID."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "title": "Group without ID",
                    "items": [],
                }
            ],
        }

        project = parser.parse(data)
        # Group without ID should be skipped
        assert len(project.tasks) == 0

    def test_parse_item_without_id(self, parser: MondayParser) -> None:
        """Test handling item without ID."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "name": "Item without ID",
                            "column_values": [],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        # Should only have group task
        assert len(project.tasks) == 1
        assert project.tasks[0].is_summary

    def test_parse_subitem_without_id(self, parser: MondayParser) -> None:
        """Test handling subitem without ID."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [],
                            "subitems": [
                                {
                                    "name": "Subitem without ID",
                                    "column_values": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        # Should have group + item, but not subitem
        assert len(project.tasks) == 2

    def test_parse_invalid_json_in_column_value(self, parser: MondayParser) -> None:
        """Test handling invalid JSON in column values."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "status",
                                    "value": "{invalid json}",
                                },
                                {
                                    "type": "timeline",
                                    "value": "{not valid}",
                                },
                                {
                                    "type": "progress",
                                    "value": "not a number",
                                },
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        # Should parse without crashing, using defaults
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.status == TaskStatus.IN_PROGRESS  # Default
        assert task.start_date is None
        assert task.finish_date is None

    def test_parse_progress_from_numbers_column(self, parser: MondayParser) -> None:
        """Test extracting progress from numbers column with 'progress' in title."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "numbers",
                                    "title": "% Progress",
                                    "value": "75",
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 75.0

    def test_parse_date_formats(self, parser: MondayParser) -> None:
        """Test parsing various date formats."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "ISO Date",
                            "column_values": [
                                {
                                    "type": "date",
                                    "value": "{\"date\": \"2025-03-15\"}",
                                }
                            ],
                            "subitems": [],
                        },
                        {
                            "id": "i2",
                            "name": "UK Date",
                            "column_values": [
                                {
                                    "type": "date",
                                    "value": "{\"date\": \"15/03/2025\"}",
                                }
                            ],
                            "subitems": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)

        iso_task = next(t for t in project.tasks if t.name == "ISO Date")
        assert iso_task.finish_date is not None
        assert iso_task.finish_date.day == 15
        assert iso_task.finish_date.month == 3

        uk_task = next(t for t in project.tasks if t.name == "UK Date")
        assert uk_task.finish_date is not None
        assert uk_task.finish_date.day == 15
        assert uk_task.finish_date.month == 3

    def test_parse_invalid_date_format(self, parser: MondayParser) -> None:
        """Test handling invalid date formats."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "date",
                                    "value": "{\"date\": \"not-a-date\"}",
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        # Invalid date should be None
        assert task.finish_date is None

    def test_parse_multiple_people_in_column(self, parser: MondayParser) -> None:
        """Test parsing multiple people assigned to same item."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "people",
                                    "value": '{"personsAndTeams": [{"id": 1, "name": "Person A"}, {"id": 2, "name": "Person B"}]}',
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 2

        names = {r.name for r in project.resources}
        assert "Person A" in names
        assert "Person B" in names

    def test_parse_people_without_id(self, parser: MondayParser) -> None:
        """Test handling person without ID in people column."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "people",
                                    "value": '{"personsAndTeams": [{"name": "No ID Person"}]}',
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        # Person without ID should be skipped
        assert len(project.resources) == 0

    def test_parse_duplicate_resources(self, parser: MondayParser) -> None:
        """Test that duplicate resources are not added twice."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item 1",
                            "column_values": [
                                {
                                    "type": "people",
                                    "value": '{"personsAndTeams": [{"id": 1, "name": "Alice"}]}',
                                }
                            ],
                            "subitems": [],
                        },
                        {
                            "id": "i2",
                            "name": "Item 2",
                            "column_values": [
                                {
                                    "type": "people",
                                    "value": '{"personsAndTeams": [{"id": 1, "name": "Alice"}]}',
                                }
                            ],
                            "subitems": [],
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        # Should only have 1 resource (Alice), not 2
        assert len(project.resources) == 1
        assert project.resources[0].name == "Alice"

    def test_parse_progress_as_numeric_value(self, parser: MondayParser) -> None:
        """Test parsing progress when value is already numeric."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "progress",
                                    "value": 60,  # Numeric, not JSON string
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 60.0

    def test_parse_status_as_dict(self, parser: MondayParser) -> None:
        """Test parsing status when value is already a dict."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "status",
                                    "value": {"label": "Done"},  # Dict, not JSON string
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.status == TaskStatus.COMPLETED

    def test_parse_progress_as_json_number(self, parser: MondayParser) -> None:
        """Test parsing progress when JSON string contains a number, not a dict."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "progress",
                                    "value": "75",  # JSON string that's a number
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 75.0

    def test_parse_progress_from_numbers_column_as_int(self, parser: MondayParser) -> None:
        """Test parsing progress from numbers column when value is int."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "numbers",
                                    "title": "Progress Tracker",
                                    "value": 80,  # Int value, not string
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 80.0

    def test_parse_progress_from_numbers_column_as_float(self, parser: MondayParser) -> None:
        """Test parsing progress from numbers column when value is float."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "numbers",
                                    "title": "Complete %",
                                    "value": 67.5,  # Float value, not string
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 67.5

    def test_parse_people_with_invalid_structure(self, parser: MondayParser) -> None:
        """Test resource extraction handles invalid people column structure gracefully."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "people",
                                    "value": "[1, 2, 3]",  # JSON array, not dict - triggers AttributeError
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        # Should not crash, just skip invalid people data
        project = parser.parse(data)
        assert len(project.resources) == 0

    def test_parse_progress_from_numbers_column_invalid_string(
        self, parser: MondayParser
    ) -> None:
        """Test parsing progress from numbers column with invalid number string."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "numbers",
                                    "title": "Progress %",
                                    "value": "not-a-number",  # Invalid string
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        # Should not crash, just return None for percent complete
        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.percent_complete == 0.0  # Default when extraction fails

    def test_parse_status_column_with_empty_value(self, parser: MondayParser) -> None:
        """Test status column with empty value falls back to default."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "status",
                                    "value": "",  # Empty value
                                }
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        assert task.status == TaskStatus.IN_PROGRESS  # Default

    def test_parse_multiple_date_columns(self, parser: MondayParser) -> None:
        """Test parsing with multiple date-related columns."""
        data = {
            "id": "123",
            "name": "Test Board",
            "groups": [
                {
                    "id": "g1",
                    "title": "Group",
                    "items": [
                        {
                            "id": "i1",
                            "name": "Item",
                            "column_values": [
                                {
                                    "type": "date",
                                    "value": "null",  # Null date - should be skipped
                                },
                                {
                                    "type": "timeline",
                                    "value": '{"from": "2025-01-01", "to": "2025-01-31"}',
                                },
                            ],
                            "subitems": [],
                        }
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = next(t for t in project.tasks if not t.is_summary)
        # Timeline should take precedence
        assert task.start_date is not None
        assert task.finish_date is not None
