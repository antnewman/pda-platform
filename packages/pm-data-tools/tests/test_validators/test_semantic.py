"""Tests for semantic validator."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from pm_data_tools.models import (
    DeliveryConfidence,
    Dependency,
    DependencyType,
    Duration,
    Money,
    Project,
    Resource,
    ResourceType,
    Risk,
    RiskStatus,
    SourceInfo,
    Task,
    TaskStatus,
)
from pm_data_tools.validators import SemanticValidator, Severity


@pytest.fixture
def validator() -> SemanticValidator:
    """Create a semantic validator."""
    return SemanticValidator()


@pytest.fixture
def valid_project() -> Project:
    """Create a valid project for testing."""
    task1_id = uuid4()
    task2_id = uuid4()

    task1 = Task(
        id=task1_id,
        name="Task 1",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        start_date=datetime(2025, 1, 1),
        finish_date=datetime(2025, 1, 10),
        percent_complete=0.0,
        status=TaskStatus.NOT_STARTED,
        budgeted_cost=Money(Decimal("1000.00"), "GBP"),
        budgeted_work=Duration(value=40.0, unit="hours"),
    )

    task2 = Task(
        id=task2_id,
        name="Task 2",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
        start_date=datetime(2025, 1, 11),
        finish_date=datetime(2025, 1, 20),
        percent_complete=0.0,
        status=TaskStatus.NOT_STARTED,
        budgeted_cost=Money(Decimal("1500.00"), "GBP"),
        budgeted_work=Duration(value=60.0, unit="hours"),
    )

    dependency = Dependency(
        id=uuid4(),
        predecessor_id=task1_id,
        successor_id=task2_id,
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        dependency_type=DependencyType.FINISH_TO_START,
    )

    project = Project(
        id=uuid4(),
        name="Test Project",
        source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
        delivery_confidence=DeliveryConfidence.GREEN,
        start_date=datetime(2025, 1, 1),
        finish_date=datetime(2025, 1, 31),
        budgeted_cost=Money(Decimal("2500.00"), "GBP"),
        tasks=[task1, task2],
        resources=[],
        assignments=[],
        dependencies=[dependency],
        calendars=[],
        custom_fields=[],
        risks=[],
    )

    return project


class TestSemanticValidatorBasic:
    """Basic semantic validator tests."""

    def test_valid_project_passes(
        self, validator: SemanticValidator, valid_project: Project
    ) -> None:
        """Test that a valid project passes validation."""
        result = validator.validate(valid_project)

        assert result.is_valid
        assert result.errors_count == 0


class TestDependencyCycles:
    """Test circular dependency detection."""

    def test_no_cycles_passes(self, validator: SemanticValidator) -> None:
        """Test validation passes with no circular dependencies."""
        task1_id = uuid4()
        task2_id = uuid4()
        task3_id = uuid4()

        tasks = [
            Task(
                id=task1_id,
                name="Task 1",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
            Task(
                id=task2_id,
                name="Task 2",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
            Task(
                id=task3_id,
                name="Task 3",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="3"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
        ]

        # Linear dependencies: 1 -> 2 -> 3
        dependencies = [
            Dependency(
                id=uuid4(),
                predecessor_id=task1_id,
                successor_id=task2_id,
                source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
                dependency_type=DependencyType.FINISH_TO_START,
            ),
            Dependency(
                id=uuid4(),
                predecessor_id=task2_id,
                successor_id=task3_id,
                source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
                dependency_type=DependencyType.FINISH_TO_START,
            ),
        ]

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=tasks,
            resources=[],
            assignments=[],
            dependencies=dependencies,
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not any(issue.code == "CIRCULAR_DEPENDENCY" for issue in result.issues)

    def test_circular_dependency_detected(self, validator: SemanticValidator) -> None:
        """Test validation detects circular dependencies."""
        task1_id = uuid4()
        task2_id = uuid4()
        task3_id = uuid4()

        tasks = [
            Task(
                id=task1_id,
                name="Task 1",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
            Task(
                id=task2_id,
                name="Task 2",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
            Task(
                id=task3_id,
                name="Task 3",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="3"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
            ),
        ]

        # Circular dependencies: 1 -> 2 -> 3 -> 1
        dependencies = [
            Dependency(
                id=uuid4(),
                predecessor_id=task1_id,
                successor_id=task2_id,
                source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
                dependency_type=DependencyType.FINISH_TO_START,
            ),
            Dependency(
                id=uuid4(),
                predecessor_id=task2_id,
                successor_id=task3_id,
                source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
                dependency_type=DependencyType.FINISH_TO_START,
            ),
            Dependency(
                id=uuid4(),
                predecessor_id=task3_id,
                successor_id=task1_id,  # Creates cycle
                source=SourceInfo(tool="test", tool_version="1.0", original_id="3"),
                dependency_type=DependencyType.FINISH_TO_START,
            ),
        ]

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            tasks=tasks,
            resources=[],
            assignments=[],
            dependencies=dependencies,
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "CIRCULAR_DEPENDENCY" for issue in result.issues)


class TestScheduleLogic:
    """Test schedule logic validation."""

    def test_task_before_project_start(self, validator: SemanticValidator) -> None:
        """Test warning when task starts before project."""
        task = Task(
            id=uuid4(),
            name="Early Task",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            start_date=datetime(2024, 12, 1),  # Before project start
            finish_date=datetime(2025, 1, 5),
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 31),
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert any(
            issue.code == "TASK_BEFORE_PROJECT_START" for issue in result.issues
        )

    def test_task_after_project_finish(self, validator: SemanticValidator) -> None:
        """Test warning when task finishes after project."""
        task = Task(
            id=uuid4(),
            name="Late Task",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            start_date=datetime(2025, 1, 25),
            finish_date=datetime(2025, 2, 10),  # After project finish
            percent_complete=0.0,
            status=TaskStatus.NOT_STARTED,
        )

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 31),
            tasks=[task],
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert any(
            issue.code == "TASK_AFTER_PROJECT_FINISH" for issue in result.issues
        )


class TestCostConsistency:
    """Test cost consistency validation."""

    def test_cost_mismatch(self, validator: SemanticValidator) -> None:
        """Test warning when task costs don't match project budget."""
        tasks = [
            Task(
                id=uuid4(),
                name="Task 1",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
                budgeted_cost=Money(Decimal("1000.00"), "GBP"),
            ),
            Task(
                id=uuid4(),
                name="Task 2",
                source=SourceInfo(tool="test", tool_version="1.0", original_id="2"),
                percent_complete=0.0,
                status=TaskStatus.NOT_STARTED,
                budgeted_cost=Money(Decimal("1500.00"), "GBP"),
            ),
        ]

        project = Project(
            id=uuid4(),
            name="Test Project",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            delivery_confidence=DeliveryConfidence.GREEN,
            budgeted_cost=Money(Decimal("3000.00"), "GBP"),  # Doesn't match sum (2500)
            tasks=tasks,
            resources=[],
            assignments=[],
            dependencies=[],
            calendars=[],
            custom_fields=[],
            risks=[],
        )

        result = validator.validate(project)

        assert any(issue.code == "COST_MISMATCH" for issue in result.issues)

    def test_task_cost_overrun(self, validator: SemanticValidator) -> None:
        """Test info message when task actual cost exceeds budget."""
        task = Task(
            id=uuid4(),
            name="Over Budget Task",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=50.0,
            status=TaskStatus.IN_PROGRESS,
            budgeted_cost=Money(Decimal("1000.00"), "GBP"),
            actual_cost=Money(Decimal("1200.00"), "GBP"),  # Over budget
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

        assert any(issue.code == "TASK_COST_OVERRUN" for issue in result.issues)


class TestProgressConsistency:
    """Test progress consistency validation."""

    def test_work_overrun(self, validator: SemanticValidator) -> None:
        """Test info message when actual work exceeds budgeted work."""
        task = Task(
            id=uuid4(),
            name="Work Overrun Task",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            percent_complete=50.0,
            status=TaskStatus.IN_PROGRESS,
            budgeted_work=Duration(value=40.0, unit="hours"),
            actual_work=Duration(value=50.0, unit="hours"),  # Over budget
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

        assert any(issue.code == "WORK_OVERRUN" for issue in result.issues)

    def test_started_task_no_progress(self, validator: SemanticValidator) -> None:
        """Test warning when task has actual start but 0% progress."""
        task = Task(
            id=uuid4(),
            name="Started Task",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            actual_start=datetime(2025, 1, 1),
            percent_complete=0.0,  # No progress despite starting
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

        assert any(issue.code == "STARTED_TASK_NO_PROGRESS" for issue in result.issues)


class TestRiskAssessments:
    """Test risk assessment validation."""

    def test_invalid_risk_probability(self, validator: SemanticValidator) -> None:
        """Test error when risk probability is outside valid range."""
        risk = Risk(
            id=uuid4(),
            name="Invalid Risk",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            probability=10,  # Invalid (should be 1-5)
            impact=3,
            status=RiskStatus.IDENTIFIED,
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
            calendars=[],
            custom_fields=[],
            risks=[risk],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_RISK_PROBABILITY" for issue in result.issues)

    def test_invalid_risk_impact(self, validator: SemanticValidator) -> None:
        """Test error when risk impact is outside valid range."""
        risk = Risk(
            id=uuid4(),
            name="Invalid Risk",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            probability=3,
            impact=0,  # Invalid (should be 1-5)
            status=RiskStatus.IDENTIFIED,
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
            calendars=[],
            custom_fields=[],
            risks=[risk],
        )

        result = validator.validate(project)

        assert not result.is_valid
        assert any(issue.code == "INVALID_RISK_IMPACT" for issue in result.issues)

    def test_high_risk_no_mitigation(self, validator: SemanticValidator) -> None:
        """Test warning when high-severity risk lacks mitigation strategy."""
        risk = Risk(
            id=uuid4(),
            name="High Risk",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            probability=5,
            impact=5,  # Score: 25 (very high)
            status=RiskStatus.IDENTIFIED,
            mitigation="",  # No mitigation
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
            calendars=[],
            custom_fields=[],
            risks=[risk],
        )

        result = validator.validate(project)

        assert any(issue.code == "HIGH_RISK_NO_MITIGATION" for issue in result.issues)

    def test_low_risk_no_mitigation_allowed(
        self, validator: SemanticValidator
    ) -> None:
        """Test that low-severity risks don't require mitigation."""
        risk = Risk(
            id=uuid4(),
            name="Low Risk",
            source=SourceInfo(tool="test", tool_version="1.0", original_id="1"),
            probability=2,
            impact=2,  # Score: 4 (low)
            status=RiskStatus.IDENTIFIED,
            mitigation="",  # No mitigation needed
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
            calendars=[],
            custom_fields=[],
            risks=[risk],
        )

        result = validator.validate(project)

        # Should not have HIGH_RISK_NO_MITIGATION for low risks
        assert not any(
            issue.code == "HIGH_RISK_NO_MITIGATION" for issue in result.issues
        )


class TestProgressConsistencyEdgeCases:
    """Tests for progress consistency edge cases."""

    def test_task_100_percent_with_actual_start_no_finish(
        self, validator: SemanticValidator
    ) -> None:
        """Test task at 100% with actual start but no finish (line 235 - pass branch)."""
        task = Task(
            id=uuid4(),
            name="Almost Done",
            source=SourceInfo(tool="test"),
            actual_start=datetime(2025, 1, 1),
            actual_finish=None,  # Missing!
            percent_complete=100.0,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # This is caught by structural validator, so semantic skips it (line 235)
        # Should not crash

    def test_task_with_actual_cost_no_budget(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with actual cost but no budgeted cost."""
        task = Task(
            id=uuid4(),
            name="No Budget",
            source=SourceInfo(tool="test"),
            budgeted_cost=None,
            actual_cost=Money(Decimal("1000"), "GBP"),
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not crash

    def test_task_with_actual_work_no_budget(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with actual work but no budgeted work."""
        task = Task(
            id=uuid4(),
            name="No Budgeted Work",
            source=SourceInfo(tool="test"),
            budgeted_work=None,
            actual_work=Duration(40, "hours"),
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not crash


class TestScheduleLogicEdgeCases:
    """Tests for schedule logic edge cases."""

    def test_dependencies_without_dates(
        self, validator: SemanticValidator
    ) -> None:
        """Test dependencies without task dates don't trigger validation."""
        task_a = Task(id=uuid4(), name="A", source=SourceInfo(tool="test"))
        task_b = Task(id=uuid4(), name="B", source=SourceInfo(tool="test"))

        dep = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b],
            dependencies=[dep],
        )

        result = validator.validate(project)
        # Should not have schedule validation issues without dates
        assert not any("SCHEDULE" in issue.code for issue in result.issues)

    def test_finish_to_start_satisfied(
        self, validator: SemanticValidator
    ) -> None:
        """Test FS dependency validation when satisfied."""
        task_a = Task(
            id=uuid4(),
            name="A",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 10),
        )
        task_b = Task(
            id=uuid4(),
            name="B",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 11),  # Valid!
            finish_date=datetime(2025, 1, 20),
        )

        dep = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b],
            dependencies=[dep],
        )

        result = validator.validate(project)
        # Should pass
        assert not any(
            "DEPENDENCY" in issue.code or "SCHEDULE" in issue.code
            for issue in result.issues
        )

    def test_start_to_start_dependency(
        self, validator: SemanticValidator
    ) -> None:
        """Test SS dependency type validation."""
        task_a = Task(
            id=uuid4(),
            name="A",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 10),
            finish_date=datetime(2025, 1, 20),
        )
        task_b = Task(
            id=uuid4(),
            name="B",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 5),  # Violates SS
            finish_date=datetime(2025, 1, 15),
        )

        dep = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.START_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b],
            dependencies=[dep],
        )

        result = validator.validate(project)
        # Validator only checks FS dependencies currently, so this should not crash
        # (SS validation not yet implemented)

    def test_finish_to_finish_dependency(
        self, validator: SemanticValidator
    ) -> None:
        """Test FF dependency type validation."""
        task_a = Task(
            id=uuid4(),
            name="A",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 20),
        )
        task_b = Task(
            id=uuid4(),
            name="B",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 5),
            finish_date=datetime(2025, 1, 15),
        )

        dep = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_FINISH,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b],
            dependencies=[dep],
        )

        result = validator.validate(project)
        # Validator only checks FS dependencies currently, so this should not crash
        # (FF validation not yet implemented)

    def test_start_to_finish_dependency(
        self, validator: SemanticValidator
    ) -> None:
        """Test SF dependency type validation."""
        task_a = Task(
            id=uuid4(),
            name="A",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 10),
            finish_date=datetime(2025, 1, 20),
        )
        task_b = Task(
            id=uuid4(),
            name="B",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 1, 15),
        )

        dep = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.START_TO_FINISH,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b],
            dependencies=[dep],
        )

        result = validator.validate(project)
        # Validator only checks FS dependencies currently, so this should not crash
        # (SF validation not yet implemented)


class TestCostAndWorkEdgeCases:
    """Tests for cost and work validation edge cases."""

    def test_project_cost_variance_no_actual(
        self, validator: SemanticValidator
    ) -> None:
        """Test project with budgeted cost but no actual cost."""
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            budgeted_cost=Money(Decimal("100000"), "GBP"),
            actual_cost=None,
        )

        result = validator.validate(project)
        # Should not crash

    def test_task_cost_overrun_edge(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with exactly 110% cost overrun threshold."""
        task = Task(
            id=uuid4(),
            name="At Threshold",
            source=SourceInfo(tool="test"),
            budgeted_cost=Money(Decimal("1000"), "GBP"),
            actual_cost=Money(Decimal("1100"), "GBP"),  # Exactly 110%
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should have cost overrun warning
        assert any("COST_OVERRUN" in issue.code for issue in result.issues)

    def test_task_cost_different_currencies(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with costs in different currencies (branch 188->186)."""
        task = Task(
            id=uuid4(),
            name="Multi-Currency Task",
            source=SourceInfo(tool="test"),
            budgeted_cost=Money(Decimal("1000"), "GBP"),
            actual_cost=Money(Decimal("1500"), "USD"),  # Different currency
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not compare costs in different currencies
        cost_codes = [issue.code for issue in result.issues]
        assert "TASK_COST_OVERRUN" not in cost_codes

    def test_task_cost_under_budget(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with actual cost under budget (branch 189->186)."""
        task = Task(
            id=uuid4(),
            name="Under Budget Task",
            source=SourceInfo(tool="test"),
            budgeted_cost=Money(Decimal("1000"), "GBP"),
            actual_cost=Money(Decimal("800"), "GBP"),  # Under budget
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not have cost overrun
        cost_codes = [issue.code for issue in result.issues]
        assert "TASK_COST_OVERRUN" not in cost_codes

    def test_task_work_under_budget(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with actual work under budget (branch 219->232)."""
        task = Task(
            id=uuid4(),
            name="Efficient Task",
            source=SourceInfo(tool="test"),
            budgeted_work=Duration(value=100, unit="hours"),
            actual_work=Duration(value=80, unit="hours"),  # Under budget
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not have work overrun
        work_codes = [issue.code for issue in result.issues]
        assert "WORK_OVERRUN" not in work_codes

    def test_task_started_progress_between_zero_and_hundred(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with actual start, no finish, progress 50% (branch 236->214)."""
        task = Task(
            id=uuid4(),
            name="In Progress Task",
            source=SourceInfo(tool="test"),
            actual_start=datetime(2025, 1, 1),
            actual_finish=None,
            percent_complete=50.0,  # Not 0 or 100
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not have progress issues (valid in-progress state)
        progress_codes = [issue.code for issue in result.issues]
        assert "STARTED_TASK_NO_PROGRESS" not in progress_codes

    def test_task_finish_only_with_project_dates(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with finish date but no start date (branch 125->137)."""
        task = Task(
            id=uuid4(),
            name="Task with Finish Only",
            source=SourceInfo(tool="test"),
            start_date=None,  # No start date
            finish_date=datetime(2025, 2, 1),
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 3, 1),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should still check finish date against project dates
        # No error expected since finish is within project dates

    def test_task_no_dates_with_project_dates(
        self, validator: SemanticValidator
    ) -> None:
        """Test task with no dates when project has dates (branch 137->124)."""
        task = Task(
            id=uuid4(),
            name="Task with No Dates",
            source=SourceInfo(tool="test"),
            start_date=None,
            finish_date=None,
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            start_date=datetime(2025, 1, 1),
            finish_date=datetime(2025, 3, 1),
            tasks=[task],
        )

        result = validator.validate(project)
        # Should not crash or have date validation issues for dateless tasks

    def test_risk_no_probability(
        self, validator: SemanticValidator
    ) -> None:
        """Test risk with no probability (branch 262->275)."""
        risk = Risk(
            id=uuid4(),
            name="Risk without Probability",
            source=SourceInfo(tool="test"),
            probability=None,  # No probability
            impact=3,
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            risks=[risk],
        )

        result = validator.validate(project)
        # Should skip probability validation
        risk_codes = [issue.code for issue in result.issues]
        assert "INVALID_RISK_PROBABILITY" not in risk_codes

    def test_risk_no_impact(
        self, validator: SemanticValidator
    ) -> None:
        """Test risk with no impact (branch 275->288)."""
        risk = Risk(
            id=uuid4(),
            name="Risk without Impact",
            source=SourceInfo(tool="test"),
            probability=3,
            impact=None,  # No impact
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            risks=[risk],
        )

        result = validator.validate(project)
        # Should skip impact validation
        risk_codes = [issue.code for issue in result.issues]
        assert "INVALID_RISK_IMPACT" not in risk_codes

    def test_high_risk_with_mitigation(
        self, validator: SemanticValidator
    ) -> None:
        """Test high-risk with mitigation strategy (branch 291->260)."""
        risk = Risk(
            id=uuid4(),
            name="High Risk with Mitigation",
            source=SourceInfo(tool="test"),
            probability=5,
            impact=5,  # Score = 25, very high
            mitigation="Implement redundancy and monitoring",  # Has mitigation
        )
        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            risks=[risk],
        )

        result = validator.validate(project)
        # Should not warn about missing mitigation
        risk_codes = [issue.code for issue in result.issues]
        assert "HIGH_RISK_NO_MITIGATION" not in risk_codes

    def test_circular_dependency_detection_in_degree_loop(
        self, validator: SemanticValidator
    ) -> None:
        """Test circular dependency with multiple cycles (branch 83->81)."""
        task_a = Task(id=uuid4(), name="Task A", source=SourceInfo(tool="test"))
        task_b = Task(id=uuid4(), name="Task B", source=SourceInfo(tool="test"))
        task_c = Task(id=uuid4(), name="Task C", source=SourceInfo(tool="test"))

        # Create complex cycle: A->B->C->A and B->A
        dep1 = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_b.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )
        dep2 = Dependency(
            id=uuid4(),
            predecessor_id=task_b.id,
            successor_id=task_c.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )
        dep3 = Dependency(
            id=uuid4(),
            predecessor_id=task_c.id,
            successor_id=task_a.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b, task_c],
            dependencies=[dep1, dep2, dep3],
        )

        result = validator.validate(project)
        # Should detect circular dependency
        assert any("CIRCULAR_DEPENDENCY" in issue.code for issue in result.issues)

    def test_complex_dependency_graph_in_degree_reduction(
        self, validator: SemanticValidator
    ) -> None:
        """Test complex dependency graph with multiple predecessors (branch 83->81)."""
        task_a = Task(id=uuid4(), name="Task A", source=SourceInfo(tool="test"))
        task_b = Task(id=uuid4(), name="Task B", source=SourceInfo(tool="test"))
        task_c = Task(id=uuid4(), name="Task C", source=SourceInfo(tool="test"))
        task_d = Task(id=uuid4(), name="Task D", source=SourceInfo(tool="test"))

        # Create graph where D has multiple predecessors (A, B, C)
        # A -> D, B -> D, C -> D
        # This ensures when we process A and reduce D's in-degree, it's still > 0
        dep1 = Dependency(
            id=uuid4(),
            predecessor_id=task_a.id,
            successor_id=task_d.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )
        dep2 = Dependency(
            id=uuid4(),
            predecessor_id=task_b.id,
            successor_id=task_d.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )
        dep3 = Dependency(
            id=uuid4(),
            predecessor_id=task_c.id,
            successor_id=task_d.id,
            source=SourceInfo(tool="test"),
            dependency_type=DependencyType.FINISH_TO_START,
        )

        project = Project(
            id=uuid4(),
            name="Test",
            source=SourceInfo(tool="test"),
            tasks=[task_a, task_b, task_c, task_d],
            dependencies=[dep1, dep2, dep3],
        )

        result = validator.validate(project)
        # Should not have circular dependency (valid DAG)
        circ_issues = [
            issue for issue in result.issues if "CIRCULAR_DEPENDENCY" in issue.code
        ]
        assert len(circ_issues) == 0
