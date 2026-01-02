"""Critical roundtrip tests for MSPDI schema.

These tests ensure that parse → write → parse preserves data integrity,
which is essential for lossless conversion workflows.
"""

import pytest
from pathlib import Path

from pm_data_tools.schemas.mspdi.parser import MspdiParser
from pm_data_tools.schemas.mspdi.writer import MspdiWriter


@pytest.fixture
def parser() -> MspdiParser:
    """MSPDI parser instance."""
    return MspdiParser()


@pytest.fixture
def writer() -> MspdiWriter:
    """MSPDI writer instance."""
    return MspdiWriter()


@pytest.fixture
def simple_project_file() -> Path:
    """Path to simple project fixture."""
    return Path(__file__).parent.parent / "fixtures" / "mspdi" / "simple_project.xml"


@pytest.fixture
def complex_project_file() -> Path:
    """Path to complex project fixture."""
    return Path(__file__).parent.parent / "fixtures" / "mspdi" / "complex_project.xml"


class TestMspdiRoundtripSimple:
    """Roundtrip tests for simple project."""

    def test_roundtrip_project_metadata(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test project metadata preserved in roundtrip."""
        # Parse original
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        # Write to XML
        xml_bytes = writer.write_string(project1)

        # Parse again
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Compare
        assert project2.name == project1.name
        assert project2.description == project1.description
        assert project2.project_manager == project1.project_manager
        assert project2.department == project1.department

    def test_roundtrip_project_dates(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test project dates preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert project2.start_date == project1.start_date
        assert project2.finish_date == project1.finish_date
        assert project2.status_date == project1.status_date

    def test_roundtrip_task_count(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task count preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert len(project2.tasks) == len(project1.tasks)

    def test_roundtrip_task_fields(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task fields preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Compare first task
        task1 = project1.tasks[0]
        task2 = next(
            (t for t in project2.tasks if t.source.original_id == task1.source.original_id),
            None,
        )
        assert task2 is not None

        assert task2.name == task1.name
        assert task2.wbs_code == task1.wbs_code
        assert task2.outline_level == task1.outline_level
        assert task2.percent_complete == task1.percent_complete
        assert task2.is_milestone == task1.is_milestone
        assert task2.is_critical == task1.is_critical

    def test_roundtrip_task_dates(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task dates preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        task1 = project1.tasks[0]
        task2 = next(
            (t for t in project2.tasks if t.source.original_id == task1.source.original_id),
            None,
        )
        assert task2 is not None

        assert task2.start_date == task1.start_date
        assert task2.finish_date == task1.finish_date

    def test_roundtrip_task_duration(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task duration preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        task1 = project1.tasks[0]
        task2 = next(
            (t for t in project2.tasks if t.source.original_id == task1.source.original_id),
            None,
        )
        assert task2 is not None

        assert task2.duration is not None
        assert task1.duration is not None
        assert task2.duration.value == task1.duration.value
        assert task2.duration.unit == task1.duration.unit

    def test_roundtrip_task_work(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task work preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        task1 = project1.tasks[0]
        task2 = next(
            (t for t in project2.tasks if t.source.original_id == task1.source.original_id),
            None,
        )
        assert task2 is not None

        assert task2.budgeted_work is not None
        assert task1.budgeted_work is not None
        assert task2.budgeted_work.to_hours() == task1.budgeted_work.to_hours()

    def test_roundtrip_task_cost(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test task cost preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        task1 = project1.tasks[0]
        task2 = next(
            (t for t in project2.tasks if t.source.original_id == task1.source.original_id),
            None,
        )
        assert task2 is not None

        assert task2.budgeted_cost is not None
        assert task1.budgeted_cost is not None
        assert task2.budgeted_cost.amount == task1.budgeted_cost.amount
        assert task2.budgeted_cost.currency == task1.budgeted_cost.currency

    def test_roundtrip_resource_count(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test resource count preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert len(project2.resources) == len(project1.resources)

    def test_roundtrip_resource_fields(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test resource fields preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        resource1 = project1.resources[0]
        resource2 = next(
            (
                r
                for r in project2.resources
                if r.source.original_id == resource1.source.original_id
            ),
            None,
        )
        assert resource2 is not None

        assert resource2.name == resource1.name
        assert resource2.email == resource1.email
        assert resource2.resource_type == resource1.resource_type
        assert resource2.max_units == resource1.max_units

    def test_roundtrip_assignment_count(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test assignment count preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert len(project2.assignments) == len(project1.assignments)

    def test_roundtrip_dependency_count(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test dependency count preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert len(project2.dependencies) == len(project1.dependencies)

    def test_roundtrip_dependency_type(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test dependency type preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        dep1 = project1.dependencies[0]
        # Match by source ID
        dep2 = next(
            (
                d
                for d in project2.dependencies
                if d.source.original_id == dep1.source.original_id
            ),
            None,
        )
        assert dep2 is not None
        assert dep2.dependency_type == dep1.dependency_type

    def test_roundtrip_calendar_count(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        simple_project_file: Path,
    ) -> None:
        """Test calendar count preserved in roundtrip."""
        project1 = parser.parse_file(simple_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        assert len(project2.calendars) == len(project1.calendars)


class TestMspdiRoundtripComplex:
    """Roundtrip tests for complex project."""

    def test_roundtrip_task_hierarchy(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test task hierarchy preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Find a parent-child pair
        parent1 = next((t for t in project1.tasks if t.is_summary), None)
        assert parent1 is not None

        child1 = next((t for t in project1.tasks if t.parent_id == parent1.id), None)
        assert child1 is not None

        # Find same tasks in roundtrip result
        parent2 = next(
            (
                t
                for t in project2.tasks
                if t.source.original_id == parent1.source.original_id
            ),
            None,
        )
        assert parent2 is not None

        child2 = next(
            (
                t
                for t in project2.tasks
                if t.source.original_id == child1.source.original_id
            ),
            None,
        )
        assert child2 is not None

        # Verify hierarchy preserved
        assert child2.parent_id == parent2.id
        assert child2.outline_level == child1.outline_level

    def test_roundtrip_summary_tasks(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test summary task flag preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        summary1 = next((t for t in project1.tasks if t.is_summary), None)
        assert summary1 is not None

        summary2 = next(
            (
                t
                for t in project2.tasks
                if t.source.original_id == summary1.source.original_id
            ),
            None,
        )
        assert summary2 is not None
        assert summary2.is_summary == summary1.is_summary

    def test_roundtrip_milestone_tasks(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test milestone flag preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        milestone1 = next((t for t in project1.tasks if t.is_milestone), None)
        assert milestone1 is not None

        milestone2 = next(
            (
                t
                for t in project2.tasks
                if t.source.original_id == milestone1.source.original_id
            ),
            None,
        )
        assert milestone2 is not None
        assert milestone2.is_milestone == milestone1.is_milestone

    def test_roundtrip_actual_dates(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test actual dates preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Find task with actual dates
        task1 = next((t for t in project1.tasks if t.actual_start is not None), None)
        assert task1 is not None

        task2 = next(
            (
                t
                for t in project2.tasks
                if t.source.original_id == task1.source.original_id
            ),
            None,
        )
        assert task2 is not None

        assert task2.actual_start == task1.actual_start
        assert task2.actual_finish == task1.actual_finish


    def test_roundtrip_dependency_lag(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test dependency lag preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Find dependency with lag
        dep1 = next((d for d in project1.dependencies if d.lag is not None), None)
        assert dep1 is not None

        dep2 = next(
            (
                d
                for d in project2.dependencies
                if d.source.original_id == dep1.source.original_id
            ),
            None,
        )
        assert dep2 is not None

        assert dep2.lag is not None
        assert dep1.lag is not None
        assert dep2.lag.to_hours() == dep1.lag.to_hours()

    def test_roundtrip_multiple_resource_types(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test different resource types preserved in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # Check we have different resource types
        resource_types1 = {r.resource_type for r in project1.resources if r.resource_type}
        resource_types2 = {r.resource_type for r in project2.resources if r.resource_type}

        assert len(resource_types1) > 1  # Multiple types in source
        assert resource_types2 == resource_types1

    def test_roundtrip_complete_project_integrity(
        self,
        parser: MspdiParser,
        writer: MspdiWriter,
        complex_project_file: Path,
    ) -> None:
        """Test complete project integrity in roundtrip."""
        project1 = parser.parse_file(complex_project_file)
        assert project1 is not None

        xml_bytes = writer.write_string(project1)
        project2 = parser.parse_string(xml_bytes)
        assert project2 is not None

        # High-level integrity checks
        assert project2.name == project1.name
        assert len(project2.tasks) == len(project1.tasks)
        assert len(project2.resources) == len(project1.resources)
        assert len(project2.assignments) == len(project1.assignments)
        assert len(project2.dependencies) == len(project1.dependencies)
        assert len(project2.calendars) == len(project1.calendars)
