"""Semantic validator for project business logic.

This module validates the semantic correctness of project data including:
- Circular dependency detection
- Schedule logic validation
- Cost consistency
- Progress consistency
- Risk assessment validation
"""

from typing import Optional
from collections import defaultdict, deque
from decimal import Decimal

from pm_data_tools.models import Project
from .base import ValidationIssue, ValidationResult, Severity


class SemanticValidator:
    """Validator for semantic business logic.

    Validates that project data follows PM best practices and logical
    constraints including dependency cycles, schedule consistency, and more.
    """

    def validate(self, project: Project) -> ValidationResult:
        """Validate a project for semantic correctness.

        Args:
            project: Project to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: list[ValidationIssue] = []

        # Run all semantic validation checks
        issues.extend(self._validate_dependency_cycles(project))
        issues.extend(self._validate_schedule_logic(project))
        issues.extend(self._validate_cost_consistency(project))
        issues.extend(self._validate_progress_consistency(project))
        issues.extend(self._validate_risk_assessments(project))

        return ValidationResult(issues=issues)

    def _validate_dependency_cycles(self, project: Project) -> list[ValidationIssue]:
        """Detect circular dependencies using topological sort.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        if not project.dependencies:
            return issues

        # Build adjacency list (successor -> predecessors)
        graph: dict = defaultdict(list)
        in_degree: dict = defaultdict(int)
        task_ids = {task.id for task in project.tasks}

        for dep in project.dependencies:
            # successor depends on predecessor
            graph[dep.predecessor_id].append(dep.successor_id)
            in_degree[dep.successor_id] += 1
            # Ensure all nodes are in the graph
            if dep.predecessor_id not in in_degree:
                in_degree[dep.predecessor_id] = 0

        # Topological sort using Kahn's algorithm
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        sorted_count = 0

        while queue:
            node = queue.popleft()
            sorted_count += 1

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If not all nodes were sorted, there's a cycle
        if sorted_count < len(in_degree):
            # Find nodes involved in cycle
            cycle_nodes = [node for node in in_degree if in_degree[node] > 0]

            # Get task names for context
            task_map = {task.id: task.name for task in project.tasks}
            cycle_tasks = [
                f"{task_map.get(node, 'Unknown')} (ID: {node})"
                for node in cycle_nodes
                if node in task_map
            ]

            issues.append(
                ValidationIssue(
                    code="CIRCULAR_DEPENDENCY",
                    message="Circular dependency detected in task dependencies",
                    severity=Severity.ERROR,
                    context=f"Tasks involved: {', '.join(cycle_tasks[:5])}{'...' if len(cycle_tasks) > 5 else ''}",
                    suggestion="Remove or modify dependencies to eliminate cycles",
                )
            )

        return issues

    def _validate_schedule_logic(self, project: Project) -> list[ValidationIssue]:
        """Validate schedule logic and consistency.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        # Check if tasks fall within project dates
        if project.start_date and project.finish_date:
            for task in project.tasks:
                if task.start_date:
                    if task.start_date < project.start_date:
                        issues.append(
                            ValidationIssue(
                                code="TASK_BEFORE_PROJECT_START",
                                message="Task starts before project start date",
                                severity=Severity.WARNING,
                                context=f"Task: {task.name} (ID: {task.id}), Task Start: {task.start_date}, Project Start: {project.start_date}",
                                suggestion="Adjust task or project start date",
                            )
                        )

                if task.finish_date:
                    if task.finish_date > project.finish_date:
                        issues.append(
                            ValidationIssue(
                                code="TASK_AFTER_PROJECT_FINISH",
                                message="Task finishes after project finish date",
                                severity=Severity.WARNING,
                                context=f"Task: {task.name} (ID: {task.id}), Task Finish: {task.finish_date}, Project Finish: {project.finish_date}",
                                suggestion="Adjust task or project finish date",
                            )
                        )

        return issues

    def _validate_cost_consistency(self, project: Project) -> list[ValidationIssue]:
        """Validate cost consistency and budget alignment.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        # Calculate total budgeted cost from tasks
        if project.tasks and project.budgeted_cost:
            task_total = sum(
                task.budgeted_cost.amount
                for task in project.tasks
                if task.budgeted_cost and task.budgeted_cost.currency == project.budgeted_cost.currency
            )

            # Check if task costs sum to project budget (with 1% tolerance)
            tolerance = abs(project.budgeted_cost.amount) * Decimal("0.01")
            difference = abs(task_total - project.budgeted_cost.amount)

            if difference > tolerance:
                issues.append(
                    ValidationIssue(
                        code="COST_MISMATCH",
                        message="Sum of task budgeted costs does not match project budget",
                        severity=Severity.WARNING,
                        context=f"Project Budget: {project.budgeted_cost}, Task Total: {task_total} {project.budgeted_cost.currency}, Difference: {difference}",
                        suggestion="Review task costs or adjust project budget",
                    )
                )

        # Check for tasks with actual cost exceeding budgeted cost
        for task in project.tasks:
            if task.budgeted_cost and task.actual_cost:
                if task.actual_cost.currency == task.budgeted_cost.currency:
                    if task.actual_cost.amount > task.budgeted_cost.amount:
                        overrun = task.actual_cost.amount - task.budgeted_cost.amount
                        issues.append(
                            ValidationIssue(
                                code="TASK_COST_OVERRUN",
                                message="Task actual cost exceeds budgeted cost",
                                severity=Severity.INFO,
                                context=f"Task: {task.name} (ID: {task.id}), Budgeted: {task.budgeted_cost}, Actual: {task.actual_cost}, Overrun: {overrun}",
                                suggestion="Review task progress and budget allocation",
                            )
                        )

        return issues

    def _validate_progress_consistency(self, project: Project) -> list[ValidationIssue]:
        """Validate progress tracking consistency.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        for task in project.tasks:
            # Check if actual work exceeds budgeted work
            if task.budgeted_work and task.actual_work:
                actual_hours = task.actual_work.to_hours()
                budgeted_hours = task.budgeted_work.to_hours()
                if actual_hours > budgeted_hours:
                    overrun = actual_hours - budgeted_hours
                    issues.append(
                        ValidationIssue(
                            code="WORK_OVERRUN",
                            message="Task actual work exceeds budgeted work",
                            severity=Severity.INFO,
                            context=f"Task: {task.name} (ID: {task.id}), Budgeted: {budgeted_hours}h, Actual: {actual_hours}h, Overrun: {overrun}h",
                            suggestion="Review task estimates or work tracking",
                        )
                    )

            # Check if actual start without actual finish for in-progress tasks
            if task.actual_start and not task.actual_finish:
                if task.percent_complete == 100.0:
                    # This is caught by structural validator, skip
                    pass
                elif task.percent_complete == 0.0:
                    issues.append(
                        ValidationIssue(
                            code="STARTED_TASK_NO_PROGRESS",
                            message="Task has actual start date but 0% progress",
                            severity=Severity.WARNING,
                            context=f"Task: {task.name} (ID: {task.id}), Actual Start: {task.actual_start}",
                            suggestion="Update task progress to reflect actual work",
                        )
                    )

        return issues

    def _validate_risk_assessments(self, project: Project) -> list[ValidationIssue]:
        """Validate risk assessment data.

        Args:
            project: Project to validate

        Returns:
            List of validation issues
        """
        issues: list[ValidationIssue] = []

        for risk in project.risks:
            # Check probability is in valid range (typically 1-5)
            if risk.probability is not None:
                if not (1 <= risk.probability <= 5):
                    issues.append(
                        ValidationIssue(
                            code="INVALID_RISK_PROBABILITY",
                            message="Risk probability outside valid range (1-5)",
                            severity=Severity.ERROR,
                            context=f"Risk: {risk.name} (ID: {risk.id}), Probability: {risk.probability}",
                            suggestion="Set probability to a value between 1 and 5",
                        )
                    )

            # Check impact is in valid range (typically 1-5)
            if risk.impact is not None:
                if not (1 <= risk.impact <= 5):
                    issues.append(
                        ValidationIssue(
                            code="INVALID_RISK_IMPACT",
                            message="Risk impact outside valid range (1-5)",
                            severity=Severity.ERROR,
                            context=f"Risk: {risk.name} (ID: {risk.id}), Impact: {risk.impact}",
                            suggestion="Set impact to a value between 1 and 5",
                        )
                    )

            # Check for risks without mitigation strategy (high severity)
            if risk.probability and risk.impact:
                risk_score = risk.probability * risk.impact
                if risk_score >= 15:  # High risk (3x5, 4x4, 5x3, 5x4, 5x5)
                    if not risk.mitigation or not risk.mitigation.strip():
                        issues.append(
                            ValidationIssue(
                                code="HIGH_RISK_NO_MITIGATION",
                                message="High-severity risk lacks mitigation strategy",
                                severity=Severity.WARNING,
                                context=f"Risk: {risk.name} (ID: {risk.id}), Score: {risk_score} (P:{risk.probability} × I:{risk.impact})",
                                suggestion="Define a mitigation strategy for high-severity risks",
                            )
                        )

        return issues
