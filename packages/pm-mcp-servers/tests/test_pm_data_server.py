"""Tests for PM-Data MCP Server - Basic functionality tests."""

import pytest
from pathlib import Path

# Import tools for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pm_mcp_servers.pm_data.tools import (
    load_project,
    query_tasks,
    ProjectStore,
)


@pytest.mark.asyncio
async def test_load_project_file_not_found():
    """Test loading a non-existent file."""
    store = ProjectStore()
    result = await load_project(
        {"file_path": "/nonexistent/file.xml", "format": "mspdi"},
        store
    )

    assert "error" in result
    assert result["error"]["code"] == "FILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_load_project_creates_entry(tmp_path):
    """Test that loading a project creates an entry in the store."""
    test_file = tmp_path / "test.xml"
    test_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Test Project</Name>
</Project>''')

    store = ProjectStore()
    result = await load_project(
        {"file_path": str(test_file), "format": "mspdi"},
        store
    )

    assert "project_id" in result
    assert "name" in result
    assert store.exists(result["project_id"])


@pytest.mark.asyncio
async def test_query_tasks_project_not_found():
    """Test querying tasks from non-existent project."""
    store = ProjectStore()
    result = await query_tasks(
        {"project_id": "nonexistent"},
        store
    )

    assert "error" in result
    assert result["error"]["code"] == "PROJECT_NOT_FOUND"
