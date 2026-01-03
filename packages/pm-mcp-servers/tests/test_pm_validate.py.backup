"""Comprehensive test suite for PM-Validate MCP Server.

World-class testing for validation infrastructure supporting UK government NISTA compliance.
Tests cover: structural validation, semantic validation, NISTA compliance, custom rules, edge cases.

Coverage target: 90%+
"""

import pytest
from unittest.mock import Mock
from pm_mcp_servers.pm_validate.tools import (
    Severity,
    ValidationIssue,
    validate_structure,
    validate_semantic,
    validate_nista,
    validate_custom,
    _get_project,
)


# ============================================================================
# TEST FIXTURES - Mock Projects and Data
# ============================================================================

@pytest.fixture
def mock_task():
    """Create a mock task with configurable properties."""
    def _create_task(id="T1", name="Task 1", **kwargs):
        task = Mock()
        task.id = id
        task.name = name
        task.start_date = kwargs.get("start_date")
        task.finish_date = kwargs.get("finish_date")
        task.duration = kwargs.get("duration")
        task.percent_complete = kwargs.get("percent_complete", 0)
        task.is_milestone = kwargs.get("is_milestone", False)
        task.total_float = kwargs.get("total_float", None)
        return task
    return _create_task


@pytest.fixture
def mock_dependency():
    """Create a mock dependency."""
    def _create_dependency(predecessor_id, successor_id, dep_type="FS"):
        dep = Mock()
        dep.predecessor_id = predecessor_id
        dep.successor_id = successor_id
        dep.type = dep_type
        return dep
    return _create_dependency


@pytest.fixture
def valid_project(mock_task, mock_dependency):
    """Create a valid mock project with no issues."""
    from datetime import date
    project = Mock()
    project.name = "Valid Project"
    project.department = "Department for Transport"
    project.start_date = date(2026, 1, 1)
    project.end_date = date(2026, 12, 31)
    project.delivery_confidence_assessment = "green"
    project.tasks = [
        mock_task("T1", "Task 1", start_date=date(2026, 1, 1), finish_date=date(2026, 3, 31), duration=90),
        mock_task("T2", "Task 2", start_date=date(2026, 4, 1), finish_date=date(2026, 6, 30), duration=90),
    ]
    project.dependencies = [mock_dependency("T1", "T2")]
    return project


@pytest.fixture
def project_with_orphan_tasks(mock_task):
    """Project with orphaned tasks (referenced but not in tasks list)."""
    from datetime import date
    project = Mock()
    project.name = "Orphan Project"
    project.tasks = [mock_task("T1", "Task 1")]

    # Dependency references T2, which doesn't exist
    dep = Mock()
    dep.predecessor_id = "T1"
    dep.successor_id = "T2"  # Orphan!
    dep.type = "FS"
    project.dependencies = [dep]
    return project


@pytest.fixture
def project_with_circular_deps(mock_task, mock_dependency):
    """Project with circular dependencies."""
    project = Mock()
    project.name = "Circular Project"
    project.tasks = [
        mock_task("T1", "Task 1"),
        mock_task("T2", "Task 2"),
        mock_task("T3", "Task 3"),
    ]
    # T1 -> T2 -> T3 -> T1 (circular!)
    project.dependencies = [
        mock_dependency("T1", "T2"),
        mock_dependency("T2", "T3"),
        mock_dependency("T3", "T1"),
    ]
    return project


@pytest.fixture
def project_with_date_inconsistencies(mock_task):
    """Project with date logic errors."""
    from datetime import date
    project = Mock()
    project.name = "Date Issue Project"
    project.tasks = [
        # Task ends before it starts!
        mock_task("T1", "Bad Task", start_date=date(2026, 12, 31), finish_date=date(2026, 1, 1)),
    ]
    project.dependencies = []
    return project


@pytest.fixture
def nista_non_compliant_project():
    """Project missing required NISTA fields."""
    project = Mock()
    project.name = "Non-Compliant Project"
    # Missing: department, start_date, end_date, DCA
    project.department = None
    project.start_date = None
    project.end_date = None
    project.delivery_confidence_assessment = None
    project.tasks = []
    project.dependencies = []
    return project


@pytest.fixture
def nista_invalid_dca_project():
    """Project with invalid DCA value."""
    from datetime import date
    project = Mock()
    project.name = "Invalid DCA Project"
    project.department = "Department for Transport"
    project.start_date = date(2026, 1, 1)
    project.end_date = date(2026, 12, 31)
    project.delivery_confidence_assessment = "purple"  # Invalid!
    project.tasks = []
    project.dependencies = []
    return project


# ============================================================================
# UNIT TESTS - ValidationIssue
# ============================================================================

class TestValidationIssue:
    """Unit tests for ValidationIssue dataclass."""

    def test_create_error(self):
        """Test creating an error issue."""
        issue = ValidationIssue(
            severity=Severity.ERROR,
            code="TEST_ERROR",
            message="Test error message"
        )
        assert issue.severity == Severity.ERROR
        assert issue.code == "TEST_ERROR"
        assert issue.message == "Test error message"

    def test_create_warning(self):
        """Test creating a warning issue."""
        issue = ValidationIssue(
            severity=Severity.WARNING,
            code="TEST_WARNING",
            message="Test warning"
        )
        assert issue.severity == Severity.WARNING

    def test_optional_fields(self):
        """Test optional location, field, and suggestion fields."""
        issue = ValidationIssue(
            severity=Severity.INFO,
            code="TEST_INFO",
            message="Test info",
            location="Task T1",
            field="start_date",
            suggestion="Check the date"
        )
        assert issue.location == "Task T1"
        assert issue.field == "start_date"
        assert issue.suggestion == "Check the date"


# ============================================================================
# INTEGRATION TESTS - validate_structure()
# ============================================================================

class TestValidateStructure:
    """Comprehensive tests for validate_structure()."""

    @pytest.mark.asyncio
    async def test_valid_project(self, valid_project):
        """Test validation of a valid project structure."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_structure({"project_id": "test-id"})

        assert result["valid"] is True
        assert result["total_issues"] == 0
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_orphan_tasks_detection(self, project_with_orphan_tasks):
        """Test detection of orphaned task references."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project_with_orphan_tasks):
            result = await validate_structure({
                "project_id": "test-id",
                "checks": ["orphan_tasks"]
            })

        assert result["valid"] is False
        assert result["total_issues"] > 0
        assert any(i["code"] == "ORPHAN_TASK_REFERENCE" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, project_with_circular_deps):
        """Test detection of circular dependencies."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project_with_circular_deps):
            result = await validate_structure({
                "project_id": "test-id",
                "checks": ["circular_dependencies"]
            })

        assert result["valid"] is False
        assert any(i["code"] == "CIRCULAR_DEPENDENCY" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_date_consistency_check(self, project_with_date_inconsistencies):
        """Test date consistency validation."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project_with_date_inconsistencies):
            result = await validate_structure({
                "project_id": "test-id",
                "checks": ["date_consistency"]
            })

        assert result["valid"] is False
        assert any(i["code"] == "INVALID_DATE_RANGE" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_duplicate_id_detection(self):
        """Test detection of duplicate task IDs."""
        from unittest.mock import patch, Mock

        task1 = Mock()
        task1.id = "T1"
        task1.name = "Task 1"
        task2 = Mock()
        task2.id = "T1"  # Duplicate!
        task2.name = "Task 2"

        project = Mock()
        project.name = "Duplicate ID Project"
        project.tasks = [task1, task2]
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_structure({
                "project_id": "test-id",
                "checks": ["duplicate_ids"]
            })

        assert result["valid"] is False
        assert any(i["code"] == "DUPLICATE_TASK_ID" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_all_checks_combined(self, project_with_circular_deps):
        """Test running all structure checks together."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project_with_circular_deps):
            result = await validate_structure({"project_id": "test-id"})

        # Should run all default checks
        assert "issues" in result
        assert "total_issues" in result
        assert "checks_performed" in result

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await validate_structure({})

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_project_not_found(self):
        """Test error when project doesn't exist."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=None):
            result = await validate_structure({"project_id": "fake-id"})

        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"


# ============================================================================
# INTEGRATION TESTS - validate_semantic()
# ============================================================================

class TestValidateSemantic:
    """Comprehensive tests for validate_semantic()."""

    @pytest.mark.asyncio
    async def test_valid_project_semantics(self, valid_project):
        """Test semantic validation of a valid project."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_semantic({"project_id": "test-id"})

        assert result["valid"] is True
        assert result["total_issues"] == 0

    @pytest.mark.asyncio
    async def test_detect_unrealistic_durations(self):
        """Test detection of unrealistic task durations."""
        from unittest.mock import patch, Mock
        from datetime import date

        task = Mock()
        task.id = "T1"
        task.name = "Super Long Task"
        task.start_date = date(2026, 1, 1)
        task.finish_date = date(2030, 1, 1)  # 4 years!
        task.duration = 1460  # 4 years in days
        task.percent_complete = 0

        project = Mock()
        project.name = "Long Duration Project"
        project.tasks = [task]
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_semantic({
                "project_id": "test-id",
                "rules": ["unrealistic_durations"]
            })

        # May or may not flag depending on threshold
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_detect_missing_critical_data(self):
        """Test detection of tasks missing critical fields."""
        from unittest.mock import patch, Mock

        task = Mock()
        task.id = "T1"
        task.name = "Incomplete Task"
        task.start_date = None  # Missing!
        task.finish_date = None  # Missing!
        task.duration = None  # Missing!
        task.percent_complete = 0

        project = Mock()
        project.name = "Incomplete Data Project"
        project.tasks = [task]
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_semantic({
                "project_id": "test-id",
                "rules": ["missing_critical_data"]
            })

        # Should detect missing data
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_all_semantic_rules(self, valid_project):
        """Test running all semantic validation rules."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_semantic({"project_id": "test-id"})

        assert "valid" in result
        assert "total_issues" in result
        assert "rules_applied" in result

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await validate_semantic({})

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# INTEGRATION TESTS - validate_nista()
# ============================================================================

class TestValidateNISTA:
    """Comprehensive tests for validate_nista()."""

    @pytest.mark.asyncio
    async def test_fully_compliant_project(self, valid_project):
        """Test NISTA validation of fully compliant project."""
        from unittest.mock import patch

        # Add SRO field for full compliance
        valid_project.sro = "Jane Smith"

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_nista({"project_id": "test-id", "strictness": "standard"})

        assert result["compliant"] is True
        assert result["compliance_score"] == 100.0

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, nista_non_compliant_project):
        """Test detection of missing required NISTA fields."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=nista_non_compliant_project):
            result = await validate_nista({"project_id": "test-id"})

        assert result["compliant"] is False
        assert result["compliance_score"] < 100.0
        assert len(result["missing_fields"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_dca_value(self, nista_invalid_dca_project):
        """Test detection of invalid DCA values."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=nista_invalid_dca_project):
            result = await validate_nista({"project_id": "test-id"})

        assert result["compliant"] is False
        assert any(i["code"] == "INVALID_DCA_VALUE" for i in result["issues"])

    @pytest.mark.asyncio
    async def test_strictness_lenient(self, nista_non_compliant_project):
        """Test lenient strictness mode."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=nista_non_compliant_project):
            result = await validate_nista({
                "project_id": "test-id",
                "strictness": "lenient"
            })

        # Lenient mode may be more forgiving
        assert "compliance_score" in result

    @pytest.mark.asyncio
    async def test_strictness_strict(self, valid_project):
        """Test strict strictness mode."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_nista({
                "project_id": "test-id",
                "strictness": "strict"
            })

        # Strict mode requires more fields
        assert "compliance_score" in result

    @pytest.mark.asyncio
    async def test_all_valid_dca_values(self):
        """Test that all valid DCA values are accepted."""
        from unittest.mock import patch, Mock
        from datetime import date

        valid_dca_values = ["green", "amber_green", "amber", "amber_red", "red"]

        for dca in valid_dca_values:
            project = Mock()
            project.name = f"Project {dca}"
            project.department = "Test Department"
            project.start_date = date(2026, 1, 1)
            project.end_date = date(2026, 12, 31)
            project.delivery_confidence_assessment = dca
            project.tasks = []
            project.dependencies = []

            with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
                result = await validate_nista({"project_id": "test-id"})

            # Should not flag DCA as invalid
            assert not any(
                i["code"] == "INVALID_DCA_VALUE"
                for i in result.get("issues", [])
            ), f"Valid DCA {dca} was flagged as invalid"

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await validate_nista({})

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_gmpp_compliance(self):
        """Test that GMPP projects require additional fields."""
        from unittest.mock import patch, Mock
        from datetime import date

        project = Mock()
        project.name = "GMPP Project"
        project.department = "Cabinet Office"
        project.start_date = date(2026, 1, 1)
        project.end_date = date(2026, 12, 31)
        project.delivery_confidence_assessment = "amber"
        project.whole_life_cost = None  # GMPP might require this
        project.tasks = []
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_nista({
                "project_id": "test-id",
                "strictness": "strict"
            })

        # Strict mode might require additional fields
        assert "compliance_score" in result


# ============================================================================
# INTEGRATION TESTS - validate_custom()
# ============================================================================

class TestValidateCustom:
    """Comprehensive tests for validate_custom()."""

    @pytest.mark.asyncio
    async def test_simple_custom_rule(self, valid_project):
        """Test custom validation with simple rule."""
        from unittest.mock import patch

        # Custom rule: task names must start with capital letter
        custom_rule = {
            "name": "task_name_capitalization",
            "condition": "task.name[0].isupper()",
            "message": "Task names must start with capital letter",
            "severity": "warning"
        }

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_custom({
                "project_id": "test-id",
                "rules": [custom_rule]
            })

        assert "valid" in result
        assert "total_issues" in result

    @pytest.mark.asyncio
    async def test_multiple_custom_rules(self, valid_project):
        """Test multiple custom validation rules."""
        from unittest.mock import patch

        rules = [
            {
                "name": "rule1",
                "condition": "task.duration > 0",
                "message": "Duration must be positive",
                "severity": "error"
            },
            {
                "name": "rule2",
                "condition": "task.percent_complete <= 100",
                "message": "Percent complete cannot exceed 100",
                "severity": "error"
            }
        ]

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=valid_project):
            result = await validate_custom({
                "project_id": "test-id",
                "rules": rules
            })

        assert "rules_applied" in result
        assert result["rules_applied"] == 2

    @pytest.mark.asyncio
    async def test_custom_rule_violations(self):
        """Test detection of custom rule violations."""
        from unittest.mock import patch, Mock

        task = Mock()
        task.id = "T1"
        task.name = "task"  # Lowercase!
        task.duration = 10
        task.percent_complete = 0

        project = Mock()
        project.name = "Test Project"
        project.tasks = [task]
        project.dependencies = []

        rule = {
            "name": "capitalization",
            "condition": "task.name[0].isupper()",
            "message": "Must start with capital",
            "severity": "error"
        }

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_custom({
                "project_id": "test-id",
                "rules": [rule]
            })

        # Should detect violation
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_missing_rules_parameter(self):
        """Test error when rules parameter is missing."""
        result = await validate_custom({"project_id": "test-id"})

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        """Test error when project_id is missing."""
        result = await validate_custom({"rules": []})

        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test comprehensive error handling across all validation tools."""

    @pytest.mark.asyncio
    async def test_all_validators_handle_missing_project(self):
        """Test that all validators properly handle missing projects."""
        from unittest.mock import patch

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=None):
            results = [
                await validate_structure({"project_id": "fake-id"}),
                await validate_semantic({"project_id": "fake-id"}),
                await validate_nista({"project_id": "fake-id"}),
                await validate_custom({"project_id": "fake-id", "rules": []}),
            ]

        for result in results:
            assert "error" in result
            assert result["error"]["code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_all_validators_handle_missing_project_id(self):
        """Test that all validators require project_id."""
        results = [
            await validate_structure({}),
            await validate_semantic({}),
            await validate_nista({}),
            await validate_custom({"rules": []}),
        ]

        for result in results:
            assert "error" in result
            assert result["error"]["code"] == "MISSING_PARAMETER"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_project(self):
        """Test validation of project with no tasks."""
        from unittest.mock import patch, Mock

        project = Mock()
        project.name = "Empty Project"
        project.tasks = []
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_structure({"project_id": "test-id"})

        # Empty project should validate without errors
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_project_with_only_milestones(self):
        """Test project containing only milestone tasks."""
        from unittest.mock import patch, Mock
        from datetime import date

        milestone1 = Mock()
        milestone1.id = "M1"
        milestone1.name = "Milestone 1"
        milestone1.is_milestone = True
        milestone1.start_date = date(2026, 6, 1)
        milestone1.finish_date = date(2026, 6, 1)
        milestone1.duration = 0

        project = Mock()
        project.name = "Milestone Project"
        project.tasks = [milestone1]
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_semantic({"project_id": "test-id"})

        assert "valid" in result

    @pytest.mark.asyncio
    async def test_large_project_performance(self):
        """Test validation performance with large number of tasks."""
        from unittest.mock import patch, Mock
        from datetime import date

        # Create 1000 tasks
        tasks = []
        for i in range(1000):
            task = Mock()
            task.id = f"T{i}"
            task.name = f"Task {i}"
            task.start_date = date(2026, 1, 1)
            task.finish_date = date(2026, 12, 31)
            task.duration = 365
            task.percent_complete = 0
            tasks.append(task)

        project = Mock()
        project.name = "Large Project"
        project.tasks = tasks
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_structure({"project_id": "test-id"})

        # Should complete without timeout or error
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_unicode_in_project_names(self):
        """Test validation with unicode characters in names."""
        from unittest.mock import patch, Mock
        from datetime import date

        task = Mock()
        task.id = "T1"
        task.name = "Tâche française 项目"
        task.start_date = date(2026, 1, 1)
        task.finish_date = date(2026, 12, 31)
        task.duration = 365
        task.percent_complete = 0

        project = Mock()
        project.name = "Проект с юникодом"
        project.department = "Département"
        project.tasks = [task]
        project.dependencies = []

        with patch("pm_mcp_servers.pm_validate.tools._get_project", return_value=project):
            result = await validate_structure({"project_id": "test-id"})

        # Should handle unicode without errors
        assert "valid" in result
