"""Integration tests for PM-Data MCP Server with real pm-data-tools parsers.

Tests the integration between MCP server tools and pm-data-tools library.
Requires pm-data-tools>=0.2.0 to be installed.
"""

import pytest
from pathlib import Path
from pm_mcp_servers.pm_data.tools import (
    ProjectStore,
    load_project,
    query_tasks,
    get_critical_path,
    get_dependencies,
    convert_format,
    get_project_summary,
)


@pytest.fixture
def project_store():
    """Provide a fresh ProjectStore for each test."""
    return ProjectStore()


@pytest.fixture
def sample_mspdi_path(tmp_path):
    """Create a minimal valid MSPDI file for testing."""
    mspdi_content = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Test Project</Name>
    <StartDate>2026-01-01T00:00:00</StartDate>
    <FinishDate>2026-12-31T00:00:00</FinishDate>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Task 1</Name>
            <Start>2026-01-01T00:00:00</Start>
            <Finish>2026-01-10T00:00:00</Finish>
            <Duration>PT80H0M0S</Duration>
            <PercentComplete>100</PercentComplete>
        </Task>
        <Task>
            <UID>2</UID>
            <ID>2</ID>
            <Name>Milestone</Name>
            <Start>2026-01-11T00:00:00</Start>
            <Finish>2026-01-11T00:00:00</Finish>
            <Duration>PT0H0M0S</Duration>
            <Milestone>1</Milestone>
        </Task>
    </Tasks>
</Project>
"""
    
    file_path = tmp_path / "test_project.xml"
    file_path.write_text(mspdi_content)
    return str(file_path)


@pytest.mark.asyncio
async def test_load_project_auto_detect(project_store, sample_mspdi_path):
    """Test loading project with automatic format detection."""
    result = await load_project(
        {"file_path": sample_mspdi_path, "format": "auto"},
        store=project_store
    )
    
    assert "error" not in result
    assert "project_id" in result
    assert result["name"] == "Test Project"
    assert result["source_format"] == "mspdi"
    assert result["task_count"] >= 2
    

@pytest.mark.asyncio
async def test_load_project_explicit_format(project_store, sample_mspdi_path):
    """Test loading project with explicit format specification."""
    result = await load_project(
        {"file_path": sample_mspdi_path, "format": "mspdi"},
        store=project_store
    )
    
    assert "error" not in result
    assert result["source_format"] == "mspdi"
    assert "project_id" in result
    

@pytest.mark.asyncio
async def test_load_project_file_not_found(project_store):
    """Test error handling for non-existent file."""
    result = await load_project(
        {"file_path": "/nonexistent/file.xml"},
        store=project_store
    )
    
    assert "error" in result
    assert result["error"]["code"] == "FILE_NOT_FOUND"
    

@pytest.mark.asyncio
async def test_query_tasks_all(project_store, sample_mspdi_path):
    """Test querying all tasks."""
    # Load project first
    load_result = await load_project(
        {"file_path": sample_mspdi_path},
        store=project_store
    )
    project_id = load_result["project_id"]
    
    # Query all tasks
    result = await query_tasks(
        {"project_id": project_id},
        store=project_store
    )
    
    assert "error" not in result
    assert result["total_matching"] >= 2
    assert len(result["tasks"]) >= 2
    

@pytest.mark.asyncio
async def test_query_tasks_with_filters(project_store, sample_mspdi_path):
    """Test querying tasks with filters."""
    load_result = await load_project(
        {"file_path": sample_mspdi_path},
        store=project_store
    )
    project_id = load_result["project_id"]
    
    # Query milestones only
    result = await query_tasks(
        {
            "project_id": project_id,
            "filters": {"is_milestone": True}
        },
        store=project_store
    )
    
    assert "error" not in result
    # Should find the milestone task
    

@pytest.mark.asyncio
async def test_get_critical_path(project_store, sample_mspdi_path):
    """Test critical path calculation."""
    load_result = await load_project(
        {"file_path": sample_mspdi_path},
        store=project_store
    )
    project_id = load_result["project_id"]
    
    result = await get_critical_path(
        {"project_id": project_id},
        store=project_store
    )
    
    assert "error" not in result
    assert "critical_path_length_days" in result
    assert "critical_tasks" in result
    

@pytest.mark.asyncio
async def test_get_dependencies(project_store, sample_mspdi_path):
    """Test dependency retrieval."""
    load_result = await load_project(
        {"file_path": sample_mspdi_path},
        store=project_store
    )
    project_id = load_result["project_id"]
    
    result = await get_dependencies(
        {"project_id": project_id},
        store=project_store
    )
    
    assert "error" not in result
    assert "dependencies" in result
    

@pytest.mark.asyncio
async def test_get_project_summary(project_store, sample_mspdi_path):
    """Test project summary generation."""
    load_result = await load_project(
        {"file_path": sample_mspdi_path},
        store=project_store
    )
    project_id = load_result["project_id"]
    
    result = await get_project_summary(
        {"project_id": project_id},
        store=project_store
    )
    
    assert "error" not in result
    assert result["name"] == "Test Project"
    assert result["task_count"] >= 2
    assert result["milestone_count"] >= 1
    assert "percent_complete" in result
    

@pytest.mark.asyncio
async def test_project_not_found_errors(project_store):
    """Test that all tools return proper errors for non-existent projects."""
    fake_id = "nonexistent-project-id"
    
    # Test each tool
    tasks_result = await query_tasks({"project_id": fake_id}, store=project_store)
    assert tasks_result["error"]["code"] == "PROJECT_NOT_FOUND"
    
    cp_result = await get_critical_path({"project_id": fake_id}, store=project_store)
    assert cp_result["error"]["code"] == "PROJECT_NOT_FOUND"
    
    deps_result = await get_dependencies({"project_id": fake_id}, store=project_store)
    assert deps_result["error"]["code"] == "PROJECT_NOT_FOUND"
    
    summary_result = await get_project_summary({"project_id": fake_id}, store=project_store)
    assert summary_result["error"]["code"] == "PROJECT_NOT_FOUND"
