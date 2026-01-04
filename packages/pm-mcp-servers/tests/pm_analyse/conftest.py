"""
Pytest fixtures for PM-Analyse tests.

Provides mock project data, tasks, resources, and dependencies for testing
all analysis modules.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import pytest


class MockTask:
    """Mock task object for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '1')
        self.name = kwargs.get('name', 'Test Task')
        self.start_date = kwargs.get('start_date', date.today())
        self.finish_date = kwargs.get('finish_date', date.today() + timedelta(days=10))
        self.percent_complete = kwargs.get('percent_complete', 0)
        self.is_summary = kwargs.get('is_summary', False)
        self.is_milestone = kwargs.get('is_milestone', False)
        self.is_critical = kwargs.get('is_critical', False)
        self.total_float = kwargs.get('total_float', None)
        self.notes = kwargs.get('notes', '')
        self.baseline_start = kwargs.get('baseline_start', None)
        self.baseline_finish = kwargs.get('baseline_finish', None)
        self.baseline_duration = kwargs.get('baseline_duration', None)


class MockResource:
    """Mock resource object for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '1')
        self.name = kwargs.get('name', 'Test Resource')
        self.max_units = kwargs.get('max_units', 1.0)
        self.type = kwargs.get('type', 'work')


class MockDependency:
    """Mock dependency object for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '1')
        self.predecessor_id = kwargs.get('predecessor_id', '1')
        self.successor_id = kwargs.get('successor_id', '2')
        self.type = kwargs.get('type', 'FS')
        self.lag = kwargs.get('lag', 0)


class MockCost:
    """Mock cost object for testing."""

    def __init__(self, amount: float, currency: str = 'USD'):
        self.amount = amount
        self.currency = currency


class MockRiskEntry:
    """Mock risk register entry for testing."""

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'External Risk')
        self.description = kwargs.get('description', 'Risk description')
        self.category = kwargs.get('category', 'external')
        self.probability = kwargs.get('probability', 3)
        self.impact = kwargs.get('impact', 3)
        self.mitigation = kwargs.get('mitigation', None)


class MockProject:
    """Mock project object for testing."""

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test-project-1')
        self.name = kwargs.get('name', 'Test Project')
        self.start_date = kwargs.get('start_date', date.today() - timedelta(days=30))
        self.finish_date = kwargs.get('finish_date', date.today() + timedelta(days=60))
        self.tasks = kwargs.get('tasks', [])
        self.resources = kwargs.get('resources', [])
        self.dependencies = kwargs.get('dependencies', [])
        self.budget = kwargs.get('budget', None)
        self.actual_cost = kwargs.get('actual_cost', None)
        self.forecast_cost = kwargs.get('forecast_cost', None)
        self.project_type = kwargs.get('project_type', 'default')
        self.risk_register = kwargs.get('risk_register', [])


@pytest.fixture
def simple_task():
    """Simple task with minimal data."""
    return MockTask(
        id='task-1',
        name='Simple Task',
        start_date=date.today(),
        finish_date=date.today() + timedelta(days=5),
        percent_complete=50
    )


@pytest.fixture
def overdue_task():
    """Task that is overdue."""
    return MockTask(
        id='task-2',
        name='Overdue Task',
        start_date=date.today() - timedelta(days=20),
        finish_date=date.today() - timedelta(days=10),
        percent_complete=60,
        is_critical=True
    )


@pytest.fixture
def critical_task():
    """Critical path task with low float."""
    return MockTask(
        id='task-3',
        name='Critical Task',
        start_date=date.today(),
        finish_date=date.today() + timedelta(days=7),
        percent_complete=0,
        is_critical=True,
        total_float=2
    )


@pytest.fixture
def task_with_baseline():
    """Task with baseline variance."""
    baseline = date.today() + timedelta(days=10)
    current = date.today() + timedelta(days=25)
    return MockTask(
        id='task-4',
        name='Slipping Task',
        start_date=date.today(),
        finish_date=current,
        baseline_start=date.today(),
        baseline_finish=baseline,
        baseline_duration=10,
        percent_complete=40
    )


@pytest.fixture
def milestone_task():
    """Milestone task."""
    return MockTask(
        id='milestone-1',
        name='Project Milestone',
        start_date=date.today() + timedelta(days=30),
        finish_date=date.today() + timedelta(days=30),
        percent_complete=0,
        is_milestone=True
    )


@pytest.fixture
def summary_task():
    """Summary/parent task."""
    return MockTask(
        id='summary-1',
        name='Phase 1',
        start_date=date.today(),
        finish_date=date.today() + timedelta(days=30),
        percent_complete=50,
        is_summary=True
    )


@pytest.fixture
def long_duration_task():
    """Task with unusually long duration."""
    return MockTask(
        id='task-5',
        name='Long Task',
        start_date=date.today(),
        finish_date=date.today() + timedelta(days=200),
        percent_complete=10
    )


@pytest.fixture
def stuck_task():
    """Task that is stuck (started but no progress)."""
    return MockTask(
        id='task-6',
        name='Stuck Task',
        start_date=date.today() - timedelta(days=15),
        finish_date=date.today() + timedelta(days=10),
        percent_complete=2
    )


@pytest.fixture
def overallocated_resource():
    """Resource that is overallocated."""
    return MockResource(
        id='resource-1',
        name='Overworked Developer',
        max_units=1.5
    )


@pytest.fixture
def normal_resource():
    """Normal resource."""
    return MockResource(
        id='resource-2',
        name='Normal Developer',
        max_units=1.0
    )


@pytest.fixture
def simple_dependency():
    """Simple FS dependency."""
    return MockDependency(
        id='dep-1',
        predecessor_id='task-1',
        successor_id='task-2',
        type='FS'
    )


@pytest.fixture
def basic_project(simple_task, normal_resource):
    """Basic project with minimal data."""
    return MockProject(
        id='project-basic',
        name='Basic Project',
        tasks=[simple_task],
        resources=[normal_resource],
        budget=MockCost(100000),
        actual_cost=MockCost(25000),
        forecast_cost=MockCost(105000)
    )


@pytest.fixture
def complex_project(
    simple_task,
    overdue_task,
    critical_task,
    task_with_baseline,
    milestone_task,
    summary_task,
    overallocated_resource,
    normal_resource,
    simple_dependency
):
    """Complex project with multiple tasks, resources, and issues."""
    # Create dependency chain
    deps = [
        MockDependency(id='dep-1', predecessor_id='task-1', successor_id='task-2'),
        MockDependency(id='dep-2', predecessor_id='task-2', successor_id='task-3'),
        MockDependency(id='dep-3', predecessor_id='task-3', successor_id='task-4'),
    ]

    return MockProject(
        id='project-complex',
        name='Complex Project',
        start_date=date.today() - timedelta(days=30),
        finish_date=date.today() + timedelta(days=90),
        tasks=[
            summary_task,
            simple_task,
            overdue_task,
            critical_task,
            task_with_baseline,
            milestone_task
        ],
        resources=[normal_resource, overallocated_resource],
        dependencies=deps,
        budget=MockCost(500000),
        actual_cost=MockCost(200000),
        forecast_cost=MockCost(650000),
        project_type='it'
    )


@pytest.fixture
def empty_project():
    """Project with no tasks or resources."""
    return MockProject(
        id='project-empty',
        name='Empty Project'
    )


@pytest.fixture
def project_with_risk_register():
    """Project with external risks in risk register."""
    risks = [
        MockRiskEntry(
            name='Vendor Delay Risk',
            description='Third-party vendor may delay delivery',
            category='external',
            probability=4,
            impact=4,
            mitigation='Maintain backup vendor list'
        ),
        MockRiskEntry(
            name='Regulatory Risk',
            description='New regulations may impact scope',
            category='external',
            probability=3,
            impact=5
        )
    ]

    return MockProject(
        id='project-risks',
        name='Project with Risks',
        tasks=[
            MockTask(id='task-1', name='Task 1', percent_complete=30),
            MockTask(id='task-2', name='Task 2', percent_complete=0)
        ],
        risk_register=risks
    )


@pytest.fixture
def project_over_budget():
    """Project significantly over budget."""
    tasks = [
        MockTask(
            id=f'task-{i}',
            name=f'Task {i}',
            start_date=date.today() - timedelta(days=60),
            finish_date=date.today() + timedelta(days=30),
            percent_complete=70 if i < 5 else 20
        )
        for i in range(1, 11)
    ]

    return MockProject(
        id='project-overbudget',
        name='Over Budget Project',
        tasks=tasks,
        budget=MockCost(100000),
        actual_cost=MockCost(95000),
        forecast_cost=MockCost(140000)
    )


@pytest.fixture
def project_no_milestones():
    """Project with many tasks but no milestones."""
    tasks = [
        MockTask(
            id=f'task-{i}',
            name=f'Task {i}',
            percent_complete=i * 10,
            notes='' if i % 3 == 0 else f'Description for task {i}'
        )
        for i in range(1, 16)
    ]

    return MockProject(
        id='project-no-milestones',
        name='Project Without Milestones',
        tasks=tasks
    )


@pytest.fixture
def project_with_bottleneck():
    """Project with dependency bottleneck."""
    tasks = [
        MockTask(id=f'task-{i}', name=f'Task {i}')
        for i in range(1, 11)
    ]

    # Create bottleneck: task-1 has 6 successors
    deps = [
        MockDependency(id=f'dep-{i}', predecessor_id='task-1', successor_id=f'task-{i}')
        for i in range(2, 8)
    ]

    return MockProject(
        id='project-bottleneck',
        name='Project with Bottleneck',
        tasks=tasks,
        dependencies=deps
    )


@pytest.fixture
def project_with_long_chain():
    """Project with long dependency chain."""
    tasks = [
        MockTask(id=f'task-{i}', name=f'Task {i}')
        for i in range(1, 16)
    ]

    # Create long chain: task-1 -> task-2 -> ... -> task-15
    deps = [
        MockDependency(id=f'dep-{i}', predecessor_id=f'task-{i}', successor_id=f'task-{i+1}')
        for i in range(1, 15)
    ]

    return MockProject(
        id='project-longchain',
        name='Project with Long Chain',
        tasks=tasks,
        dependencies=deps
    )
