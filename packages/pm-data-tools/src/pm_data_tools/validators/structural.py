"""Structural validator for project data integrity.

This module validates the structural integrity of project data including:
- Required fields present
- Valid references between entities
- Hierarchy consistency
- Date consistency
"""

from typing import Optional

from pm_data_tools.models import Project
from .base import ValidationIssue, ValidationResult, Severity


class StructuralValidator:
    """Validator for structural data integrity.

    Validates that project data has consistent structure including required
    fields, valid references, and logical consistency.
    """

    def validate(self, project: Project) -> ValidationResult:
        """Validate a project for structural integrity.

        Args:
            project: Project to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: list[ValidationIssue] = []

        # Run all validation checks
        issues.extend(self._validate_required_fields(project))
        issues.extend(self._validate_task_references(project))
        issues.extend(self._validate_resource_references(project))
        issues.extend(self._validate_assignment_references(project))
        issues.extend(self._validate_dependency_references(project))
        issues.extend(self._validate_date_consistency(project))

        return ValidationResult(issues=issues)

    def _validate_required_fields(self, project: Project) -> list[ValidationIssue]:
        """Validate required fields are present.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        # Project must have a name
        if not project.name or not project.name.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_PROJECT_NAME",
                    message="Project must have a name",
                    severity=Severity.ERROR,
                    suggestion="Set the project name to a non-empty string",
                )
            )

        # All tasks must have names
        for task in project.tasks:
            if not task.name or not task.name.strip():
                issues.append(
                    ValidationIssue(
                        code="MISSING_TASK_NAME",
                        message="Task must have a name",
                        severity=Severity.ERROR,
                        context=f"Task ID: {task.id}",
                        suggestion="Set the task name to a non-empty string",
                    )
                )

        # All resources must have names
        for resource in project.resources:
            if not resource.name or not resource.name.strip():
                issues.append(
                    ValidationIssue(
                        code="MISSING_RESOURCE_NAME",
                        message="Resource must have a name",
                        severity=Severity.ERROR,
                        context=f"Resource ID: {resource.id}",
                        suggestion="Set the resource name to a non-empty string",
                    )
                )

        return issues

    def _validate_task_references(self, project: Project) -> list[ValidationIssue]:
        """Validate task parent references are valid.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        task_ids = {task.id for task in project.tasks}

        for task in project.tasks:
            if task.parent_id and task.parent_id not in task_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_PARENT_TASK_REF",
                        message=f"Task references non-existent parent task",
                        severity=Severity.ERROR,
                        context=f"Task: {task.name} (ID: {task.id}), Parent ID: {task.parent_id}",
                        suggestion="Ensure the parent task exists in the project",
                    )
                )

            # Check for circular references (task can't be its own parent)
            if task.parent_id == task.id:
                issues.append(
                    ValidationIssue(
                        code="CIRCULAR_PARENT_REF",
                        message="Task cannot be its own parent",
                        severity=Severity.ERROR,
                        context=f"Task: {task.name} (ID: {task.id})",
                        suggestion="Set a different parent task or remove parent reference",
                    )
                )

        return issues

    def _validate_resource_references(self, project: Project) -> list[ValidationIssue]:
        """Validate resource references in calendars.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        calendar_ids = {cal.id for cal in project.calendars}

        for calendar in project.calendars:
            if calendar.base_calendar_id and calendar.base_calendar_id not in calendar_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_BASE_CALENDAR_REF",
                        message="Calendar references non-existent base calendar",
                        severity=Severity.ERROR,
                        context=f"Calendar: {calendar.name} (ID: {calendar.id}), Base Calendar ID: {calendar.base_calendar_id}",
                        suggestion="Ensure the base calendar exists in the project",
                    )
                )

        return issues

    def _validate_assignment_references(self, project: Project) -> list[ValidationIssue]:
        """Validate assignment references to tasks and resources.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        task_ids = {task.id for task in project.tasks}
        resource_ids = {resource.id for resource in project.resources}

        for assignment in project.assignments:
            # Check task reference
            if assignment.task_id not in task_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_ASSIGNMENT_TASK_REF",
                        message="Assignment references non-existent task",
                        severity=Severity.ERROR,
                        context=f"Assignment ID: {assignment.id}, Task ID: {assignment.task_id}",
                        suggestion="Ensure the task exists in the project",
                    )
                )

            # Check resource reference
            if assignment.resource_id not in resource_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_ASSIGNMENT_RESOURCE_REF",
                        message="Assignment references non-existent resource",
                        severity=Severity.ERROR,
                        context=f"Assignment ID: {assignment.id}, Resource ID: {assignment.resource_id}",
                        suggestion="Ensure the resource exists in the project",
                    )
                )

        return issues

    def _validate_dependency_references(self, project: Project) -> list[ValidationIssue]:
        """Validate dependency references to tasks.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        task_ids = {task.id for task in project.tasks}

        for dependency in project.dependencies:
            # Check predecessor reference
            if dependency.predecessor_id not in task_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_PREDECESSOR_REF",
                        message="Dependency references non-existent predecessor task",
                        severity=Severity.ERROR,
                        context=f"Dependency ID: {dependency.id}, Predecessor ID: {dependency.predecessor_id}",
                        suggestion="Ensure the predecessor task exists in the project",
                    )
                )

            # Check successor reference
            if dependency.successor_id not in task_ids:
                issues.append(
                    ValidationIssue(
                        code="INVALID_SUCCESSOR_REF",
                        message="Dependency references non-existent successor task",
                        severity=Severity.ERROR,
                        context=f"Dependency ID: {dependency.id}, Successor ID: {dependency.successor_id}",
                        suggestion="Ensure the successor task exists in the project",
                    )
                )

            # Check for self-dependency
            if dependency.predecessor_id == dependency.successor_id:
                issues.append(
                    ValidationIssue(
                        code="SELF_DEPENDENCY",
                        message="Task cannot depend on itself",
                        severity=Severity.ERROR,
                        context=f"Dependency ID: {dependency.id}, Task ID: {dependency.predecessor_id}",
                        suggestion="Remove the self-dependency or link to a different task",
                    )
                )

        return issues

    def _validate_date_consistency(self, project: Project) -> list[ValidationIssue]:
        """Validate date consistency within entities.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        # Validate project dates
        if project.start_date and project.finish_date:
            if project.finish_date < project.start_date:
                issues.append(
                    ValidationIssue(
                        code="INVALID_PROJECT_DATES",
                        message="Project finish date is before start date",
                        severity=Severity.ERROR,
                        context=f"Start: {project.start_date}, Finish: {project.finish_date}",
                        suggestion="Ensure finish date is on or after start date",
                    )
                )

        # Validate task dates
        for task in project.tasks:
            if task.start_date and task.finish_date:
                if task.finish_date < task.start_date:
                    issues.append(
                        ValidationIssue(
                            code="INVALID_TASK_DATES",
                            message="Task finish date is before start date",
                            severity=Severity.ERROR,
                            context=f"Task: {task.name} (ID: {task.id}), Start: {task.start_date}, Finish: {task.finish_date}",
                            suggestion="Ensure finish date is on or after start date",
                        )
                    )

            # Validate actual dates
            if task.actual_start and task.actual_finish:
                if task.actual_finish < task.actual_start:
                    issues.append(
                        ValidationIssue(
                            code="INVALID_ACTUAL_DATES",
                            message="Task actual finish date is before actual start date",
                            severity=Severity.ERROR,
                            context=f"Task: {task.name} (ID: {task.id}), Actual Start: {task.actual_start}, Actual Finish: {task.actual_finish}",
                            suggestion="Ensure actual finish date is on or after actual start date",
                        )
                    )

            # Validate progress consistency
            if task.percent_complete == 100 and not task.actual_finish:
                issues.append(
                    ValidationIssue(
                        code="COMPLETED_TASK_NO_ACTUAL_FINISH",
                        message="Task marked as 100% complete but has no actual finish date",
                        severity=Severity.WARNING,
                        context=f"Task: {task.name} (ID: {task.id})",
                        suggestion="Set the actual finish date for completed tasks",
                    )
                )

        return issues
