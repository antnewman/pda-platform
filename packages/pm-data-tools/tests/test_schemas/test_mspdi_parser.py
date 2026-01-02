"""Tests for MSPDI parser."""

import pytest
from pathlib import Path
from decimal import Decimal

from pm_data_tools.schemas.mspdi.parser import MspdiParser
from pm_data_tools.models.task import TaskStatus
from pm_data_tools.models.dependency import DependencyType
from pm_data_tools.models.resource import ResourceType


@pytest.fixture
def parser() -> MspdiParser:
    """MSPDI parser instance."""
    return MspdiParser()


@pytest.fixture
def simple_project_file() -> Path:
    """Path to simple project fixture."""
    return Path(__file__).parent.parent / "fixtures" / "mspdi" / "simple_project.xml"


@pytest.fixture
def complex_project_file() -> Path:
    """Path to complex project fixture."""
    return Path(__file__).parent.parent / "fixtures" / "mspdi" / "complex_project.xml"


class TestMspdiParserBasic:
    """Tests for basic MSPDI parsing."""

    def test_parse_simple_project_file(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing simple project file."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert project.name == "Simple Test Project"
        assert project.description == "A simple test project"
        assert project.project_manager == "John Smith"
        assert project.department == "Test Company"

    def test_parse_project_dates(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing project dates."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert project.start_date is not None
        assert project.start_date.year == 2025
        assert project.start_date.month == 1
        assert project.start_date.day == 1

        assert project.finish_date is not None
        assert project.finish_date.year == 2025
        assert project.finish_date.month == 1
        assert project.finish_date.day == 10

    def test_parse_project_custom_fields(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing custom fields."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.custom_fields) > 0

        # Check author custom field
        author_field = next(
            (cf for cf in project.custom_fields if cf.name == "author"), None
        )
        assert author_field is not None
        assert author_field.value == "Test Author"

    def test_parse_invalid_file_returns_none(self, parser: MspdiParser) -> None:
        """Test parsing invalid file returns None."""
        result = parser.parse_file("nonexistent.xml")
        assert result is None

    def test_parse_string(self, parser: MspdiParser) -> None:
        """Test parsing XML string."""
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
  <Name>Test</Name>
  <UID>1</UID>
  <SaveVersion>14</SaveVersion>
</Project>"""

        project = parser.parse_string(xml_str)
        assert project is not None
        assert project.name == "Test"


class TestMspdiParserTasks:
    """Tests for parsing tasks."""

    def test_parse_tasks(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing tasks."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.tasks) == 3

    def test_parse_task_basic_fields(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task basic fields."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.name == "Task 1"
        assert task.wbs_code == "1"
        assert task.outline_level == 1
        assert task.notes == "This is task 1"

    def test_parse_task_dates(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task dates."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.start_date is not None
        assert task.finish_date is not None
        assert task.start_date.year == 2025
        assert task.start_date.month == 1
        assert task.start_date.day == 1

    def test_parse_task_duration(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task duration."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.duration is not None
        assert task.duration.value == 16.0
        assert task.duration.unit == "hours"

    def test_parse_task_progress(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task progress."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.percent_complete == 50.0
        assert task.status == TaskStatus.IN_PROGRESS

    def test_parse_task_flags(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task flags."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task1 = project.tasks[0]
        assert task1.is_milestone is False
        assert task1.is_critical is True
        assert task1.is_summary is False

        milestone = project.tasks[2]
        assert milestone.is_milestone is True

    def test_parse_task_work(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task work."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.budgeted_work is not None
        assert task.budgeted_work.value == 16.0  # 960 minutes = 16 hours
        assert task.actual_work is not None
        assert task.actual_work.value == 8.0  # 480 minutes = 8 hours

    def test_parse_task_cost(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing task cost."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        task = project.tasks[0]
        assert task.budgeted_cost is not None
        assert task.budgeted_cost.amount == Decimal("1000.00")
        assert task.budgeted_cost.currency == "GBP"
        assert task.actual_cost is not None
        assert task.actual_cost.amount == Decimal("500.00")

    def test_parse_summary_task(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing summary task."""
        project = parser.parse_file(complex_project_file)

        assert project is not None
        summary = next((t for t in project.tasks if t.is_summary), None)
        assert summary is not None
        assert summary.name == "Phase 1: Planning"
        assert summary.is_summary is True

    def test_parse_task_hierarchy(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing task hierarchy."""
        project = parser.parse_file(complex_project_file)

        assert project is not None

        # Find parent and child
        parent = next((t for t in project.tasks if t.source.original_id == "1"), None)
        child = next((t for t in project.tasks if t.source.original_id == "2"), None)

        assert parent is not None
        assert child is not None
        assert child.parent_id == parent.id
        assert child.outline_level == 2

    def test_parse_task_actual_dates(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing task actual and baseline dates."""
        project = parser.parse_file(complex_project_file)

        assert project is not None
        task = next(
            (t for t in project.tasks if t.source.original_id == "2"), None
        )

        assert task is not None
        assert task.actual_start is not None
        assert task.actual_finish is not None


class TestMspdiParserResources:
    """Tests for parsing resources."""

    def test_parse_resources(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing resources."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.resources) == 2

    def test_parse_resource_basic_fields(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing resource basic fields."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        resource = project.resources[0]
        assert resource.name == "Developer 1"
        assert resource.email == "dev1@test.com"
        assert resource.resource_type == ResourceType.WORK

    def test_parse_resource_availability(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing resource availability."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        resource = project.resources[0]
        assert resource.max_units == 1.0

    def test_parse_resource_cost(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing resource cost."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        resource = project.resources[0]
        assert resource.standard_rate is not None
        assert resource.standard_rate.amount == Decimal("50.00")

    def test_parse_different_resource_types(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing different resource types."""
        project = parser.parse_file(complex_project_file)

        assert project is not None

        # Work resource
        work_resource = next(
            (r for r in project.resources if r.source.original_id == "1"), None
        )
        assert work_resource is not None
        assert work_resource.resource_type == ResourceType.WORK

        # Material resource
        material_resource = next(
            (r for r in project.resources if r.source.original_id == "4"), None
        )
        assert material_resource is not None
        assert material_resource.resource_type == ResourceType.MATERIAL

        # Cost resource
        cost_resource = next(
            (r for r in project.resources if r.source.original_id == "5"), None
        )
        assert cost_resource is not None
        assert cost_resource.resource_type == ResourceType.COST


class TestMspdiParserAssignments:
    """Tests for parsing assignments."""

    def test_parse_assignments(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing assignments."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.assignments) == 2

    def test_parse_assignment_fields(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing assignment fields."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assignment = project.assignments[0]
        assert assignment.units == 1.0
        assert assignment.budgeted_work is not None
        assert assignment.budgeted_work.value == 16.0  # 960 minutes
        assert assignment.budgeted_cost is not None
        assert assignment.budgeted_cost.amount == Decimal("800.00")

    def test_parse_assignment_references(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test assignment task and resource references."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assignment = project.assignments[0]

        # Verify task reference
        task = next((t for t in project.tasks if t.id == assignment.task_id), None)
        assert task is not None
        assert task.source.original_id == "1"

        # Verify resource reference
        resource = next(
            (r for r in project.resources if r.id == assignment.resource_id), None
        )
        assert resource is not None
        assert resource.source.original_id == "1"


class TestMspdiParserDependencies:
    """Tests for parsing dependencies."""

    def test_parse_dependencies(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing dependencies."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.dependencies) == 2

    def test_parse_finish_to_start_dependency(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing FS dependency."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        # Task 2 depends on Task 1 (FS)
        dep = next(
            (
                d
                for d in project.dependencies
                if d.source.original_id == "1-2"
            ),
            None,
        )

        assert dep is not None
        assert dep.dependency_type == DependencyType.FINISH_TO_START
        assert dep.lag is None or dep.lag.value == 0

    def test_parse_start_to_start_dependency(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing SS dependency."""
        project = parser.parse_file(complex_project_file)

        assert project is not None
        # Task 3 depends on Task 2 (SS with lag)
        dep = next(
            (
                d
                for d in project.dependencies
                if d.source.original_id == "2-3"
            ),
            None,
        )

        assert dep is not None
        assert dep.dependency_type == DependencyType.START_TO_START
        assert dep.lag is not None
        assert dep.lag.value == 16.0  # 960 minutes = 16 hours

    def test_parse_dependency_references(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test dependency task references."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        dep = project.dependencies[0]

        # Verify predecessor reference
        predecessor = next(
            (t for t in project.tasks if t.id == dep.predecessor_id), None
        )
        assert predecessor is not None

        # Verify successor reference
        successor = next((t for t in project.tasks if t.id == dep.successor_id), None)
        assert successor is not None


class TestMspdiParserCalendars:
    """Tests for parsing calendars."""

    def test_parse_calendars(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing calendars."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        assert len(project.calendars) == 1

    def test_parse_calendar_fields(
        self, parser: MspdiParser, simple_project_file: Path
    ) -> None:
        """Test parsing calendar fields."""
        project = parser.parse_file(simple_project_file)

        assert project is not None
        calendar = project.calendars[0]
        assert calendar.name == "Standard"

    def test_parse_multiple_calendars(
        self, parser: MspdiParser, complex_project_file: Path
    ) -> None:
        """Test parsing multiple calendars."""
        project = parser.parse_file(complex_project_file)

        assert project is not None
        assert len(project.calendars) == 2

        calendar_names = {c.name for c in project.calendars}
        assert "Standard" in calendar_names
        assert "24 Hour" in calendar_names


class TestMspdiParserMalformedXML:
    """Tests for MSPDI parser handling malformed XML."""

    def test_parse_invalid_xml(self, parser: MspdiParser) -> None:
        """Test parsing invalid XML returns None (line 90)."""
        invalid_xml = "<Project><broken"
        result = parser.parse_string(invalid_xml)
        assert result is None

    def test_parse_task_without_uid(self, parser: MspdiParser) -> None:
        """Test parsing task without UID is skipped (line 220)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Tasks>
        <Task>
            <Name>Task without UID</Name>
        </Task>
    </Tasks>
</Project>"""
        project = parser.parse_string(xml)
        # Task without UID should be skipped
        assert project is not None
        assert len(project.tasks) == 0

    def test_parse_resource_without_uid(self, parser: MspdiParser) -> None:
        """Test parsing resource without UID is skipped (line 362)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Resources>
        <Resource>
            <Name>Resource without UID</Name>
        </Resource>
    </Resources>
</Project>"""
        project = parser.parse_string(xml)
        # Resource without UID should be skipped
        assert project is not None
        assert len(project.resources) == 0

    def test_parse_assignment_without_uid(self, parser: MspdiParser) -> None:
        """Test parsing assignment without UID is skipped (line 444)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Assignments>
        <Assignment>
            <TaskUID>1</TaskUID>
            <ResourceUID>1</ResourceUID>
        </Assignment>
    </Assignments>
</Project>"""
        project = parser.parse_string(xml)
        # Assignment without UID should be skipped
        assert project is not None
        assert len(project.assignments) == 0

    def test_parse_assignment_without_task_or_resource_uid(
        self, parser: MspdiParser
    ) -> None:
        """Test parsing assignment without TaskUID or ResourceUID (line 451)."""
        xml_no_task = """<?xml version="1.0"?>
<Project>
    <Assignments>
        <Assignment>
            <UID>1</UID>
            <ResourceUID>1</ResourceUID>
        </Assignment>
    </Assignments>
</Project>"""
        project = parser.parse_string(xml_no_task)
        assert project is not None
        assert len(project.assignments) == 0

        xml_no_resource = """<?xml version="1.0"?>
<Project>
    <Assignments>
        <Assignment>
            <UID>1</UID>
            <TaskUID>1</TaskUID>
        </Assignment>
    </Assignments>
</Project>"""
        project = parser.parse_string(xml_no_resource)
        assert project is not None
        assert len(project.assignments) == 0

    def test_parse_dependency_task_without_uid(self, parser: MspdiParser) -> None:
        """Test parsing dependencies when task has no UID (line 519)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Tasks>
        <Task>
            <Name>Task without UID</Name>
            <PredecessorLink>
                <PredecessorUID>1</PredecessorUID>
            </PredecessorLink>
        </Task>
    </Tasks>
</Project>"""
        project = parser.parse_string(xml)
        assert project is not None
        # Task without UID should be skipped, so no dependencies
        assert len(project.dependencies) == 0

    def test_parse_dependency_without_predecessor_uid(
        self, parser: MspdiParser
    ) -> None:
        """Test parsing PredecessorLink without PredecessorUID (line 527)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Tasks>
        <Task>
            <UID>1</UID>
            <Name>Task 1</Name>
            <PredecessorLink>
                <Type>1</Type>
            </PredecessorLink>
        </Task>
    </Tasks>
</Project>"""
        project = parser.parse_string(xml)
        assert project is not None
        # PredecessorLink without UID should be skipped
        assert len(project.dependencies) == 0

    def test_parse_calendar_without_uid(self, parser: MspdiParser) -> None:
        """Test parsing calendar without UID is skipped (line 602)."""
        xml = """<?xml version="1.0"?>
<Project>
    <Calendars>
        <Calendar>
            <Name>Calendar without UID</Name>
        </Calendar>
    </Calendars>
</Project>"""
        project = parser.parse_string(xml)
        # Calendar without UID should be skipped
        assert project is not None
        assert len(project.calendars) == 0
