"""Basic test suite for PM-Validate MCP Server."""

import pytest
from pm_mcp_servers.pm_validate.tools import (
    Severity,
    ValidationIssue,
    validate_structure,
    validate_semantic,
    validate_nista,
    validate_custom,
)


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_create_error(self):
        issue = ValidationIssue(
            severity=Severity.ERROR,
            code="TEST_ERROR",
            message="Test error message",
        )
        assert issue.severity == Severity.ERROR
        assert issue.code == "TEST_ERROR"

    def test_create_warning(self):
        issue = ValidationIssue(
            severity=Severity.WARNING,
            code="TEST_WARNING",
            message="Test warning message",
        )
        assert issue.severity == Severity.WARNING

    def test_optional_fields(self):
        issue = ValidationIssue(
            severity=Severity.INFO,
            code="TEST",
            message="Test",
            location="task:T1",
            field="name",
            suggestion="Fix this",
        )
        assert issue.location == "task:T1"


class TestValidateStructure:
    """Tests for validate_structure()."""

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        result = await validate_structure({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_project_not_found(self):
        result = await validate_structure({"project_id": "nonexistent"})
        assert "error" in result
        assert result["error"]["code"] == "PROJECT_NOT_FOUND"


class TestValidateSemantic:
    """Tests for validate_semantic()."""

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        result = await validate_semantic({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


class TestValidateNISTA:
    """Tests for validate_nista()."""

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        result = await validate_nista({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"


class TestValidateCustom:
    """Tests for validate_custom()."""

    @pytest.mark.asyncio
    async def test_missing_rules_parameter(self):
        result = await validate_custom({"project_id": "test"})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.asyncio
    async def test_missing_project_id(self):
        result = await validate_custom({})
        assert "error" in result
        assert result["error"]["code"] == "MISSING_PARAMETER"
