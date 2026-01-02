"""NISTA Migration Assistant for assessing and planning compliance migrations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..models import Project
from ..schemas.nista import NISTAValidator, StrictnessLevel, ValidationResult


class EffortLevel(Enum):
    """Migration effort estimation."""

    LOW = "low"  # < 1 day
    MEDIUM = "medium"  # 1-5 days
    HIGH = "high"  # > 5 days


@dataclass
class MigrationGap:
    """Single migration gap."""

    field_name: str
    description: str
    current_value: Optional[str]
    required: bool
    mapping_suggestion: Optional[str] = None
    effort: EffortLevel = EffortLevel.MEDIUM


@dataclass
class MigrationReport:
    """NISTA migration assessment report."""

    current_compliance_score: float  # 0-100
    target_compliance_score: float  # 0-100
    gaps: list[MigrationGap] = field(default_factory=list)
    mapping_suggestions: dict[str, str] = field(default_factory=dict)
    estimated_effort: EffortLevel = EffortLevel.MEDIUM
    validation_result: Optional[ValidationResult] = None

    @property
    def required_gaps_count(self) -> int:
        """Count of required field gaps."""
        return len([g for g in self.gaps if g.required])

    @property
    def recommended_gaps_count(self) -> int:
        """Count of recommended field gaps."""
        return len([g for g in self.gaps if not g.required])

    def __str__(self) -> str:
        """String representation."""
        return (
            f"NISTA Migration Report\n"
            f"Current Compliance: {self.current_compliance_score:.1f}%\n"
            f"Target Compliance: {self.target_compliance_score:.1f}%\n"
            f"Required Gaps: {self.required_gaps_count}\n"
            f"Recommended Gaps: {self.recommended_gaps_count}\n"
            f"Estimated Effort: {self.estimated_effort.value}"
        )


class NISTAMigrationAssistant:
    """Assistant for NISTA compliance migration.

    Helps organizations migrate from current formats to NISTA compliance by:
    - Assessing current compliance score
    - Identifying missing fields (gaps)
    - Suggesting field mappings from source data
    - Estimating migration effort

    Usage:
        assistant = NISTAMigrationAssistant()
        report = assistant.assess(project)
        print(report.gaps)
        print(report.mapping_suggestions)
    """

    # Field mapping suggestions from common PM tools
    COMMON_MAPPINGS = {
        "project_id": [
            "id",
            "projectId",
            "project_code",
            "code",
            "uid",
            "uniqueId",
        ],
        "project_name": [
            "name",
            "title",
            "projectName",
            "project_title",
        ],
        "description": [
            "description",
            "desc",
            "summary",
            "overview",
            "objectives",
        ],
        "department": [
            "department",
            "dept",
            "owner",
            "organization",
            "organisation",
            "team",
        ],
        "category": [
            "category",
            "type",
            "project_type",
            "projectType",
            "classification",
        ],
        "senior_responsible_owner": [
            "sro",
            "owner",
            "sponsor",
            "project_sponsor",
            "responsible_owner",
            "manager",
            "project_manager",
        ],
        "start_date_baseline": [
            "start_date",
            "startDate",
            "planned_start",
            "baseline_start",
            "planned_start_date",
        ],
        "end_date_baseline": [
            "end_date",
            "endDate",
            "finish_date",
            "planned_end",
            "baseline_end",
            "planned_finish_date",
        ],
        "whole_life_cost_baseline": [
            "budget",
            "total_cost",
            "cost",
            "whole_life_cost",
            "wlc",
            "baseline_cost",
            "planned_cost",
        ],
        "benefits_baseline": [
            "benefits",
            "expected_benefits",
            "value",
            "roi",
            "business_value",
        ],
    }

    def __init__(
        self,
        target_strictness: StrictnessLevel = StrictnessLevel.STANDARD,
    ):
        """Initialize migration assistant.

        Args:
            target_strictness: Target NISTA compliance level
        """
        self.target_strictness = target_strictness
        self.validator = NISTAValidator(strictness=target_strictness)

    def assess(self, project: Project) -> MigrationReport:
        """Assess project for NISTA compliance and identify migration gaps.

        Args:
            project: Canonical Project model

        Returns:
            MigrationReport with gaps and recommendations
        """
        # Validate current state
        validation_result = self.validator.validate_project(project)

        # Identify gaps
        gaps = self._identify_gaps(project, validation_result)

        # Generate mapping suggestions
        mapping_suggestions = self._generate_mapping_suggestions(gaps)

        # Estimate effort
        effort = self._estimate_effort(gaps)

        # Calculate target score (assume 100% after migration)
        target_score = 100.0

        return MigrationReport(
            current_compliance_score=validation_result.compliance_score,
            target_compliance_score=target_score,
            gaps=gaps,
            mapping_suggestions=mapping_suggestions,
            estimated_effort=effort,
            validation_result=validation_result,
        )

    def _identify_gaps(
        self, project: Project, validation_result: ValidationResult
    ) -> list[MigrationGap]:
        """Identify specific migration gaps.

        Args:
            project: Project model
            validation_result: Validation result

        Returns:
            List of MigrationGap objects
        """
        gaps = []

        # Check each missing required field
        for field_name in validation_result.missing_required_fields:
            current_value = self._get_project_field_value(project, field_name)
            gap = MigrationGap(
                field_name=field_name,
                description=f"Required field '{field_name}' is missing",
                current_value=current_value,
                required=True,
                mapping_suggestion=self._suggest_mapping(project, field_name),
                effort=self._estimate_field_effort(field_name, current_value),
            )
            gaps.append(gap)

        # Check each missing recommended field
        for field_name in validation_result.missing_recommended_fields:
            current_value = self._get_project_field_value(project, field_name)
            gap = MigrationGap(
                field_name=field_name,
                description=f"Recommended field '{field_name}' is missing",
                current_value=current_value,
                required=False,
                mapping_suggestion=self._suggest_mapping(project, field_name),
                effort=self._estimate_field_effort(field_name, current_value),
            )
            gaps.append(gap)

        return gaps

    def _get_project_field_value(
        self, project: Project, field_name: str
    ) -> Optional[str]:
        """Get current value of a field from Project.

        Args:
            project: Project model
            field_name: NISTA field name

        Returns:
            Current value as string or None
        """
        # Map NISTA field names to Project attributes
        field_mapping = {
            "project_id": lambda p: str(p.id) if p.id else None,
            "project_name": lambda p: p.name,
            "department": lambda p: p.department,
            "category": lambda p: p.category,
            "description": lambda p: p.description,
            "senior_responsible_owner": lambda p: p.senior_responsible_owner,
            "start_date_baseline": lambda p: (
                str(p.start_date) if p.start_date else None
            ),
            "end_date_baseline": lambda p: (
                str(p.finish_date) if p.finish_date else None
            ),
            "whole_life_cost_baseline": lambda p: (
                str(p.whole_life_cost) if p.whole_life_cost else None
            ),
            "benefits_baseline": lambda p: (
                str(p.monetised_benefits) if p.monetised_benefits else None
            ),
        }

        getter = field_mapping.get(field_name)
        if getter:
            return getter(project)

        return None

    def _suggest_mapping(self, project: Project, field_name: str) -> Optional[str]:
        """Suggest field mapping from source data.

        Args:
            project: Project model
            field_name: NISTA field name

        Returns:
            Mapping suggestion string or None
        """
        # Check custom fields for potential mappings
        if project.custom_fields:
            possible_sources = self.COMMON_MAPPINGS.get(field_name, [])
            for cf in project.custom_fields:
                if cf.name.lower() in [s.lower() for s in possible_sources]:
                    return f"Map from custom field: {cf.name}"

        # Generic suggestions based on field type
        if field_name == "department":
            return "Extract from project metadata or organization structure"
        elif field_name == "category":
            return "Classify as: Infrastructure, Transformation, Military, or ICT"
        elif field_name == "senior_responsible_owner":
            if project.project_manager:
                return f"Use project_manager: {project.project_manager}"
            return "Assign from project governance documentation"
        elif field_name == "delivery_confidence_assessment_ipa":
            return "Assess using GMPP DCA criteria (Green/Amber/Red)"
        elif field_name == "milestones":
            milestone_count = len([t for t in project.tasks if t.is_milestone])
            if milestone_count > 0:
                return f"Extract {milestone_count} existing milestones from tasks"
            return "Define key project milestones (start, major gates, end)"
        elif field_name == "risks_summary":
            if project.risks:
                return f"Summarize {len(project.risks)} existing risks"
            return "Create risk register with top 3-5 risks"

        return None

    def _generate_mapping_suggestions(
        self, gaps: list[MigrationGap]
    ) -> dict[str, str]:
        """Generate field mapping suggestions.

        Args:
            gaps: List of migration gaps

        Returns:
            Dictionary of field_name -> suggestion
        """
        suggestions = {}
        for gap in gaps:
            if gap.mapping_suggestion:
                suggestions[gap.field_name] = gap.mapping_suggestion
        return suggestions

    def _estimate_field_effort(
        self, field_name: str, current_value: Optional[str]
    ) -> EffortLevel:
        """Estimate effort to populate a field.

        Args:
            field_name: NISTA field name
            current_value: Current value (if any)

        Returns:
            EffortLevel estimation
        """
        # If field already has a value, effort is low (just format conversion)
        if current_value:
            return EffortLevel.LOW

        # Complex fields requiring new data
        high_effort_fields = [
            "delivery_confidence_assessment_ipa",
            "delivery_confidence_assessment_sro",
            "risks_summary",
            "issues_summary",
            "benefits_baseline",
        ]

        if field_name in high_effort_fields:
            return EffortLevel.HIGH

        # Simple administrative fields
        low_effort_fields = [
            "project_id",
            "department",
            "category",
        ]

        if field_name in low_effort_fields:
            return EffortLevel.LOW

        # Default to medium
        return EffortLevel.MEDIUM

    def _estimate_effort(self, gaps: list[MigrationGap]) -> EffortLevel:
        """Estimate overall migration effort.

        Args:
            gaps: List of migration gaps

        Returns:
            Overall EffortLevel
        """
        if not gaps:
            return EffortLevel.LOW

        # Count by effort level
        high_count = len([g for g in gaps if g.effort == EffortLevel.HIGH])
        medium_count = len([g for g in gaps if g.effort == EffortLevel.MEDIUM])

        # Decision logic
        if high_count >= 3:
            return EffortLevel.HIGH
        elif high_count >= 1 or medium_count >= 5:
            return EffortLevel.MEDIUM
        else:
            return EffortLevel.LOW
