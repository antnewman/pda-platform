"""Tests for MSPDI writer."""

import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from lxml import etree

from pm_data_tools.schemas.mspdi.writer import MspdiWriter
from pm_data_tools.models import (
    Project,
    Task,
    Resource,
    Assignment,
    Dependency,
    Calendar,
    SourceInfo,
    Duration,
    Money,
    CustomField,
    DeliveryConfidence,
)
from pm_data_tools.models.task import TaskStatus, ConstraintType
from pm_data_tools.models.dependency import DependencyType
from pm_data_tools.models.resource import ResourceType
from pm_data_tools.utils.xml_helpers import parse_xml_string, get_text, get_int, strip_namespaces


@pytest.fixture
def writer() -> MspdiWriter:
    """MSPDI writer instance."""
    return MspdiWriter()


@pytest.fixture
def simple_project() -> Project:
    """Create a simple project for testing."""
    task1_id = uuid4()
    task2_id = uuid4()
    resource1_id = uuid4()

    task1 = Task(
        id=task1_id,
        name="Task 1",
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="1"),
        wbs_code="1",
        outline_level=1,
        start_date=datetime(2025, 1, 1, 9, 0),
        finish_date=datetime(2025, 1, 2, 17, 0),
        duration=Duration(16.0, "hours"),
        percent_complete=50.0,
        status=TaskStatus.IN_PROGRESS,
        is_milestone=False,
        is_critical=True,
        budgeted_work=Duration(16.0, "hours"),
        budgeted_cost=Money(Decimal("1000.00"), "GBP"),
        notes="Test task",
    )

    task2 = Task(
        id=task2_id,
        name="Task 2",
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="2"),
        wbs_code="2",
        outline_level=1,
        start_date=datetime(2025, 1, 3, 9, 0),
        finish_date=datetime(2025, 1, 3, 17, 0),
        duration=Duration(8.0, "hours"),
        percent_complete=0.0,
        status=TaskStatus.NOT_STARTED,
        is_milestone=False,
        is_critical=True,
        budgeted_work=Duration(8.0, "hours"),
        budgeted_cost=Money(Decimal("500.00"), "GBP"),
    )

    resource1 = Resource(
        id=resource1_id,
        name="Developer 1",
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="1"),
        resource_type=ResourceType.WORK,
        email="dev1@test.com",
        max_units=1.0,
        standard_rate=Money(Decimal("50.00"), "GBP"),
    )

    assignment1 = Assignment(
        id=uuid4(),
        task_id=task1_id,
        resource_id=resource1_id,
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="1"),
        units=1.0,
        budgeted_work=Duration(16.0, "hours"),
        budgeted_cost=Money(Decimal("800.00"), "GBP"),
    )

    dependency1 = Dependency(
        id=uuid4(),
        predecessor_id=task1_id,
        successor_id=task2_id,
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="dep-1-2"),
        dependency_type=DependencyType.FINISH_TO_START,
    )

    calendar1 = Calendar(
        id=uuid4(),
        name="Standard",
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="1"),
        working_days=[0, 1, 2, 3, 4],  # Monday to Friday
    )

    return Project(
        id=uuid4(),
        name="Test Project",
        source=SourceInfo(tool="mspdi", tool_version="14", original_id="1"),
        start_date=datetime(2025, 1, 1, 9, 0),
        finish_date=datetime(2025, 1, 10, 17, 0),
        description="Test description",
        project_manager="Test Manager",
        department="Test Company",
        tasks=[task1, task2],
        resources=[resource1],
        assignments=[assignment1],
        dependencies=[dependency1],
        calendars=[calendar1],
        custom_fields=[
            CustomField(
                name="author",
                value="Test Author",
                field_type="text",
                source_tool="mspdi",
            )
        ],
        delivery_confidence=DeliveryConfidence.GREEN,
    )


class TestMspdiWriterBasic:
    """Tests for basic MSPDI writing."""

    def test_write_string(self, writer: MspdiWriter, simple_project: Project) -> None:
        """Test writing project to XML string."""
        xml_bytes = writer.write_string(simple_project)

        assert xml_bytes is not None
        assert isinstance(xml_bytes, bytes)
        assert b"<?xml" in xml_bytes
        assert b"<Project" in xml_bytes

    def test_write_file(
        self, writer: MspdiWriter, simple_project: Project, tmp_path: Path
    ) -> None:
        """Test writing project to file."""
        output_file = tmp_path / "test_output.xml"
        writer.write_file(simple_project, output_file)

        assert output_file.exists()
        content = output_file.read_bytes()
        assert b"<Project" in content

    def test_write_project_metadata(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing project metadata."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assert get_text(root, "Name") == "Test Project"
        assert get_text(root, "Title") == "Test description"
        assert get_text(root, "Manager") == "Test Manager"
        assert get_text(root, "Company") == "Test Company"

    def test_write_project_dates(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing project dates."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assert get_text(root, "StartDate") == "2025-01-01T09:00:00"
        assert get_text(root, "FinishDate") == "2025-01-10T17:00:00"

    def test_write_project_custom_fields(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing custom fields."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assert get_text(root, "Author") == "Test Author"

    def test_write_currency(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing currency code."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assert get_text(root, "CurrencyCode") == "GBP"


class TestMspdiWriterTasks:
    """Tests for writing tasks."""

    def test_write_tasks(self, writer: MspdiWriter, simple_project: Project) -> None:
        """Test writing tasks."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elems = tasks_elem.findall("Task")
        assert len(task_elems) == 2

    def test_write_task_basic_fields(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task basic fields."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "UID") == "1"
        assert get_text(task_elem, "Name") == "Task 1"
        assert get_text(task_elem, "WBS") == "1"
        assert get_int(task_elem, "OutlineLevel") == 1

    def test_write_task_dates(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task dates."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "Start") == "2025-01-01T09:00:00"
        assert get_text(task_elem, "Finish") == "2025-01-02T17:00:00"

    def test_write_task_duration(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task duration."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "Duration") == "PT16H0M0S"

    def test_write_task_progress(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task progress."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_int(task_elem, "PercentComplete") == 50

    def test_write_task_flags(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task flags."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "Milestone") == "0"
        assert get_text(task_elem, "Critical") == "1"

    def test_write_task_work(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task work."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        # Work should be in minutes: 16 hours = 960 minutes
        assert get_int(task_elem, "Work") == 960

    def test_write_task_cost(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task cost."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "Cost") == "1000.0"

    def test_write_task_notes(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing task notes."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elem = tasks_elem.find("Task")
        assert task_elem is not None

        assert get_text(task_elem, "Notes") == "Test task"


class TestMspdiWriterResources:
    """Tests for writing resources."""

    def test_write_resources(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing resources."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        resources_elem = root.find("Resources")
        assert resources_elem is not None
        resource_elems = resources_elem.findall("Resource")
        assert len(resource_elems) == 1

    def test_write_resource_fields(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing resource fields."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        resources_elem = root.find("Resources")
        assert resources_elem is not None
        resource_elem = resources_elem.find("Resource")
        assert resource_elem is not None

        assert get_text(resource_elem, "UID") == "1"
        assert get_text(resource_elem, "Name") == "Developer 1"
        assert get_text(resource_elem, "EmailAddress") == "dev1@test.com"
        assert get_int(resource_elem, "Type") == 1  # Work resource
        assert get_text(resource_elem, "MaxUnits") == "1.0"


class TestMspdiWriterAssignments:
    """Tests for writing assignments."""

    def test_write_assignments(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing assignments."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assignments_elem = root.find("Assignments")
        assert assignments_elem is not None
        assignment_elems = assignments_elem.findall("Assignment")
        assert len(assignment_elems) == 1

    def test_write_assignment_fields(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing assignment fields."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assignments_elem = root.find("Assignments")
        assert assignments_elem is not None
        assignment_elem = assignments_elem.find("Assignment")
        assert assignment_elem is not None

        assert get_text(assignment_elem, "UID") == "1"
        assert get_text(assignment_elem, "Units") == "1.0"
        assert get_int(assignment_elem, "Work") == 960  # 16 hours in minutes


class TestMspdiWriterDependencies:
    """Tests for writing dependencies."""

    def test_write_dependencies_as_predecessor_links(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test dependencies written as PredecessorLink elements."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Dependencies are written as PredecessorLink in successor task
        tasks_elem = root.find("Tasks")
        assert tasks_elem is not None
        task_elems = tasks_elem.findall("Task")

        # Find Task 2 (successor)
        task2 = next(
            (t for t in task_elems if get_text(t, "UID") == "2"),
            None,
        )
        assert task2 is not None

        # Check PredecessorLink
        pred_link = task2.find("PredecessorLink")
        assert pred_link is not None
        assert get_text(pred_link, "PredecessorUID") == "1"
        assert get_int(pred_link, "Type") == 1  # FS


class TestMspdiWriterCalendars:
    """Tests for writing calendars."""

    def test_write_calendars(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing calendars."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        calendars_elem = root.find("Calendars")
        assert calendars_elem is not None
        calendar_elems = calendars_elem.findall("Calendar")
        assert len(calendar_elems) == 1

    def test_write_calendar_fields(
        self, writer: MspdiWriter, simple_project: Project
    ) -> None:
        """Test writing calendar fields."""
        xml_bytes = writer.write_string(simple_project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        calendars_elem = root.find("Calendars")
        assert calendars_elem is not None
        calendar_elem = calendars_elem.find("Calendar")
        assert calendar_elem is not None

        assert get_text(calendar_elem, "UID") == "1"
        assert get_text(calendar_elem, "Name") == "Standard"
        assert get_text(calendar_elem, "IsBaseCalendar") == "1"


class TestMspdiWriterOptionalFields:
    """Tests for MSPDI writer with optional/minimal fields."""

    def test_write_project_without_dates(self, writer: MspdiWriter) -> None:
        """Test writing project without start/finish/status dates (branches 88,92,96)."""
        project = Project(
            id=uuid4(),
            name="Minimal Project",
            source=SourceInfo(tool="test", original_id="1"),
            # No dates
            start_date=None,
            finish_date=None,
            status_date=None,
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Should not have date elements
        assert root.find("StartDate") is None
        assert root.find("FinishDate") is None
        assert root.find("StatusDate") is None

    def test_write_project_without_custom_fields(self, writer: MspdiWriter) -> None:
        """Test writing project without custom fields matching author/subject (branch 112->109)."""
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            custom_fields=[
                # Custom field that doesn't match "author" or "subject"
            ],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        # Should write successfully without author/subject elements

    def test_write_project_without_tasks(self, writer: MspdiWriter) -> None:
        """Test writing project without tasks (branch 116->122)."""
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[],  # Empty tasks
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Should not have Tasks element
        assert root.find("Tasks") is None

    def test_write_project_without_resources(self, writer: MspdiWriter) -> None:
        """Test writing project without resources (branch 122->128)."""
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            resources=[],  # Empty resources
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Should not have Resources element
        assert root.find("Resources") is None

    def test_write_project_without_assignments(self, writer: MspdiWriter) -> None:
        """Test writing project without assignments (branch 128->134)."""
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            assignments=[],  # Empty assignments
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Should not have Assignments element
        assert root.find("Assignments") is None

    def test_write_project_without_calendars(self, writer: MspdiWriter) -> None:
        """Test writing project without calendars (branch 134->139)."""
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            calendars=[],  # Empty calendars
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        # Should not have Calendars element
        assert root.find("Calendars") is None

    def test_write_task_without_wbs(self, writer: MspdiWriter) -> None:
        """Test writing task without WBS code (branch 158->160)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
            wbs_code=None,  # No WBS
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have WBS element
        assert task_elem.find("WBS") is None

    def test_write_task_without_parent(self, writer: MspdiWriter) -> None:
        """Test writing task without parent (branch 167->173)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
            parent_id=None,  # No parent
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have OutlineParent element
        assert task_elem.find("OutlineParent") is None

    def test_write_task_without_dates(self, writer: MspdiWriter) -> None:
        """Test writing task without dates (branches 173,175,179)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
            start_date=None,
            finish_date=None,
            actual_start=None,
            actual_finish=None,
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have date elements
        assert task_elem.find("Start") is None
        assert task_elem.find("Finish") is None
        assert task_elem.find("ActualStart") is None
        assert task_elem.find("ActualFinish") is None

    def test_write_task_without_duration(self, writer: MspdiWriter) -> None:
        """Test writing task without duration (branch 189->193)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
            duration=None,  # No duration
            actual_duration=None,
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have Duration element
        assert task_elem.find("Duration") is None

    def test_write_resource_with_different_types(self, writer: MspdiWriter) -> None:
        """Test writing resources with different types (branches 241,246,271)."""
        # Material resource
        material = Resource(
            id=uuid4(),
            name="Material",
            source=SourceInfo(tool="test", original_id="1"),
            resource_type=ResourceType.MATERIAL,
        )
        # Cost resource
        cost = Resource(
            id=uuid4(),
            name="Cost",
            source=SourceInfo(tool="test", original_id="2"),
            resource_type=ResourceType.COST,
        )
        # Equipment resource
        equipment = Resource(
            id=uuid4(),
            name="Equipment",
            source=SourceInfo(tool="test", original_id="3"),
            resource_type=ResourceType.EQUIPMENT,
        )

        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            resources=[material, cost, equipment],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        resources = root.findall(".//Resource")
        assert len(resources) == 3
        # Check that Type elements are written correctly
        types = [get_int(r, "Type", default=-1) for r in resources]
        assert 0 in types  # Material
        assert 2 in types  # Cost

    def test_write_assignment_without_cost(self, writer: MspdiWriter) -> None:
        """Test writing assignment without cost fields (branches 306,310,326)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
        )
        resource = Resource(
            id=uuid4(),
            name="Resource",
            source=SourceInfo(tool="test", original_id="1"),
        )
        assignment = Assignment(
            id=uuid4(),
            task_id=task.id,
            resource_id=resource.id,
            source=SourceInfo(tool="test", original_id="1"),
            budgeted_cost=None,  # No budgeted cost
            actual_cost=None,  # No actual cost
            budgeted_work=None,  # No budgeted work
        )

        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
            resources=[resource],
            assignments=[assignment],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        # Should write without cost elements

    def test_write_custom_field_not_author_or_subject(
        self, writer: MspdiWriter
    ) -> None:
        """Test custom field that is not author or subject (branch 112->109)."""
        from pm_data_tools.models.base import CustomField

        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            custom_fields=[
                CustomField(
                    name="other_field",  # Not "author" or "subject"
                    value="value",
                    field_type="text",
                    source_tool="test",
                )
            ],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        # Should skip this custom field

    def test_write_task_with_invalid_parent_id(self, writer: MspdiWriter) -> None:
        """Test task with parent_id that doesn't exist (branch 167->173)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
            parent_id=uuid4(),  # Parent doesn't exist in project
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have OutlineParent since parent not found
        assert task_elem.find("OutlineParent") is None

    def test_write_dependency_with_missing_predecessor(
        self, writer: MspdiWriter
    ) -> None:
        """Test dependency where predecessor task not found (branch 241->237)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
        )
        dep = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),  # Doesn't exist
            successor_id=task.id,
            source=SourceInfo(tool="test", original_id="1"),
            dependency_type=DependencyType.FINISH_TO_START,
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
            dependencies=[dep],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task")
        assert task_elem is not None
        # Should not have PredecessorLink since predecessor not found
        assert task_elem.find("PredecessorLink") is None

    def test_write_dependency_without_type(self, writer: MspdiWriter) -> None:
        """Test dependency without dependency_type (branch 246->249)."""
        task1 = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", original_id="1"),
        )
        task2 = Task(
            id=uuid4(),
            name="Task 2",
            source=SourceInfo(tool="test", original_id="2"),
        )
        dep = Dependency(
            id=uuid4(),
            predecessor_id=task1.id,
            successor_id=task2.id,
            source=SourceInfo(tool="test", original_id="1"),
            dependency_type=None,  # No type
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task1, task2],
            dependencies=[dep],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        task_elem = root.find(".//Task[Name='Task 2']")
        assert task_elem is not None
        pred_link = task_elem.find("PredecessorLink")
        assert pred_link is not None
        # Should not have Type element when dependency_type is None
        assert pred_link.find("Type") is None

    def test_write_resource_without_type(self, writer: MspdiWriter) -> None:
        """Test resource without resource_type (branch 271->276)."""
        resource = Resource(
            id=uuid4(),
            name="Resource",
            source=SourceInfo(tool="test", original_id="1"),
            resource_type=None,  # No type
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            resources=[resource],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        resource_elem = root.find(".//Resource")
        assert resource_elem is not None
        # Should not have Type element when resource_type is None
        assert resource_elem.find("Type") is None

    def test_write_assignment_with_missing_task(self, writer: MspdiWriter) -> None:
        """Test assignment where task not found (branch 306->309)."""
        resource = Resource(
            id=uuid4(),
            name="Resource",
            source=SourceInfo(tool="test", original_id="1"),
        )
        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),  # Task doesn't exist
            resource_id=resource.id,
            source=SourceInfo(tool="test", original_id="1"),
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            resources=[resource],
            assignments=[assignment],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assignment_elem = root.find(".//Assignment")
        assert assignment_elem is not None
        # Should not have TaskUID since task not found
        assert assignment_elem.find("TaskUID") is None

    def test_write_assignment_with_missing_resource(self, writer: MspdiWriter) -> None:
        """Test assignment where resource not found (branch 310->313)."""
        task = Task(
            id=uuid4(),
            name="Task",
            source=SourceInfo(tool="test", original_id="1"),
        )
        assignment = Assignment(
            id=uuid4(),
            task_id=task.id,
            resource_id=uuid4(),  # Resource doesn't exist
            source=SourceInfo(tool="test", original_id="1"),
        )
        project = Project(
            id=uuid4(),
            name="Project",
            source=SourceInfo(tool="test", original_id="1"),
            tasks=[task],
            assignments=[assignment],
        )

        xml_bytes = writer.write_string(project)
        root = parse_xml_string(xml_bytes)
        assert root is not None
        root = strip_namespaces(root)

        assignment_elem = root.find(".//Assignment")
        assert assignment_elem is not None
        # Should not have ResourceUID since resource not found
        assert assignment_elem.find("ResourceUID") is None
