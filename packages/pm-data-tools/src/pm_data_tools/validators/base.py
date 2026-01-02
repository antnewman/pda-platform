"""Base validation classes and types.

This module defines the core validation framework including severity levels,
validation issues, and validation results.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Severity level for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue found during validation.

    Attributes:
        code: Machine-readable issue code (e.g., MISSING_PROJECT_NAME)
        message: Human-readable description of the issue
        severity: Severity level (ERROR, WARNING, INFO)
        context: Optional context information (e.g., task ID, resource name)
        suggestion: Optional suggestion for fixing the issue
    """

    code: str
    message: str
    severity: Severity
    context: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """String representation."""
        parts = [f"[{self.severity.value.upper()}]", f"{self.code}:", self.message]
        if self.context:
            parts.append(f"(Context: {self.context})")
        if self.suggestion:
            parts.append(f"→ {self.suggestion}")
        return " ".join(parts)


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a project.

    Attributes:
        issues: List of validation issues found
        errors_count: Number of ERROR-level issues
        warnings_count: Number of WARNING-level issues
        info_count: Number of INFO-level issues
    """

    issues: list[ValidationIssue]

    @property
    def errors_count(self) -> int:
        """Count of ERROR-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.ERROR)

    @property
    def warnings_count(self) -> int:
        """Count of WARNING-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of INFO-level issues."""
        return sum(1 for issue in self.issues if issue.severity == Severity.INFO)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Returns:
            True if there are no ERROR-level issues
        """
        return self.errors_count == 0

    def __str__(self) -> str:
        """String representation."""
        if not self.issues:
            return "Validation passed: No issues found"

        lines = [
            f"Validation {'failed' if not self.is_valid else 'passed with warnings'}:",
            f"  Errors: {self.errors_count}",
            f"  Warnings: {self.warnings_count}",
            f"  Info: {self.info_count}",
            "\nIssues:",
        ]

        for issue in self.issues:
            lines.append(f"  {issue}")

        return "\n".join(lines)
