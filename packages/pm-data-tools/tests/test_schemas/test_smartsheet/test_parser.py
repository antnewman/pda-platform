"""Tests for Smartsheet parser."""

from pathlib import Path

import pytest

from pm_data_tools.models import TaskStatus
from pm_data_tools.schemas.smartsheet import SmartsheetParser


class TestSmartsheetParser:
    """Tests for SmartsheetParser class."""

    @pytest.fixture
    def parser(self) -> SmartsheetParser:
        """Create parser instance."""
        return SmartsheetParser()

    @pytest.fixture
    def fixture_path(self) -> Path:
        """Get path to test fixtures."""
        return Path(__file__).parent.parent.parent / "fixtures" / "smartsheet"

    def test_parse_from_file(
        self, parser: SmartsheetParser, fixture_path: Path
    ) -> None:
        """Test parsing from file."""
        file_path = fixture_path / "simple_sheet.json"
        project = parser.parse_file(file_path)

        assert project.name == "Project Plan"
        assert len(project.tasks) > 0
        assert len(project.resources) > 0

    def test_parse_from_string(self, parser: SmartsheetParser) -> None:
        """Test parsing from JSON string."""
        json_string = """
        {
            "data": {
                "id": "123",
                "name": "Test Sheet",
                "rows": []
            }
        }
        """

        project = parser.parse_string(json_string)
        assert project.name == "Test Sheet"

    def test_parse_hierarchy_from_parent_id(
        self, parser: SmartsheetParser, fixture_path: Path
    ) -> None:
        """Test hierarchical structure built from parentId."""
        file_path = fixture_path / "simple_sheet.json"
        project = parser.parse_file(file_path)

        # Find summary tasks (rows with children)
        summary_tasks = [t for t in project.tasks if t.is_summary]
        assert len(summary_tasks) == 2  # Phase 1, Phase 2

        phase1 = next(t for t in summary_tasks if "Phase 1" in t.name)
        assert phase1.is_summary

        # Find child tasks
        child_tasks = [t for t in project.tasks if t.parent_id == phase1.id]
        assert len(child_tasks) == 2  # Requirements, Design

    def test_parse_percent_complete_to_status(
        self, parser: SmartsheetParser
    ) -> None:
        """Test percent complete maps to status correctly."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "cells": [
                        {"columnId": 1, "value": "Completed task"},
                        {"columnId": 2, "columnType": "PERCENT_COMPLETE", "value": 1.0},
                    ],
                },
                {
                    "id": 2,
                    "cells": [
                        {"columnId": 1, "value": "Not started task"},
                        {"columnId": 2, "columnType": "PERCENT_COMPLETE", "value": 0.0},
                    ],
                },
                {
                    "id": 3,
                    "cells": [
                        {"columnId": 1, "value": "In progress task"},
                        {
                            "columnId": 2,
                            "columnType": "PERCENT_COMPLETE",
                            "value": 0.5,
                        },
                    ],
                },
            ],
        }

        project = parser.parse(data)

        completed = next(t for t in project.tasks if "Completed" in t.name)
        assert completed.status == TaskStatus.COMPLETED
        assert completed.percent_complete == 100.0

        not_started = next(t for t in project.tasks if "Not started" in t.name)
        assert not_started.status == TaskStatus.NOT_STARTED
        assert not_started.percent_complete == 0.0

        in_progress = next(t for t in project.tasks if "In progress" in t.name)
        assert in_progress.status == TaskStatus.IN_PROGRESS
        assert in_progress.percent_complete == 50.0

    def test_parse_dates_from_cells(self, parser: SmartsheetParser) -> None:
        """Test date parsing from cells."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "cells": [
                        {"columnId": 1, "value": "Task with dates"},
                        {"columnId": 2, "columnType": "DATE", "value": "2025-01-01"},
                        {"columnId": 3, "columnType": "DATE", "value": "2025-01-31"},
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = project.tasks[0]

        assert task.start_date is not None
        assert task.start_date.year == 2025
        assert task.start_date.month == 1
        assert task.start_date.day == 1

    def test_extract_resources_from_contact_list(
        self, parser: SmartsheetParser, fixture_path: Path
    ) -> None:
        """Test resources extracted from CONTACT_LIST cells."""
        file_path = fixture_path / "simple_sheet.json"
        project = parser.parse_file(file_path)

        # Should have 2 unique users
        assert len(project.resources) == 2

        alice = next(
            r for r in project.resources if "alice@example.com" in r.name.lower()
        )
        assert "alice" in alice.name.lower()

        bob = next(r for r in project.resources if "bob@example.com" in r.name.lower())
        assert "bob" in bob.name.lower()

    def test_custom_sheet_name(self, parser: SmartsheetParser) -> None:
        """Test custom sheet name override."""
        parser_with_name = SmartsheetParser(sheet_name="Custom Name")
        data = {
            "id": "123",
            "name": "Original Name",
            "rows": [],
        }

        project = parser_with_name.parse(data)
        assert project.name == "Custom Name"

    def test_parse_row_without_id(self, parser: SmartsheetParser) -> None:
        """Test row without id is skipped."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {"cells": [{"columnId": 1, "value": "Row without id"}]},
                {
                    "id": 1,
                    "cells": [{"columnId": 1, "value": "Valid row"}],
                },
            ],
        }

        project = parser.parse(data)
        assert len(project.tasks) == 1
        assert project.tasks[0].name == "Valid row"

    def test_parse_row_without_cells(self, parser: SmartsheetParser) -> None:
        """Test row without cells uses default name."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    # No cells
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.tasks) == 1
        assert project.tasks[0].name == "Untitled Row"

    def test_parse_assignedTo_as_string(self, parser: SmartsheetParser) -> None:
        """Test assignedTo field as string."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "assignedTo": "user@example.com",
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 1
        assert project.resources[0].name == "user@example.com"

    def test_parse_assignedTo_as_dict(self, parser: SmartsheetParser) -> None:
        """Test assignedTo field as dictionary."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "assignedTo": {
                        "id": "user123",
                        "name": "John Doe",
                        "email": "john@example.com",
                    },
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 1
        assert project.resources[0].name == "John Doe"

    def test_parse_duplicate_resources(self, parser: SmartsheetParser) -> None:
        """Test same user assigned to multiple rows creates one resource."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "assignedTo": "alice@example.com",
                    "cells": [{"columnId": 1, "value": "Task 1"}],
                },
                {
                    "id": 2,
                    "assignedTo": "alice@example.com",
                    "cells": [{"columnId": 1, "value": "Task 2"}],
                },
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 1

    def test_parse_row_with_no_assignee(self, parser: SmartsheetParser) -> None:
        """Test row without assignee creates no resource."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "cells": [{"columnId": 1, "value": "Unassigned task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 0

    def test_parse_date_formats(self, parser: SmartsheetParser) -> None:
        """Test parsing different date formats."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "cells": [
                        {"columnId": 1, "value": "ISO date"},
                        {"columnId": 2, "columnType": "DATE", "value": "2025-01-15"},
                    ],
                },
                {
                    "id": 2,
                    "cells": [
                        {"columnId": 1, "value": "ISO timestamp"},
                        {
                            "columnId": 2,
                            "columnType": "DATE",
                            "value": "2025-01-15T10:30:00",
                        },
                    ],
                },
            ],
        }

        project = parser.parse(data)
        tasks = project.tasks

        # All should parse to same date
        for task in tasks:
            if task.start_date:
                assert task.start_date.year == 2025
                assert task.start_date.month == 1
                assert task.start_date.day == 15

    def test_parse_invalid_date(self, parser: SmartsheetParser) -> None:
        """Test invalid date format returns None."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "cells": [
                        {"columnId": 1, "value": "Task"},
                        {
                            "columnId": 2,
                            "columnType": "DATE",
                            "value": "not-a-date",
                        },
                    ],
                }
            ],
        }

        project = parser.parse(data)
        task = project.tasks[0]
        assert task.start_date is None

    def test_parse_without_data_wrapper(self, parser: SmartsheetParser) -> None:
        """Test parsing data without 'data' wrapper."""
        data = {
            "id": "123",
            "name": "Direct Sheet",
            "rows": [
                {
                    "id": 1,
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert project.name == "Direct Sheet"
        assert len(project.tasks) == 1

    def test_parse_direct_field_values(self, parser: SmartsheetParser) -> None:
        """Test parsing when values are direct fields not in cells."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "name": "Task from field",
                    "percentComplete": 75.0,
                    "start": "2025-01-01",
                    "end": "2025-01-31",
                }
            ],
        }

        project = parser.parse(data)
        task = project.tasks[0]
        assert task.name == "Task from field"
        assert task.percent_complete == 75.0
        assert task.start_date is not None
        assert task.finish_date is not None

    def test_parse_invalid_percent_complete(self, parser: SmartsheetParser) -> None:
        """Test invalid percent complete defaults to 0."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "percentComplete": "not-a-number",
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        task = project.tasks[0]
        assert task.percent_complete == 0.0

    def test_parse_assignedTo_without_id(self, parser: SmartsheetParser) -> None:
        """Test assignedTo dict without id uses email."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "assignedTo": {
                        "name": "John Doe",
                        "email": "john@example.com",
                    },
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 1
        assert project.resources[0].name == "John Doe"

    def test_parse_assignedTo_as_invalid_type(
        self, parser: SmartsheetParser
    ) -> None:
        """Test assignedTo as invalid type creates no resource."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "assignedTo": 12345,  # Invalid type
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        assert len(project.resources) == 0

    def test_parse_date_as_non_string(self, parser: SmartsheetParser) -> None:
        """Test date value as non-string returns None."""
        data = {
            "id": "123",
            "name": "Test",
            "rows": [
                {
                    "id": 1,
                    "start": 12345,  # Non-string date
                    "cells": [{"columnId": 1, "value": "Task"}],
                }
            ],
        }

        project = parser.parse(data)
        task = project.tasks[0]
        assert task.start_date is None
