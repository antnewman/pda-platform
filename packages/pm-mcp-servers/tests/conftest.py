"""Shared test fixtures and mocks for pm-mcp-servers tests.

Provides comprehensive mocks matching pm-data-tools real interface.
"""

import pytest
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
from unittest.mock import patch, MagicMock
from enum import Enum


# ============================================================================
# Mock Enums matching pm-data-tools
# ============================================================================

class TaskStatus(Enum):
    """Task status enum."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class DeliveryConfidence(Enum):
    """Delivery Confidence Assessment."""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


# ============================================================================
# Mock Models matching pm-data-tools
# ============================================================================

@dataclass
class Duration:
    """Duration model."""
    days: float

    def __int__(self):
        return int(self.days)


@dataclass
class SourceInfo:
    """Source information."""
    tool: str = "test"
    version: str = "1.0"


@dataclass
class Task:
    """Mock task matching pm-data-tools Task model."""
    id: str
    name: str
    source: SourceInfo = field(default_factory=lambda: SourceInfo())
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None
    duration: Optional[Duration] = None
    percent_complete: float = 0.0
    status: TaskStatus = TaskStatus.NOT_STARTED
    is_milestone: bool = False
    is_summary: bool = False
    is_critical: bool = False
    wbs_code: Optional[str] = None
    outline_level: int = 1
    parent_id: Optional[str] = None


@dataclass
class Resource:
    """Mock resource."""
    id: str
    name: str
    source: SourceInfo = field(default_factory=lambda: SourceInfo())
    type: str = "work"


@dataclass
class Dependency:
    """Mock dependency."""
    predecessor_id: str
    successor_id: str
    type: str = "FS"
    lag: int = 0


@dataclass
class Project:
    """Mock project matching pm-data-tools Project model."""
    id: str
    name: str
    source: SourceInfo = field(default_factory=lambda: SourceInfo())
    description: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None
    delivery_confidence: Optional[DeliveryConfidence] = None
    senior_responsible_owner: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    risks: List = field(default_factory=list)

    # Computed properties
    @property
    def task_count(self) -> int:
        return len(self.tasks)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def mock_pm_data_tools():
    """Auto-mock pm_data_tools for all tests."""
    with patch('pm_mcp_servers.pm_data.tools.parse_project') as mock_parse, \
         patch('pm_mcp_servers.pm_data.tools.detect_format') as mock_detect, \
         patch('pm_mcp_servers.pm_data.tools.create_parser') as mock_create_parser, \
         patch('pm_mcp_servers.pm_data.tools.create_exporter') as mock_create_exporter, \
         patch('pm_mcp_servers.pm_validate.tools._get_project') as mock_get_project:

        # Setup parse_project to return a valid Project
        def create_test_project(file_path, **kwargs):
            return Project(
                id="test-project-id",
                name="Test Project",
                description="Test project description",
                start_date=datetime(2026, 1, 1),
                finish_date=datetime(2026, 12, 31),
                delivery_confidence=DeliveryConfidence.GREEN,
                tasks=[
                    Task(
                        id="T1",
                        name="Task 1",
                        start_date=datetime(2026, 1, 1),
                        finish_date=datetime(2026, 1, 31),
                        duration=Duration(30),
                        percent_complete=100.0,
                        status=TaskStatus.COMPLETED,
                        is_critical=True,
                    ),
                    Task(
                        id="T2",
                        name="Task 2",
                        start_date=datetime(2026, 2, 1),
                        finish_date=datetime(2026, 3, 31),
                        duration=Duration(59),
                        percent_complete=50.0,
                        status=TaskStatus.IN_PROGRESS,
                        is_critical=True,
                    ),
                    Task(
                        id="T3",
                        name="Milestone",
                        start_date=datetime(2026, 4, 1),
                        finish_date=datetime(2026, 4, 1),
                        duration=Duration(0),
                        is_milestone=True,
                        is_critical=True,
                    ),
                ],
                resources=[
                    Resource(id="R1", name="Resource 1"),
                    Resource(id="R2", name="Resource 2"),
                ],
                dependencies=[
                    Dependency("T1", "T2", "FS"),
                    Dependency("T2", "T3", "FS"),
                ],
            )

        mock_parse.side_effect = create_test_project
        mock_detect.return_value = "mspdi"

        # Mock parser
        mock_parser = MagicMock()
        mock_parser.parse_file = create_test_project
        mock_create_parser.return_value = mock_parser

        # Mock exporter
        mock_exporter = MagicMock()
        mock_exporter.export_to_string.return_value = '{"name": "Test Project"}'
        mock_create_exporter.return_value = mock_exporter

        # Mock _get_project for validate tools
        mock_get_project.return_value = create_test_project("")

        yield {
            'parse': mock_parse,
            'detect': mock_detect,
            'create_parser': mock_create_parser,
            'create_exporter': mock_create_exporter,
            'get_project': mock_get_project,
        }


@pytest.fixture
def project_store():
    """Provide a fresh ProjectStore for each test."""
    from pm_mcp_servers.pm_data.tools import ProjectStore
    return ProjectStore()
