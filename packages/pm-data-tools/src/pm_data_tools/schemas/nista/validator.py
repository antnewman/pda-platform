"""Validator for NISTA Programme and Project Data Standard compliance."""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from ...models import Project


class StrictnessLevel(Enum):
    """NISTA validation strictness levels."""

    LENIENT = "lenient"  # Only critical GMPP fields (backward compatible)
    STANDARD = "standard"  # All required fields, warn on recommended
    STRICT = "strict"  # Treat recommended as required


@dataclass
class ValidationIssue:
    """Single validation issue."""

    field: str
    message: str
    severity: str  # "error" or "warning"
    path: str = ""  # JSON path to field


@dataclass
class ValidationResult:
    """NISTA validation result."""

    compliant: bool
    compliance_score: float  # 0-100
    missing_required_fields: list[str] = field(default_factory=list)
    missing_recommended_fields: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    strictness: str = "standard"

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return len([i for i in self.issues if i.severity == "error"])

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return len([i for i in self.issues if i.severity == "warning"])

    def __str__(self) -> str:
        """String representation."""
        status = "COMPLIANT" if self.compliant else "NON-COMPLIANT"
        return (
            f"NISTA Validation ({self.strictness}): {status}\n"
            f"Compliance Score: {self.compliance_score:.1f}%\n"
            f"Errors: {self.error_count}, Warnings: {self.warning_count}"
        )


class NISTAValidator:
    """Validator for NISTA Programme and Project Data Standard.

    Validates project data against NISTA requirements at three strictness levels:

    - **Lenient**: Only check critical GMPP fields (backward compatible)
    - **Standard**: Check all required fields, warn on recommended
    - **Strict**: Treat recommended as required

    Compliance scoring:
    - 100% = All required and recommended fields present
    - 0% = No required fields present
    - Partial scores based on % of required fields present
    """

    # Field groups by strictness level
    LENIENT_REQUIRED = [
        "project_id",
        "project_name",
        "department",
        "category",
        "delivery_confidence_assessment_ipa",
        "start_date_baseline",
        "end_date_baseline",
        "whole_life_cost_baseline",
    ]

    STANDARD_REQUIRED = LENIENT_REQUIRED + [
        "delivery_confidence_assessment_sro",
        "senior_responsible_owner",
        "benefits_baseline",
    ]

    RECOMMENDED = [
        "description",
        "milestones",
        "risks_summary",
        "issues_summary",
    ]

    STRICT_REQUIRED = STANDARD_REQUIRED + RECOMMENDED

    def __init__(
        self,
        version: str = "1.0",
        strictness: StrictnessLevel = StrictnessLevel.STANDARD,
        schema_path: Optional[Path] = None,
    ):
        """Initialize NISTA validator.

        Args:
            version: NISTA schema version (default: "1.0")
            strictness: Validation strictness level
            schema_path: Optional path to JSON schema file
                        (defaults to bundled schema)
        """
        self.version = version
        self.strictness = strictness
        self.schema_path = schema_path or self._get_default_schema_path()
        self.schema = self._load_schema()

    def _get_default_schema_path(self) -> Path:
        """Get default schema path.

        Returns:
            Path to bundled NISTA schema
        """
        # Get path relative to this file
        current_dir = Path(__file__).parent
        return current_dir / "v1.0" / "project.schema.json"

    def _load_schema(self) -> Optional[dict[str, Any]]:
        """Load JSON schema.

        Returns:
            Loaded schema dictionary or None if not available
        """
        if not self.schema_path.exists():
            return None

        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate NISTA data dictionary.

        Args:
            data: NISTA project data dictionary

        Returns:
            ValidationResult with compliance status and issues
        """
        issues = []
        missing_required = []
        missing_recommended = []

        # Determine required fields based on strictness
        if self.strictness == StrictnessLevel.LENIENT:
            required_fields = self.LENIENT_REQUIRED
            recommended_fields = []
        elif self.strictness == StrictnessLevel.STANDARD:
            required_fields = self.STANDARD_REQUIRED
            recommended_fields = self.RECOMMENDED
        else:  # STRICT
            required_fields = self.STRICT_REQUIRED
            recommended_fields = []

        # Check required fields
        for field_name in required_fields:
            if field_name not in data or not data[field_name]:
                missing_required.append(field_name)
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        message=f"Required field '{field_name}' is missing or empty",
                        severity="error",
                        path=f"$.{field_name}",
                    )
                )

        # Check recommended fields (warnings only)
        for field_name in recommended_fields:
            if field_name not in data or not data[field_name]:
                missing_recommended.append(field_name)
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        message=f"Recommended field '{field_name}' is missing or empty",
                        severity="warning",
                        path=f"$.{field_name}",
                    )
                )

        # JSON Schema validation (if available and schema loaded)
        if JSONSCHEMA_AVAILABLE and self.schema:
            try:
                validator = Draft7Validator(self.schema)
                for error in validator.iter_errors(data):
                    issues.append(
                        ValidationIssue(
                            field=error.json_path or "",
                            message=error.message,
                            severity="error",
                            path=error.json_path or "",
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        field="schema",
                        message=f"Schema validation error: {str(e)}",
                        severity="warning",
                    )
                )

        # Calculate compliance score
        total_required = len(required_fields)
        present_required = total_required - len(missing_required)
        compliance_score = (
            (present_required / total_required * 100) if total_required > 0 else 0
        )

        # Determine compliance (no errors = compliant)
        compliant = len(missing_required) == 0

        return ValidationResult(
            compliant=compliant,
            compliance_score=compliance_score,
            missing_required_fields=missing_required,
            missing_recommended_fields=missing_recommended,
            issues=issues,
            strictness=self.strictness.value,
        )

    def validate_project(self, project: Project) -> ValidationResult:
        """Validate a canonical Project model against NISTA requirements.

        Args:
            project: Canonical Project model

        Returns:
            ValidationResult with compliance status and issues
        """
        # Convert Project to NISTA-like dictionary
        data = {
            "project_id": str(project.id),
            "project_name": project.name,
            "department": project.department,
            "category": project.category,
            "description": project.description,
            "delivery_confidence_assessment_ipa": (
                project.delivery_confidence.value
                if project.delivery_confidence
                else None
            ),
            "senior_responsible_owner": project.senior_responsible_owner,
            "start_date_baseline": (
                project.start_date.isoformat() if project.start_date else None
            ),
            "end_date_baseline": (
                project.finish_date.isoformat() if project.finish_date else None
            ),
            "whole_life_cost_baseline": (
                float(project.whole_life_cost.amount / 1_000_000)
                if project.whole_life_cost
                else None
            ),
            "benefits_baseline": (
                float(project.monetised_benefits.amount / 1_000_000)
                if project.monetised_benefits
                else None
            ),
            "milestones": [
                {"name": t.name, "baseline_date": t.start_date}
                for t in project.tasks
                if t.is_milestone
            ],
            "risks_summary": (
                {
                    "total_count": len(project.risks),
                    "top_risks": [
                        {"description": r.name, "severity": "Medium"}
                        for r in project.risks[:5]
                    ],
                }
                if project.risks
                else None
            ),
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        return self.validate(data)

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate NISTA JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            ValidationResult with compliance status and issues

        Raises:
            ValueError: If file is not JSON format
        """
        if not file_path.suffix.lower() == ".json":
            raise ValueError(
                f"Only JSON files can be validated directly. "
                f"For CSV/Excel, parse first then validate the Project."
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return self.validate(data)
