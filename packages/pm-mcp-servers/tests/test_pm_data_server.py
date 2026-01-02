"""Tests for PM-Data MCP Server."""

import pytest
from pathlib import Path

# Import tools for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pm_mcp_servers.pm_data.tools import (
    load_project,
    query_tasks,
    get_critical_path,
    get_dependencies,
    convert_format,
    get_project_summary,
)


@pytest.mark.asyncio
async def test_load_project_file_not_found():
    """Test loading a non-existent file."""
    projects = {}
    result = await load_project(
        {"file_path": "/nonexistent/file.xml", "format": "mspdi"},
        projects
    )

    assert "error" in result
    assert result["error"]["code"] == "FILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_load_project_creates_entry(tmp_path):
    """Test that loading a project creates an entry in the store."""
    # Create a temp file
    test_file = tmp_path / "test.xml"
    test_file.write_text("<Project></Project>")

    projects = {}
    result = await load_project(
        {"file_path": str(test_file), "format": "mspdi"},
        projects
    )

    assert "project_id" in result
    assert "name" in result
    assert result["project_id"] in projects
    assert result["task_count"] >= 0


@pytest.mark.asyncio
async def test_query_tasks_project_not_found():
    """Test querying tasks from non-existent project."""
    projects = {}
    result = await query_tasks(
        {"project_id": "nonexistent"},
        projects
    )

    assert "error" in result
    assert result["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.asyncio
async def test_query_tasks_with_filters():
    """Test querying tasks with filters."""
    # Setup: create mock project in memory
    projects = {
        "test123": {
            "tasks": [
                {"id": "t1", "name": "Task 1", "status": "completed", "is_critical": True, "is_milestone": False, "start_date": "2026-01-01", "finish_date": "2026-01-10", "percent_complete": 100, "duration": 10},
                {"id": "t2", "name": "Task 2", "status": "in_progress", "is_critical": False, "is_milestone": True, "start_date": "2026-01-11", "finish_date": "2026-01-11", "percent_complete": 0, "duration": 0},
            ]
        }
    }

    result = await query_tasks(
        {"project_id": "test123", "filters": {"is_critical": True}},
        projects
    )

    assert "tasks" in result
    assert result["total_matching"] == 1
    assert result["tasks"][0]["id"] == "t1"


@pytest.mark.asyncio
async def test_get_critical_path():
    """Test getting critical path."""
    projects = {
        "test123": {
            "tasks": [
                {"id": "t1", "name": "Critical Task", "is_critical": True, "duration": 10, "start_date": "2026-01-01", "finish_date": "2026-01-10", "percent_complete": 50, "total_float": 0},
                {"id": "t2", "name": "Non-Critical", "is_critical": False, "duration": 5, "start_date": "2026-01-01", "finish_date": "2026-01-05", "percent_complete": 0, "total_float": 3},
            ]
        }
    }

    result = await get_critical_path(
        {"project_id": "test123", "include_near_critical": True},
        projects
    )

    assert "critical_path_length_days" in result
    assert result["critical_path_length_days"] == 10
    assert result["critical_task_count"] == 1
    assert len(result["near_critical_tasks"]) == 1


@pytest.mark.asyncio
async def test_get_dependencies():
    """Test getting dependencies."""
    projects = {
        "test123": {
            "dependencies": [
                {"predecessor_id": "t1", "successor_id": "t2", "type": "FS", "lag": 0},
                {"predecessor_id": "t2", "successor_id": "t3", "type": "FS", "lag": 2},
            ]
        }
    }

    result = await get_dependencies(
        {"project_id": "test123", "task_id": "t2", "direction": "both"},
        projects
    )

    assert "predecessors" in result
    assert "successors" in result
    assert len(result["predecessors"]) == 1
    assert len(result["successors"]) == 1


@pytest.mark.asyncio
async def test_convert_format_json():
    """Test converting to JSON format."""
    projects = {
        "test123": {
            "name": "Test Project",
            "tasks": [],
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        }
    }

    result = await convert_format(
        {"project_id": "test123", "target_format": "json"},
        projects
    )

    assert "data" in result
    assert result["target_format"] == "json"


@pytest.mark.asyncio
async def test_get_project_summary():
    """Test getting project summary."""
    projects = {
        "test123": {
            "name": "Test Project",
            "source_file": "/path/to/file.xml",
            "source_format": "mspdi",
            "tasks": [
                {"id": "t1", "is_milestone": True, "is_critical": True, "percent_complete": 100, "duration": 5},
                {"id": "t2", "is_milestone": False, "is_critical": False, "percent_complete": 0, "duration": 10},
            ],
            "resources": [{"id": "r1"}],
            "dependencies": [{"predecessor_id": "t1", "successor_id": "t2", "type": "FS"}],
            "start_date": "2026-01-01",
            "end_date": "2026-02-28"
        }
    }

    result = await get_project_summary(
        {"project_id": "test123"},
        projects
    )

    assert result["project_id"] == "test123"
    assert result["task_count"] == 2
    assert result["resource_count"] == 1
    assert result["dependency_count"] == 1
    assert result["milestone_count"] == 1
    assert result["critical_task_count"] == 1
    assert result["percent_complete"] == 50.0
