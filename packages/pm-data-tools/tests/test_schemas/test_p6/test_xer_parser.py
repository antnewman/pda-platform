"""Tests for P6 XER parser."""

from pathlib import Path

import pytest

from pm_data_tools.models import DependencyType, ResourceType, TaskStatus
from pm_data_tools.schemas.p6.xer_parser import XERParser


@pytest.fixture
def simple_xer_file() -> Path:
    """Path to simple XER test file."""
    return Path(__file__).parent.parent.parent / "fixtures" / "p6" / "simple_project.xer"


class TestXERParser:
    """Tests for XER parser."""

    def test_parse_simple_project(self, simple_xer_file: Path) -> None:
        """Test parsing a simple XER file."""
        parser = XERParser(simple_xer_file)
        project = parser.parse()

        # Check project metadata
        assert project.name == "Simple Project"
        assert project.source.tool == "primavera-p6"
        assert project.source.tool_version == "p6"
        assert project.source.original_id == "1"

        # Check dates
        assert project.start_date is not None
        assert project.finish_date is not None

    def test_parse_tasks(self, simple_xer_file: Path) -> None:
        """Test parsing tasks from XER."""
        parser = XERParser(simple_xer_file)
        project = parser.parse()

        assert len(project.tasks) == 3

        # Check first task
        task1 = project.tasks[0]
        assert task1.name == "Task 1"
        assert task1.status == TaskStatus.NOT_STARTED
        assert task1.percent_complete == 0.0

        # Check second task
        task2 = project.tasks[1]
        assert task2.name == "Task 2"
        assert task2.status == TaskStatus.IN_PROGRESS
        assert task2.percent_complete == 50.0

        # Check third task
        task3 = project.tasks[2]
        assert task3.name == "Task 3"
        assert task3.status == TaskStatus.COMPLETED
        assert task3.percent_complete == 100.0

    def test_parse_resources(self, simple_xer_file: Path) -> None:
        """Test parsing resources from XER."""
        parser = XERParser(simple_xer_file)
        project = parser.parse()

        assert len(project.resources) == 3

        # Check labor resource
        labor = project.resources[0]
        assert labor.name == "John Doe"
        assert labor.resource_type == ResourceType.WORK

        # Check equipment resource
        equipment = project.resources[1]
        assert equipment.name == "Equipment"
        assert equipment.resource_type == ResourceType.EQUIPMENT

        # Check material resource
        material = project.resources[2]
        assert material.name == "Materials"
        assert material.resource_type == ResourceType.MATERIAL

    def test_parse_dependencies(self, simple_xer_file: Path) -> None:
        """Test parsing dependencies from XER."""
        parser = XERParser(simple_xer_file)
        project = parser.parse()

        assert len(project.dependencies) == 2

        # Check first dependency
        dep1 = project.dependencies[0]
        assert dep1.dependency_type == DependencyType.FINISH_TO_START

        # Check second dependency
        dep2 = project.dependencies[1]
        assert dep2.dependency_type == DependencyType.FINISH_TO_START

    def test_parse_project_dates(self, simple_xer_file: Path) -> None:
        """Test parsing project start and finish dates."""
        parser = XERParser(simple_xer_file)
        project = parser.parse()

        assert project.start_date is not None
        assert project.start_date.year == 2025
        assert project.start_date.month == 1
        assert project.start_date.day == 1

        assert project.finish_date is not None
        assert project.finish_date.year == 2025
        assert project.finish_date.month == 1
        assert project.finish_date.day == 31


class TestXERFileStructure:
    """Tests for XER file structure parsing."""

    def test_read_xer_tables(self, simple_xer_file: Path) -> None:
        """Test reading XER file tables."""
        parser = XERParser(simple_xer_file)
        parser._read_xer_file()

        # Check that expected tables were parsed
        assert "PROJECT" in parser.tables
        assert "TASK" in parser.tables
        assert "TASKPRED" in parser.tables
        assert "RSRC" in parser.tables

        # Check PROJECT table
        assert len(parser.tables["PROJECT"]) == 1
        assert parser.tables["PROJECT"][0]["proj_short_name"] == "Simple Project"

        # Check TASK table
        assert len(parser.tables["TASK"]) == 3

        # Check TASKPRED table
        assert len(parser.tables["TASKPRED"]) == 2

        # Check RSRC table
        assert len(parser.tables["RSRC"]) == 3


class TestXERParserEdgeCases:
    """Tests for XER parser edge cases."""

    def test_parse_xer_with_empty_lines(self, tmp_path: Path) -> None:
        """Test parsing XER file with empty lines (line 106)."""
        xer_file = tmp_path / "empty_lines.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "\n"  # Empty line
            "%R\t1\tTest\n"
            "\n"  # Another empty line
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\n"
            "%R\t1\tT1\n"
        )

        parser = XERParser(xer_file)
        parser._read_xer_file()
        # Should skip empty lines and parse successfully
        assert "PROJECT" in parser.tables
        assert "TASK" in parser.tables

    def test_parse_xer_with_malformed_table_definition(self, tmp_path: Path) -> None:
        """Test parsing XER with malformed table definition (line 112->103)."""
        xer_file = tmp_path / "malformed.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\n"  # Table definition with no name
            "%F\tfield1\tfield2\n"
            "%R\tvalue1\tvalue2\n"
        )

        parser = XERParser(xer_file)
        parser._read_xer_file()
        # Should handle gracefully (current_table will be None)

    def test_parse_project_missing_fields(self, tmp_path: Path) -> None:
        """Test parsing project with missing optional fields."""
        xer_file = tmp_path / "minimal.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tMinimal\n"  # No dates or other fields
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\n"
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should parse with minimal fields
        assert project.name == "Minimal"
        assert project.start_date is None
        assert project.finish_date is None

    def test_parse_task_invalid_dates(self, tmp_path: Path) -> None:
        """Test parsing tasks with invalid date formats."""
        xer_file = tmp_path / "invalid_dates.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\ttask_name\ttarget_start_date\ttarget_end_date\n"
            "%R\t1\tT1\tTask 1\tinvalid-date\talso-invalid\n"  # Invalid dates
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should handle invalid dates gracefully
        assert len(project.tasks) == 1
        assert project.tasks[0].start_date is None
        assert project.tasks[0].finish_date is None

    def test_parse_resource_missing_type(self, tmp_path: Path) -> None:
        """Test parsing resource without rsrc_type field."""
        xer_file = tmp_path / "no_type.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tRSRC\n"
            "%F\trsrc_id\trsrc_short_name\n"  # No rsrc_type
            "%R\t1\tWorker\n"
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should default to WORK type
        assert len(project.resources) == 1
        assert project.resources[0].resource_type == ResourceType.WORK

    def test_parse_dependency_invalid_type(self, tmp_path: Path) -> None:
        """Test parsing dependency with invalid pred_type."""
        xer_file = tmp_path / "invalid_dep.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\ttask_name\n"
            "%R\t1\tT1\tTask 1\n"
            "%R\t2\tT2\tTask 2\n"
            "%T\tTASKPRED\n"
            "%F\ttask_pred_id\ttask_id\tpred_task_id\tpred_type\n"
            "%R\t1\t2\t1\t99\n"  # Invalid pred_type
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should default to FINISH_TO_START
        assert len(project.dependencies) == 1
        assert project.dependencies[0].dependency_type == DependencyType.FINISH_TO_START

    def test_parse_dependency_types(self, tmp_path: Path) -> None:
        """Test parsing all dependency types (lines 295, 297, 299)."""
        xer_file = tmp_path / "dep_types.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\ttask_name\n"
            "%R\t1\tT1\tTask 1\n"
            "%R\t2\tT2\tTask 2\n"
            "%R\t3\tT3\tTask 3\n"
            "%R\t4\tT4\tTask 4\n"
            "%T\tTASKPRED\n"
            "%F\ttask_pred_id\ttask_id\tpred_task_id\tpred_type\n"
            "%R\t1\t2\t1\tPR_FF\n"  # Finish to Finish
            "%R\t2\t3\t1\tPR_SS\n"  # Start to Start
            "%R\t3\t4\t1\tPR_SF\n"  # Start to Finish
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        assert len(project.dependencies) == 3
        # Check each type
        deps = project.dependencies
        assert any(d.dependency_type == DependencyType.FINISH_TO_FINISH for d in deps)
        assert any(d.dependency_type == DependencyType.START_TO_START for d in deps)
        assert any(d.dependency_type == DependencyType.START_TO_FINISH for d in deps)

    def test_parse_xer_no_project_table(self, tmp_path: Path) -> None:
        """Test parsing XER without PROJECT table (line 139)."""
        xer_file = tmp_path / "no_project.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\n"
            "%R\t1\tT1\n"
        )

        parser = XERParser(xer_file)
        with pytest.raises(ValueError, match="No PROJECT table"):
            parser.parse()

    def test_parse_resource_no_table(self, tmp_path: Path) -> None:
        """Test parsing when RSRC table doesn't exist (line 184)."""
        xer_file = tmp_path / "no_rsrc.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            # No RSRC table
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should handle gracefully
        assert len(project.resources) == 0

    def test_parse_date_exception_handling(self, tmp_path: Path) -> None:
        """Test date parsing with exception (lines 355-357)."""
        xer_file = tmp_path / "bad_dates.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\tplan_start_date\n"
            "%R\t1\tTest\t\n"  # Empty date field that might cause exception
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should handle gracefully
        assert project.start_date is None

    def test_parse_task_with_wbs(self, tmp_path: Path) -> None:
        """Test parsing task with WBS ID (line 184)."""
        xer_file = tmp_path / "with_wbs.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\ttask_name\twbs_id\n"
            "%R\t1\tT1\tTask 1\t100\n"  # Has WBS ID
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should parse successfully (WBS hierarchy not yet implemented)
        assert len(project.tasks) == 1

    def test_parse_resource_equipment_type(self, tmp_path: Path) -> None:
        """Test parsing equipment resource type (branch 246->249)."""
        xer_file = tmp_path / "equipment.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tTASK\n"
            "%F\ttask_id\ttask_code\n"
            "%T\tRSRC\n"
            "%F\trsrc_id\trsrc_name\trsrc_type\n"
            "%R\t1\tCrane\tRT_Equip\n"  # Equipment type
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        assert len(project.resources) == 1
        assert project.resources[0].resource_type == ResourceType.EQUIPMENT

    def test_parse_date_no_match(self, tmp_path: Path) -> None:
        """Test date parsing when no format matches (line 355)."""
        xer_file = tmp_path / "weird_date.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\tplan_start_date\n"
            "%R\t1\tTest\t99/99/9999\n"  # No format will match this
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        # Should return None gracefully
        assert project.start_date is None

    def test_parse_resource_unknown_type(self, tmp_path: Path) -> None:
        """Test parsing resource with unknown type defaults to WORK (line 240->249)."""
        xer_file = tmp_path / "unknown_rsrc_type.xer"
        xer_file.write_text(
            "ERMHDR\t\n"
            "%T\tPROJECT\n"
            "%F\tproj_id\tproj_short_name\n"
            "%R\t1\tTest\n"
            "%T\tRSRC\n"
            "%F\trsrc_id\trsrc_name\trsrc_type\n"
            "%R\t1\tWorker\tRT_Unknown\n"  # Unknown type
        )

        parser = XERParser(xer_file)
        project = parser.parse()
        assert len(project.resources) == 1
        # Should default to WORK
        assert project.resources[0].resource_type == ResourceType.WORK
