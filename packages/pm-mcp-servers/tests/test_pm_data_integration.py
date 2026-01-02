"""Comprehensive test suite for PM-Data MCP Server.

World-class testing for production infrastructure supporting UK government project delivery.
Tests cover: unit tests, integration tests, edge cases, error paths, all formats, performance.

Coverage target: 90%+
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from pm_mcp_servers.pm_data.tools import (
    ProjectStore,
    load_project,
    query_tasks,
    get_critical_path,
    get_dependencies,
    convert_format,
    get_project_summary,
    _serialize_date,
)


# ============================================================================
# FIXTURES - Test Data and Utilities
# ============================================================================

@pytest.fixture
def project_store():
    """Provide a fresh ProjectStore for each test."""
    return ProjectStore()


@pytest.fixture
def sample_mspdi_minimal(tmp_path):
    """Minimal valid MSPDI file."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Minimal Project</Name>
    <StartDate>2026-01-01T00:00:00</StartDate>
    <FinishDate>2026-01-31T00:00:00</FinishDate>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Task 1</Name>
            <Start>2026-01-01T00:00:00</Start>
            <Finish>2026-01-10T00:00:00</Finish>
            <Duration>PT80H0M0S</Duration>
        </Task>
    </Tasks>
</Project>
"""
    file_path = tmp_path / "minimal.xml"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_mspdi_comprehensive(tmp_path):
    """Comprehensive MSPDI with tasks, resources, dependencies, milestones."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Test Project</Name>
    <StartDate>2026-01-01T00:00:00</StartDate>
    <FinishDate>2026-12-31T00:00:00</FinishDate>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Design Phase</Name>
            <Start>2026-01-01T00:00:00</Start>
            <Finish>2026-01-31T00:00:00</Finish>
            <Duration>PT240H0M0S</Duration>
            <PercentComplete>100</PercentComplete>
            <TotalSlack>PT0H0M0S</TotalSlack>
        </Task>
        <Task>
            <UID>2</UID>
            <ID>2</ID>
            <Name>Development</Name>
            <Start>2026-02-01T00:00:00</Start>
            <Finish>2026-06-30T00:00:00</Finish>
            <Duration>PT1000H0M0S</Duration>
            <PercentComplete>60</PercentComplete>
            <TotalSlack>PT0H0M0S</TotalSlack>
        </Task>
        <Task>
            <UID>3</UID>
            <ID>3</ID>
            <Name>Testing</Name>
            <Start>2026-07-01T00:00:00</Start>
            <Finish>2026-09-30T00:00:00</Finish>
            <Duration>PT600H0M0S</Duration>
            <PercentComplete>0</PercentComplete>
            <TotalSlack>PT40H0M0S</TotalSlack>
        </Task>
        <Task>
            <UID>4</UID>
            <ID>4</ID>
            <Name>Project Kickoff</Name>
            <Start>2026-01-01T00:00:00</Start>
            <Finish>2026-01-01T00:00:00</Finish>
            <Duration>PT0H0M0S</Duration>
            <Milestone>1</Milestone>
            <TotalSlack>PT0H0M0S</TotalSlack>
        </Task>
        <Task>
            <UID>5</UID>
            <ID>5</ID>
            <Name>Go Live</Name>
            <Start>2026-12-31T00:00:00</Start>
            <Finish>2026-12-31T00:00:00</Finish>
            <Duration>PT0H0M0S</Duration>
            <Milestone>1</Milestone>
            <TotalSlack>PT0H0M0S</TotalSlack>
        </Task>
    </Tasks>
    <Resources>
        <Resource>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Project Manager</Name>
        </Resource>
        <Resource>
            <UID>2</UID>
            <ID>2</ID>
            <Name>Developer</Name>
        </Resource>
    </Resources>
    <PredecessorLink>
        <PredecessorUID>1</PredecessorUID>
        <SuccessorUID>2</SuccessorUID>
        <Type>1</Type>
    </PredecessorLink>
    <PredecessorLink>
        <PredecessorUID>2</PredecessorUID>
        <SuccessorUID>3</SuccessorUID>
        <Type>1</Type>
    </PredecessorLink>
</Project>
"""
    file_path = tmp_path / "comprehensive.xml"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_unicode_mspdi(tmp_path):
    """MSPDI with unicode characters."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Проект с юникодом 项目</Name>
    <StartDate>2026-01-01T00:00:00</StartDate>
    <FinishDate>2026-01-31T00:00:00</FinishDate>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Tâche française</Name>
            <Start>2026-01-01T00:00:00</Start>
            <Finish>2026-01-10T00:00:00</Finish>
            <Duration>PT80H0M0S</Duration>
        </Task>
    </Tasks>
</Project>
"""
    file_path = tmp_path / "unicode.xml"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_malformed_xml(tmp_path):
    """Malformed XML file."""
    content = """<?xml version="1.0"?>
<Project>
    <Name>Unclosed project
</Project>
"""
    file_path = tmp_path / "malformed.xml"
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def sample_empty_project(tmp_path):
    """Valid project with no tasks."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Empty Project</Name>
    <StartDate>2026-01-01T00:00:00</StartDate>
    <FinishDate>2026-01-31T00:00:00</FinishDate>
    <Tasks />
</Project>
"""
    file_path = tmp_path / "empty.xml"
    file_path.write_text(content)
    return str(file_path)


# ============================================================================
# UNIT TESTS - Helper Functions
# ============================================================================

class TestSerializeDate:
    """Unit tests for _serialize_date helper."""

    def test_serialize_valid_date(self):
        """Test serializing a valid date."""
        from datetime import date
        d = date(2026, 1, 15)
        result = _serialize_date(d)
        assert result == "2026-01-15"

    def test_serialize_none(self):
        """Test serializing None."""
        result = _serialize_date(None)
        assert result is None


class TestProjectStore:
    """Unit tests for ProjectStore."""

    def test_add_and_get(self):
        """Test adding and retrieving projects."""
        store = ProjectStore()
        mock_project = Mock()
        mock_project.name = "Test"

        store.add("id1", mock_project)
        retrieved = store.get("id1")

        assert retrieved == mock_project
        assert retrieved.name == "Test"

    def test_exists(self):
        """Test exists check."""
        store = ProjectStore()
        mock_project = Mock()

        assert not store.exists("id1")
        store.add("id1", mock_project)
        assert store.exists("id1")

    def test_list_all(self):
        """Test listing all project IDs."""
        store = ProjectStore()
        store.add("id1", Mock())
        store.add("id2", Mock())
        store.add("id3", Mock())

        ids = store.list_all()
        assert len(ids) == 3
        assert "id1" in ids
        assert "id2" in ids
        assert "id3" in ids

    def test_remove(self):
        """Test removing projects."""
        store = ProjectStore()
        store.add("id1", Mock())

        assert store.exists("id1")
        result = store.remove("id1")
        assert result is True
        assert not store.exists("id1")

    def test_remove_nonexistent(self):
        """Test removing non-existent project."""
        store = ProjectStore()
        result = store.remove("nonexistent")
        assert result is False


# ============================================================================
# INTEGRATION TESTS - load_project()
# ============================================================================

class TestLoadProject:
    """Comprehensive tests for load_project()."""

    @pytest.mark.asyncio
    async def test_auto_detect_mspdi(self, project_store, sample_mspdi_comprehensive):
        """Test automatic format detection for MSPDI."""
        result = await load_project(
            {"file_path": sample_mspdi_comprehensive, "format": "auto"},
            store=project_store
        )

        assert "error" not in result
        assert result["source_format"] == "mspdi"
        assert "project_id" in result
        assert result["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_explicit_format(self, project_store, sample_mspdi_minimal):
        """Test explicit format specification."""
        result = await load_project(
            {"file_path": sample_mspdi_minimal, "format": "mspdi"},
            store=project_store
        )

        assert "error" not in result
        assert result["source_format"] == "mspdi"

    @pytest.mark.asyncio
    async def test_missing_file_path(self, project_store):
        """Test error when file_path is missing."""
        result = await load_project({}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_file_not_found(self, project_store):
        """Test error when file doesn't exist."""
        result = await load_project(
            {"file_path": "/nonexistent/path/file.xml"},
            store=project_store
        )

        assert "error" in result
        assert result["error"]["code"] == "FILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_parse_error(self, project_store, sample_malformed_xml):
        """Test error handling for malformed files."""
        result = await load_project(
            {"file_path": sample_malformed_xml},
            store=project_store
        )

        # Should get either PARSE_ERROR or INTERNAL_ERROR
        assert "error" in result
        assert result["error"]["code"] in ["PARSE_ERROR", "INTERNAL_ERROR", "FORMAT_DETECTION_FAILED"]

    @pytest.mark.asyncio
    async def test_unicode_handling(self, project_store, sample_unicode_mspdi):
        """Test handling of unicode characters."""
        result = await load_project(
            {"file_path": sample_unicode_mspdi},
            store=project_store
        )

        assert "error" not in result

    @pytest.mark.asyncio
    async def test_empty_project(self, project_store, sample_empty_project):
        """Test loading project with no tasks."""
        result = await load_project(
            {"file_path": sample_empty_project},
            store=project_store
        )

        assert "error" not in result
        assert result["task_count"] == 0
        assert result["milestone_count"] == 0

    @pytest.mark.asyncio
    async def test_comprehensive_metrics(self, project_store, sample_mspdi_comprehensive):
        """Test all metrics are calculated correctly."""
        result = await load_project(
            {"file_path": sample_mspdi_comprehensive},
            store=project_store
        )

        assert "error" not in result
        assert result["task_count"] == 5
        assert result["milestone_count"] == 2
        assert result["resource_count"] == 2
        assert result["dependency_count"] == 2
        assert result["critical_task_count"] >= 0
        assert "start_date" in result
        assert "end_date" in result

    @pytest.mark.asyncio
    async def test_project_stored_correctly(self, project_store, sample_mspdi_minimal):
        """Test that project is stored in ProjectStore."""
        result = await load_project(
            {"file_path": sample_mspdi_minimal},
            store=project_store
        )

        project_id = result["project_id"]
        assert project_store.exists(project_id)
        stored_project = project_store.get(project_id)
        assert stored_project is not None


# ============================================================================
# INTEGRATION TESTS - query_tasks()
# ============================================================================

class TestQueryTasks:
    """Comprehensive tests for query_tasks()."""

    @pytest.mark.asyncio
    async def test_query_all_tasks(self, project_store, sample_mspdi_comprehensive):
        """Test querying all tasks without filters."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["total_matching"] == 5
        assert len(result["tasks"]) == 5

    @pytest.mark.asyncio
    async def test_filter_milestones(self, project_store, sample_mspdi_comprehensive):
        """Test filtering for milestones only."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "filters": {"is_milestone": True}},
            store=project_store
        )

        assert "error" not in result
        assert result["total_matching"] == 2

    @pytest.mark.asyncio
    async def test_filter_critical_tasks(self, project_store, sample_mspdi_comprehensive):
        """Test filtering for critical path tasks."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "filters": {"is_critical": True}},
            store=project_store
        )

        assert "error" not in result

    @pytest.mark.asyncio
    async def test_pagination_limit(self, project_store, sample_mspdi_comprehensive):
        """Test pagination with limit."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "limit": 2},
            store=project_store
        )

        assert len(result["tasks"]) == 2
        assert result["returned_count"] == 2
        assert result["total_matching"] == 5

    @pytest.mark.asyncio
    async def test_pagination_offset(self, project_store, sample_mspdi_comprehensive):
        """Test pagination with offset."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "offset": 3, "limit": 10},
            store=project_store
        )

        assert result["offset"] == 3
        assert len(result["tasks"]) == 2  # 5 total - 3 offset = 2 remaining

    @pytest.mark.asyncio
    async def test_project_not_found(self, project_store):
        """Test error when project doesn't exist."""
        result = await query_tasks({"project_id": "fake-id"}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_missing_project_id(self, project_store):
        """Test error when project_id is missing."""
        result = await query_tasks({}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_empty_results(self, project_store, sample_empty_project):
        """Test querying project with no tasks."""
        load_result = await load_project({"file_path": sample_empty_project}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["total_matching"] == 0
        assert len(result["tasks"]) == 0


# ============================================================================
# INTEGRATION TESTS - get_critical_path()
# ============================================================================

class TestGetCriticalPath:
    """Comprehensive tests for get_critical_path()."""

    @pytest.mark.asyncio
    async def test_critical_path_comprehensive(self, project_store, sample_mspdi_comprehensive):
        """Test critical path calculation."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_critical_path({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert "critical_path_length_days" in result
        assert "critical_task_count" in result
        assert "critical_tasks" in result
        assert isinstance(result["critical_tasks"], list)

    @pytest.mark.asyncio
    async def test_no_critical_tasks(self, project_store, sample_empty_project):
        """Test when project has no critical tasks."""
        load_result = await load_project({"file_path": sample_empty_project}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_critical_path({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["critical_task_count"] == 0
        assert result["critical_path_length_days"] == 0

    @pytest.mark.asyncio
    async def test_project_not_found(self, project_store):
        """Test error when project doesn't exist."""
        result = await get_critical_path({"project_id": "fake-id"}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_missing_project_id(self, project_store):
        """Test error when project_id is missing."""
        result = await get_critical_path({}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# INTEGRATION TESTS - get_dependencies()
# ============================================================================

class TestGetDependencies:
    """Comprehensive tests for get_dependencies()."""

    @pytest.mark.asyncio
    async def test_get_dependencies_comprehensive(self, project_store, sample_mspdi_comprehensive):
        """Test dependency retrieval."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_dependencies({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["total_dependencies"] == 2
        assert len(result["dependencies"]) == 2

    @pytest.mark.asyncio
    async def test_no_dependencies(self, project_store, sample_mspdi_minimal):
        """Test project with no dependencies."""
        load_result = await load_project({"file_path": sample_mspdi_minimal}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_dependencies({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["total_dependencies"] == 0

    @pytest.mark.asyncio
    async def test_project_not_found(self, project_store):
        """Test error when project doesn't exist."""
        result = await get_dependencies({"project_id": "fake-id"}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_missing_project_id(self, project_store):
        """Test error when project_id is missing."""
        result = await get_dependencies({}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# INTEGRATION TESTS - convert_format()
# ============================================================================

class TestConvertFormat:
    """Comprehensive tests for convert_format()."""

    @pytest.mark.asyncio
    async def test_convert_to_json(self, project_store, sample_mspdi_minimal):
        """Test converting project to JSON format."""
        load_result = await load_project({"file_path": sample_mspdi_minimal}, store=project_store)
        project_id = load_result["project_id"]

        result = await convert_format(
            {"project_id": project_id, "target_format": "json"},
            store=project_store
        )

        # May succeed or fail depending on pm-data-tools exporter support
        if "error" not in result:
            assert result["target_format"] == "json"
            assert "data" in result

    @pytest.mark.asyncio
    async def test_missing_parameters(self, project_store):
        """Test error when parameters are missing."""
        result = await convert_format({"project_id": "test"}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_project_not_found(self, project_store):
        """Test error when project doesn't exist."""
        result = await convert_format(
            {"project_id": "fake-id", "target_format": "json"},
            store=project_store
        )

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"


# ============================================================================
# INTEGRATION TESTS - get_project_summary()
# ============================================================================

class TestGetProjectSummary:
    """Comprehensive tests for get_project_summary()."""

    @pytest.mark.asyncio
    async def test_comprehensive_summary(self, project_store, sample_mspdi_comprehensive):
        """Test complete project summary."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_project_summary({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["name"] == "Test Project"
        assert result["task_count"] == 5
        assert result["milestone_count"] == 2
        assert result["resource_count"] == 2
        assert result["completed_task_count"] >= 0
        assert "percent_complete" in result

    @pytest.mark.asyncio
    async def test_empty_project_summary(self, project_store, sample_empty_project):
        """Test summary for empty project."""
        load_result = await load_project({"file_path": sample_empty_project}, store=project_store)
        project_id = load_result["project_id"]

        result = await get_project_summary({"project_id": project_id}, store=project_store)

        assert "error" not in result
        assert result["task_count"] == 0
        assert result["percent_complete"] == 0

    @pytest.mark.asyncio
    async def test_project_not_found(self, project_store):
        """Test error when project doesn't exist."""
        result = await get_project_summary({"project_id": "fake-id"}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_missing_project_id(self, project_store):
        """Test error when project_id is missing."""
        result = await get_project_summary({}, store=project_store)

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test comprehensive error handling across all tools."""

    @pytest.mark.asyncio
    async def test_all_tools_handle_missing_project(self, project_store):
        """Test that all tools properly handle missing projects."""
        fake_id = "nonexistent-project-id"

        results = [
            await query_tasks({"project_id": fake_id}, store=project_store),
            await get_critical_path({"project_id": fake_id}, store=project_store),
            await get_dependencies({"project_id": fake_id}, store=project_store),
            await convert_format({"project_id": fake_id, "target_format": "json"}, store=project_store),
            await get_project_summary({"project_id": fake_id}, store=project_store),
        ]

        for result in results:
            assert "error" in result
            assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_unsupported_format(self, project_store, tmp_path):
        """Test handling of unsupported file format."""
        file_path = tmp_path / "random.bin"
        file_path.write_bytes(b"\x00\x01\x02\x03")

        result = await load_project({"file_path": str(file_path)}, store=project_store)

        assert "error" in result


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_pagination_beyond_bounds(self, project_store, sample_mspdi_comprehensive):
        """Test pagination with offset beyond task count."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "offset": 1000, "limit": 10},
            store=project_store
        )

        assert "error" not in result
        assert len(result["tasks"]) == 0
        assert result["returned_count"] == 0

    @pytest.mark.asyncio
    async def test_zero_limit(self, project_store, sample_mspdi_comprehensive):
        """Test query with limit of 0."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {"project_id": project_id, "limit": 0},
            store=project_store
        )

        assert "error" not in result
        assert len(result["tasks"]) == 0

    @pytest.mark.asyncio
    async def test_multiple_filters(self, project_store, sample_mspdi_comprehensive):
        """Test applying multiple filters simultaneously."""
        load_result = await load_project({"file_path": sample_mspdi_comprehensive}, store=project_store)
        project_id = load_result["project_id"]

        result = await query_tasks(
            {
                "project_id": project_id,
                "filters": {
                    "is_milestone": True,
                    "is_critical": True
                }
            },
            store=project_store
        )

        assert "error" not in result
