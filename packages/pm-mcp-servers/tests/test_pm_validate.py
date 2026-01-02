# Comprehensive test suite for PM-Validate
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from contextlib import contextmanager

from pm_mcp_servers.pm_validate.tools import (
    validate_structure,
    validate_semantic,
    validate_nista,
    validate_custom,
)


class MockTask:
    def __init__(self, id: str, name: str, **kwargs):
        self.id = id
        self.name = name
        self.status = kwargs.get("status", "in_progress")
        self.start_date = kwargs.get("start_date")
        self.finish_date = kwargs.get("finish_date")
        self.parent_id = kwargs.get("parent_id")
        self.is_milestone = kwargs.get("is_milestone", False)
        self.total_float = kwargs.get("total_float", None)


class MockDependency:
    def __init__(self, predecessor_id: str, successor_id: str, dep_type: str = "FS"):
        self.predecessor_id = predecessor_id
        self.successor_id = successor_id
        self.type = dep_type


class MockProject:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "Test")
        self.department = kwargs.get("department", "Dept")
        self.category = kwargs.get("category", "infrastructure")
        self.start_date = kwargs.get("start_date", date(2026, 1, 1))
        self.end_date = kwargs.get("end_date", date(2026, 12, 31))
        self.delivery_confidence_assessment = kwargs.get("delivery_confidence_assessment", "green")
        self.description = kwargs.get("description", "Test")
        self.tasks = kwargs.get("tasks", [])
        self.resources = kwargs.get("resources", [])
        self.dependencies = kwargs.get("dependencies", [])


@contextmanager
def mock_get_project(project):
    with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
        yield


class TestValidateStructure:
    @pytest.mark.asyncio
    async def test_valid(self):
        project = MockProject(tasks=[MockTask("1", "Task")])
        with mock_get_project(project):
            result = await validate_structure({"project_id": "test"})
        assert result["valid"] is True
    
    @pytest.mark.asyncio
    async def test_orphan_task(self):
        project = MockProject(tasks=[MockTask("1", "Orphan", parent_id="missing")])
        with mock_get_project(project):
            result = await validate_structure({"project_id": "test", "checks": ["orphan_tasks"]})
        assert any(i["code"] == "ORPHAN_TASK" for i in result["issues"])
    
    @pytest.mark.asyncio
    async def test_circular_deps(self):
        project = MockProject(
            tasks=[MockTask("1", "A"), MockTask("2", "B"), MockTask("3", "C")],
            dependencies=[MockDependency("1", "2"), MockDependency("2", "3"), MockDependency("3", "1")]
        )
        with mock_get_project(project):
            result = await validate_structure({"project_id": "test", "checks": ["circular_dependencies"]})
        assert any(i["code"] == "CIRCULAR_DEPENDENCY" for i in result["issues"])


class TestValidateSemantic:
    @pytest.mark.asyncio
    async def test_negative_float(self):
        project = MockProject(tasks=[MockTask("1", "Slipping", total_float=-5)])
        with mock_get_project(project):
            result = await validate_semantic({"project_id": "test", "rules": ["negative_float"]})
        assert any(i["code"] == "NEGATIVE_FLOAT" for i in result["issues"])


class TestValidateNista:
    @pytest.mark.asyncio
    async def test_compliant(self):
        project = MockProject()
        with mock_get_project(project):
            result = await validate_nista({"project_id": "test"})
        assert result["compliant"] is True
    
    @pytest.mark.asyncio
    async def test_missing_field(self):
        project = MockProject(department=None)
        with mock_get_project(project):
            result = await validate_nista({"project_id": "test"})
        assert result["compliant"] is False


class TestValidateCustom:
    @pytest.mark.asyncio
    async def test_required_passes(self):
        project = MockProject()
        with mock_get_project(project):
            result = await validate_custom({
                "project_id": "test",
                "rules": [{"name": "Name", "field": "name", "condition": "required"}]
            })
        assert result["valid"] is True
