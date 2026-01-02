"""Tests for base validation classes."""

from pm_data_tools.validators.base import Severity, ValidationIssue, ValidationResult


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating validation issue with minimal fields."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.ERROR,
        )
        assert issue.code == "TEST_CODE"
        assert issue.message == "Test message"
        assert issue.severity == Severity.ERROR
        assert issue.context is None
        assert issue.suggestion is None

    def test_creation_complete(self) -> None:
        """Test creating validation issue with all fields."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.WARNING,
            context="Test context",
            suggestion="Test suggestion",
        )
        assert issue.code == "TEST_CODE"
        assert issue.message == "Test message"
        assert issue.severity == Severity.WARNING
        assert issue.context == "Test context"
        assert issue.suggestion == "Test suggestion"

    def test_str_minimal(self) -> None:
        """Test string representation with minimal fields."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.ERROR,
        )
        result = str(issue)
        assert "[ERROR]" in result
        assert "TEST_CODE:" in result
        assert "Test message" in result
        assert "Context:" not in result
        assert "→" not in result

    def test_str_with_context(self) -> None:
        """Test string representation with context."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.WARNING,
            context="Task ID: 123",
        )
        result = str(issue)
        assert "[WARNING]" in result
        assert "TEST_CODE:" in result
        assert "Test message" in result
        assert "(Context: Task ID: 123)" in result
        assert "→" not in result

    def test_str_with_suggestion(self) -> None:
        """Test string representation with suggestion."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.INFO,
            suggestion="Fix it like this",
        )
        result = str(issue)
        assert "[INFO]" in result
        assert "TEST_CODE:" in result
        assert "Test message" in result
        assert "Context:" not in result
        assert "→ Fix it like this" in result

    def test_str_complete(self) -> None:
        """Test string representation with all fields."""
        issue = ValidationIssue(
            code="TEST_CODE",
            message="Test message",
            severity=Severity.ERROR,
            context="Task ID: 123",
            suggestion="Fix it like this",
        )
        result = str(issue)
        assert "[ERROR]" in result
        assert "TEST_CODE:" in result
        assert "Test message" in result
        assert "(Context: Task ID: 123)" in result
        assert "→ Fix it like this" in result


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_creation_empty(self) -> None:
        """Test creating validation result with no issues."""
        result = ValidationResult(issues=[])
        assert result.issues == []
        assert result.errors_count == 0
        assert result.warnings_count == 0
        assert result.info_count == 0
        assert result.is_valid

    def test_creation_with_issues(self) -> None:
        """Test creating validation result with issues."""
        issues = [
            ValidationIssue(
                code="ERROR1", message="Error 1", severity=Severity.ERROR
            ),
            ValidationIssue(
                code="WARNING1", message="Warning 1", severity=Severity.WARNING
            ),
            ValidationIssue(
                code="INFO1", message="Info 1", severity=Severity.INFO
            ),
        ]
        result = ValidationResult(issues=issues)
        assert len(result.issues) == 3
        assert result.errors_count == 1
        assert result.warnings_count == 1
        assert result.info_count == 1
        assert not result.is_valid

    def test_is_valid_with_errors(self) -> None:
        """Test is_valid returns False when errors present."""
        issues = [
            ValidationIssue(
                code="ERROR1", message="Error 1", severity=Severity.ERROR
            ),
        ]
        result = ValidationResult(issues=issues)
        assert not result.is_valid

    def test_is_valid_with_warnings_only(self) -> None:
        """Test is_valid returns True when only warnings present."""
        issues = [
            ValidationIssue(
                code="WARNING1", message="Warning 1", severity=Severity.WARNING
            ),
        ]
        result = ValidationResult(issues=issues)
        assert result.is_valid

    def test_counts(self) -> None:
        """Test severity counts."""
        issues = [
            ValidationIssue(code="E1", message="E1", severity=Severity.ERROR),
            ValidationIssue(code="E2", message="E2", severity=Severity.ERROR),
            ValidationIssue(code="W1", message="W1", severity=Severity.WARNING),
            ValidationIssue(code="W2", message="W2", severity=Severity.WARNING),
            ValidationIssue(code="W3", message="W3", severity=Severity.WARNING),
            ValidationIssue(code="I1", message="I1", severity=Severity.INFO),
        ]
        result = ValidationResult(issues=issues)
        assert result.errors_count == 2
        assert result.warnings_count == 3
        assert result.info_count == 1

    def test_str_no_issues(self) -> None:
        """Test string representation with no issues."""
        result = ValidationResult(issues=[])
        result_str = str(result)
        assert "Validation passed: No issues found" in result_str

    def test_str_with_errors(self) -> None:
        """Test string representation with errors."""
        issues = [
            ValidationIssue(code="E1", message="Error 1", severity=Severity.ERROR),
            ValidationIssue(
                code="W1", message="Warning 1", severity=Severity.WARNING
            ),
        ]
        result = ValidationResult(issues=issues)
        result_str = str(result)
        assert "Validation failed:" in result_str
        assert "Errors: 1" in result_str
        assert "Warnings: 1" in result_str
        assert "Info: 0" in result_str
        assert "Issues:" in result_str
        assert "E1" in result_str
        assert "W1" in result_str

    def test_str_with_warnings_only(self) -> None:
        """Test string representation with warnings only."""
        issues = [
            ValidationIssue(
                code="W1", message="Warning 1", severity=Severity.WARNING
            ),
            ValidationIssue(
                code="W2", message="Warning 2", severity=Severity.WARNING
            ),
        ]
        result = ValidationResult(issues=issues)
        result_str = str(result)
        assert "Validation passed with warnings:" in result_str
        assert "Errors: 0" in result_str
        assert "Warnings: 2" in result_str
        assert "Info: 0" in result_str
        assert "Issues:" in result_str
        assert "W1" in result_str
        assert "W2" in result_str

    def test_str_with_info_only(self) -> None:
        """Test string representation with info only."""
        issues = [
            ValidationIssue(code="I1", message="Info 1", severity=Severity.INFO),
        ]
        result = ValidationResult(issues=issues)
        result_str = str(result)
        assert "Validation passed with warnings:" in result_str
        assert "Errors: 0" in result_str
        assert "Warnings: 0" in result_str
        assert "Info: 1" in result_str
        assert "Issues:" in result_str
        assert "I1" in result_str
