"""Tests for structural validator."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from pm_data_tools.models import (
    Assignment,
    Calendar,
    Dependency,
    DependencyType,
    DeliveryConfidence,
    Duration,
    Money,
    Project,
    Resource,
    ResourceType,
    SourceInfo,
    Task,
    TaskStatus,
)
from pm_data_tools.validators import Severity, StructuralValidator


@pytest.fixture
def validator() -> StructuralValidator:
    """Create a structural validator."""
    return StructuralValidator()


@pytest.fixture
def valid_project() -> Project:
    """Create a valid project for testing."""
    task1_id = uuid4()
    task2_id = uuid4()
    resource1_id = uuid4()

    task1 = Task(
        id=task1_id,
        name="Task 1",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        start_date=datetime(2025, 1, 1),
        finish_date=datetime(2025, 1, 10),
        percent_complete=0.0,
        status=TaskStatus.NOT_STARTED,
    )

    task2 = Task(
        id=task2_id,
        name="Task 2",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
        start_date=datetime(2025, 1, 11),
        finish_date=datetime(2025, 1, 20),
        percent_complete=0.0,
        status=TaskStatus.NOT_STARTED,
    )

    resource1 = Resource(
        id=resource1_id,
        name="Resource 1",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        resource_type=ResourceType.WORK,
    )

    assignment1 = Assignment(
        id=uuid4(),
        task_id=task1_id,
        resource_id=resource1_id,
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        units=1.0,
    )

    dependency1 = Dependency(
        id=uuid4(),
        predecessor_id=task1_id,
        successor_id=task2_id,
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        dependency_type=DependencyType.FINISH_TO_START,
    )

    return Project(
        id=uuid4(),
        name="Test Project",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        start_date=datetime(2025, 1, 1),
        finish_date=datetime(2025, 12, 31),
        delivery_confidence=DeliveryConfidence.GREEN,
        tasks=[task1, task2],
        resources=[resource1],
        assignments=[assignment1],
        dependencies=[dependency1],
        calendars=[],
        custom_fields=[],
        risks=[],
    )


class TestStructuralValidatorBasic:
    """Test basic validation functionality."""

    def test_valid_project_passes(
        self, validator: StructuralValidator, valid_project: Project
    ) -> None:
        """Test that a valid project passes validation."""
        result = validator.validate(valid_project)

        assert result.is_valid
        assert result.errors_count == 0
        assert len(result.issues) == 0

    def test_validation_result_properties(
        self, validator: StructuralValidator
    ) -> None:
        """Test ValidationResult properties."""
        # Create project with various severity issues
        project = Project(
            id=uuid4(),
            name="",  # Error: missing name
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert result.errors_count == 1
        assert result.warnings_count == 0
        assert result.info_count == 0


class TestRequiredFields:
    """Test required field validation."""

    def test_missing_project_name(self, validator: StructuralValidator) -> None:
        """Test validation fails when project name is missing."""
        project = Project(
            id=uuid4(),
            name="",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert result.errors_count == 1
        assert any(issue.code == "MISSING_PROJECT_NAME" for issue in result.issues)

    def test_missing_task_name(self, validator: StructuralValidator) -> None:
        """Test validation fails when task name is missing."""
        task = Task(
            id=uuid4(),
            name="",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "MISSING_TASK_NAME" for issue in result.issues)

    def test_missing_resource_name(self, validator: StructuralValidator) -> None:
        """Test validation fails when resource name is missing."""
        resource = Resource(
            id=uuid4(),
            name="",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            resource_type=ResourceType.WORK,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[resource],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "MISSING_RESOURCE_NAME" for issue in result.issues)


class TestTaskReferences:
    """Test task reference validation."""

    def test_invalid_parent_task_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when task references non-existent parent."""
        task = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            parent_id=uuid4(),  # Non-existent parent
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_PARENT_TASK_REF" for issue in result.issues)

    def test_circular_parent_reference(self, validator: StructuralValidator) -> None:
        """Test validation fails when task is its own parent."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            parent_id=task_id,  # Self-reference
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "CIRCULAR_PARENT_REF" for issue in result.issues)


class TestAssignmentReferences:
    """Test assignment reference validation."""

    def test_invalid_assignment_task_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when assignment references non-existent task."""
        resource_id = uuid4()
        resource = Resource(
            id=resource_id,
            name="Resource 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            resource_type=ResourceType.WORK,
        )

        assignment = Assignment(
            id=uuid4(),
            task_id=uuid4(),  # Non-existent task
            resource_id=resource_id,
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            units=1.0,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[resource],
            assignments=[assignment],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(
            issue.code == "INVALID_ASSIGNMENT_TASK_REF" for issue in result.issues
        )

    def test_invalid_assignment_resource_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when assignment references non-existent resource."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        assignment = Assignment(
            id=uuid4(),
            task_id=task_id,
            resource_id=uuid4(),  # Non-existent resource
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            units=1.0,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[assignment],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(
            issue.code == "INVALID_ASSIGNMENT_RESOURCE_REF" for issue in result.issues
        )


class TestDependencyReferences:
    """Test dependency reference validation."""

    def test_invalid_predecessor_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when dependency references non-existent predecessor."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        dependency = Dependency(
            id=uuid4(),
            predecessor_id=uuid4(),  # Non-existent task
            successor_id=task_id,
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[dependency],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_PREDECESSOR_REF" for issue in result.issues)

    def test_invalid_successor_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when dependency references non-existent successor."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        dependency = Dependency(
            id=uuid4(),
            predecessor_id=task_id,
            successor_id=uuid4(),  # Non-existent task
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[dependency],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_SUCCESSOR_REF" for issue in result.issues)

    def test_self_dependency(self, validator: StructuralValidator) -> None:
        """Test validation fails when task depends on itself."""
        task_id = uuid4()
        task = Task(
            id=task_id,
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        dependency = Dependency(
            id=uuid4(),
            predecessor_id=task_id,
            successor_id=task_id,  # Self-dependency
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[dependency],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "SELF_DEPENDENCY" for issue in result.issues)


class TestDateConsistency:
    """Test date consistency validation."""

    def test_invalid_project_dates(self, validator: StructuralValidator) -> None:
        """Test validation fails when project finish is before start."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            start_date=datetime(2025, 12, 31),
            finish_date=datetime(2025, 1, 1),  # Before start!
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_PROJECT_DATES" for issue in result.issues)

    def test_invalid_task_dates(self, validator: StructuralValidator) -> None:
        """Test validation fails when task finish is before start."""
        task = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            start_date=datetime(2025, 1, 10),
            finish_date=datetime(2025, 1, 1),  # Before start!
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_TASK_DATES" for issue in result.issues)

    def test_invalid_actual_dates(self, validator: StructuralValidator) -> None:
        """Test validation fails when actual finish is before actual start."""
        task = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            actual_start=datetime(2025, 1, 10),
            actual_finish=datetime(2025, 1, 1),  # Before start!
            percent_complete=100.0,
            status=TaskStatus.COMPLETED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_ACTUAL_DATES" for issue in result.issues)

    def test_valid_actual_dates(self, validator: StructuralValidator) -> None:
        """Test validation passes when actual dates are valid."""
        task = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            actual_start=datetime(2025, 1, 1),
            actual_finish=datetime(2025, 1, 10),  # After start - valid
            percent_complete=100.0,
            status=TaskStatus.COMPLETED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        # Should not have actual date errors
        assert not any(issue.code == "INVALID_ACTUAL_DATES" for issue in result.issues)

    def test_completed_task_no_actual_finish(
        self, validator: StructuralValidator
    ) -> None:
        """Test warning when completed task has no actual finish date."""
        task = Task(
            id=uuid4(),
            name="Task 1",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=100.0,
            status=TaskStatus.COMPLETED,
            # No actual_finish date
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        # Should pass validation (it's a warning, not an error)
        assert result.is_valid
        assert result.warnings_count == 1
        assert any(
            issue.code == "COMPLETED_TASK_NO_ACTUAL_FINISH" for issue in result.issues
        )


class TestCalendarReferences:
    """Test calendar reference validation."""

    def test_invalid_base_calendar_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation fails when calendar references non-existent base calendar."""
        calendar = Calendar(
            id=uuid4(),
            name="Custom Calendar",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            base_calendar_id=uuid4(),  # Non-existent calendar
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[calendar],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_BASE_CALENDAR_REF" for issue in result.issues)

    def test_valid_base_calendar_reference(
        self, validator: StructuralValidator
    ) -> None:
        """Test validation passes when calendar references existing base calendar."""
        base_calendar_id = uuid4()
        base_calendar = Calendar(
            id=base_calendar_id,
            name="Base Calendar",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        )

        custom_calendar = Calendar(
            id=uuid4(),
            name="Custom Calendar",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
            base_calendar_id=base_calendar_id,  # References existing calendar
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=[],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[base_calendar, custom_calendar],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        # Should not have calendar reference errors
        assert not any(
            issue.code == "INVALID_BASE_CALENDAR_REF" for issue in result.issues
        )
