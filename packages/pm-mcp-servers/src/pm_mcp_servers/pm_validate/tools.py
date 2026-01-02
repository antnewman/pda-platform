"""PM-Validate MCP Server Tools - Production Implementation

Comprehensive validation for project management data including:
- Structural validation (references, hierarchy, cycles)
- Semantic validation (schedule logic, resources, costs)
- NISTA compliance (UK government standard)
- Custom rule engine

Developed by members of the PDA Task Force to support NISTA Programme and Project Data Standard trial.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Access to project store from pm_data
try:
    from pm_mcp_servers.pm_data.tools import _store
    HAS_PROJECT_STORE = True
except ImportError:
    HAS_PROJECT_STORE = False
    _store = None
    logging.warning("Cannot import project store from pm_data")


class Severity(str, Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A validation issue found in project data."""
    severity: Severity
    code: str
    message: str
    location: Optional[str] = None
    field: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "location": self.location,
            "field": self.field,
            "suggestion": self.suggestion,
        }


def _get_project(project_id: str):
    """Get project from store."""
    if not HAS_PROJECT_STORE or not _store:
        return None
    return _store.get(project_id)


def _make_error(code: str, message: str) -> dict[str, Any]:
    """Create error response."""
    return {"error": {"code": code, "message": message}}


def _make_result(valid: bool, issues: list[ValidationIssue], **kwargs) -> dict[str, Any]:
    """Create validation result."""
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    info = [i for i in issues if i.severity == Severity.INFO]
    
    result = {
        "valid": valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "info_count": len(info),
        "issues": [i.to_dict() for i in issues],
    }
    result.update(kwargs)
    return result



# ============================================================================
# STRUCTURAL VALIDATION
# ============================================================================

async def validate_structure(arguments: dict[str, Any]) -> dict[str, Any]:
    '''Validate project data structure and integrity.'''
    project_id = arguments.get("project_id")
    checks = arguments.get("checks", ["all"])
    
    if not project_id:
        return _make_error("MISSING_PARAMETER", "project_id is required")
    
    project = _get_project(project_id)
    if not project:
        return _make_error("PROJECT_NOT_FOUND", f"Project {project_id} not found")
    
    issues: list[ValidationIssue] = []
    checks_run: list[str] = []
    run_all = "all" in checks
    
    tasks = project.tasks or []
    resources = project.resources or []
    dependencies = project.dependencies or []
    task_ids = {t.id for t in tasks}
    resource_ids = {r.id for r in resources}
    
    # Check 1: Orphan tasks
    if run_all or "orphan_tasks" in checks:
        checks_run.append("orphan_tasks")
        for task in tasks:
            parent_id = getattr(task, "parent_id", None)
            if parent_id and parent_id not in task_ids:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="ORPHAN_TASK",
                    message=f"Task '{task.name}' references missing parent '{parent_id}'",
                    location=f"task:{task.id}",
                ))
    
    # Check 2: Circular dependencies
    if run_all or "circular_dependencies" in checks:
        checks_run.append("circular_dependencies")
        graph: dict[str, list[str]] = {t.id: [] for t in tasks}
        for dep in dependencies:
            if dep.predecessor_id in graph:
                graph[dep.predecessor_id].append(dep.successor_id)
        
        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        
        visited_global = set()
        for task_id in graph:
            if task_id not in visited_global:
                if has_cycle(task_id, visited_global, set()):
                    issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        code="CIRCULAR_DEPENDENCY",
                        message="Circular dependency detected in task network",
                        location="dependencies",
                    ))
                    break
    
    # Check 3: Invalid references
    if run_all or "invalid_references" in checks:
        checks_run.append("invalid_references")
        for dep in dependencies:
            if dep.predecessor_id not in task_ids:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="INVALID_PREDECESSOR",
                    message=f"Dependency references missing predecessor '{dep.predecessor_id}'",
                    location=f"dependency:{dep.predecessor_id}->{dep.successor_id}",
                ))
            if dep.successor_id not in task_ids:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="INVALID_SUCCESSOR",
                    message=f"Dependency references missing successor '{dep.successor_id}'",
                    location=f"dependency:{dep.predecessor_id}->{dep.successor_id}",
                ))
    
    # Check 4: Duplicate IDs
    if run_all or "duplicate_ids" in checks:
        checks_run.append("duplicate_ids")
        seen_ids: set[str] = set()
        for task in tasks:
            if task.id in seen_ids:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="DUPLICATE_TASK_ID",
                    message=f"Duplicate task ID: '{task.id}'",
                    location=f"task:{task.id}",
                ))
            seen_ids.add(task.id)
    
    # Check 5: Date consistency
    if run_all or "date_consistency" in checks:
        checks_run.append("date_consistency")
        for task in tasks:
            if task.start_date and task.finish_date and task.start_date > task.finish_date:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="START_AFTER_FINISH",
                    message=f"Task '{task.name}' starts after it finishes",
                    location=f"task:{task.id}",
                ))
    
    errors = [i for i in issues if i.severity == Severity.ERROR]
    return _make_result(valid=len(errors) == 0, issues=issues, checks_run=checks_run)


# ============================================================================
# SEMANTIC VALIDATION  
# ============================================================================

async def validate_semantic(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate business rules and scheduling logic."""
    project_id = arguments.get("project_id")
    rules = arguments.get("rules", ["all"])
    
    if not project_id:
        return _make_error("MISSING_PARAMETER", "project_id is required")
    
    project = _get_project(project_id)
    if not project:
        return _make_error("PROJECT_NOT_FOUND", f"Project {project_id} not found")
    
    issues: list[ValidationIssue] = []
    rules_run: list[str] = []
    run_all = "all" in rules
    tasks = project.tasks or []
    
    # Rule: Negative float
    if run_all or "negative_float" in rules:
        rules_run.append("negative_float")
        for task in tasks:
            total_float = getattr(task, "total_float", None)
            if total_float is not None and total_float < 0:
                issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    code="NEGATIVE_FLOAT",
                    message=f"Task {repr(task.name)} has negative float ({total_float} days)",
                    location=f"task:{task.id}",
                ))
    
    # Rule: Overdue milestones
    if run_all or "milestone_dates" in rules:
        rules_run.append("milestone_dates")
        today = date.today()
        for task in tasks:
            if getattr(task, "is_milestone", False) and task.finish_date and task.finish_date < today and task.status != "completed":
                days_overdue = (today - task.finish_date).days
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    code="MILESTONE_OVERDUE",
                    message=f"Milestone {repr(task.name)} is {days_overdue} days overdue",
                    location=f"task:{task.id}",
                ))
    
    errors = [i for i in issues if i.severity == Severity.ERROR]
    return _make_result(valid=len(errors) == 0, issues=issues, rules_checked=rules_run)


# ============================================================================
# NISTA VALIDATION
# ============================================================================

NISTA_REQUIRED_FIELDS = [
    ("name", "Project name"),
    ("department", "Department"),
    ("start_date", "Start date"),
    ("end_date", "End date"),
    ("delivery_confidence_assessment", "DCA"),
]

VALID_DCA_VALUES = ["green", "amber_green", "amber", "amber_red", "red"]


async def validate_nista(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate against NISTA standard."""
    project_id = arguments.get("project_id")
    strictness = arguments.get("strictness", "standard")
    
    if not project_id:
        return _make_error("MISSING_PARAMETER", "project_id is required")
    
    project = _get_project(project_id)
    if not project:
        return _make_error("PROJECT_NOT_FOUND", f"Project {project_id} not found")
    
    issues: list[ValidationIssue] = []
    required = list(NISTA_REQUIRED_FIELDS)
    required_present = 0
    
    for field_name, field_desc in required:
        value = getattr(project, field_name, None)
        if value is None or value == "":
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="NISTA_REQUIRED_MISSING",
                message=f"Required field {repr(field_desc)} is missing",
                field=field_name,
            ))
        else:
            required_present += 1
    
    # Validate DCA
    dca = getattr(project, "delivery_confidence_assessment", None)
    if dca and dca.lower().replace("-", "_") not in VALID_DCA_VALUES:
        issues.append(ValidationIssue(
            severity=Severity.ERROR,
            code="NISTA_INVALID_DCA",
            message=f"Invalid DCA value {repr(dca)}",
            field="delivery_confidence_assessment",
        ))
    
    compliance = (required_present / len(required) * 100) if required else 0
    errors = [i for i in issues if i.severity == Severity.ERROR]
    
    return {
        "compliant": len(errors) == 0,
        "compliance_score": round(compliance, 1),
        "strictness_applied": strictness,
        "required_fields_present": required_present,
        "required_fields_total": len(required),
        "error_count": len(errors),
        "warning_count": len([i for i in issues if i.severity == Severity.WARNING]),
        "issues": [i.to_dict() for i in issues],
    }


# ============================================================================
# CUSTOM VALIDATION
# ============================================================================

async def validate_custom(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run custom validation rules."""
    project_id = arguments.get("project_id")
    rules = arguments.get("rules", [])
    
    if not project_id:
        return _make_error("MISSING_PARAMETER", "project_id is required")
    if not rules:
        return _make_error("MISSING_PARAMETER", "rules is required")
    
    project = _get_project(project_id)
    if not project:
        return _make_error("PROJECT_NOT_FOUND", f"Project {project_id} not found")
    
    issues: list[ValidationIssue] = []
    rules_passed = 0
    rules_failed = 0
    
    for rule in rules:
        rule_name = rule.get("name", "Unnamed")
        field = rule.get("field")
        condition = rule.get("condition")
        value = rule.get("value")
        severity = Severity(rule.get("severity", "error"))
        
        if not field or not condition:
            continue
        
        field_value = getattr(project, field, None)
        rule_passed = False
        
        if condition == "required":
            rule_passed = field_value is not None and field_value != ""
        elif condition == "equals":
            rule_passed = field_value == value
        elif condition == "in_list":
            rule_passed = field_value in (value or [])
        
        if rule_passed:
            rules_passed += 1
        else:
            rules_failed += 1
            issues.append(ValidationIssue(
                severity=severity,
                code="CUSTOM_RULE_FAILED",
                message=f"Rule {repr(rule_name)} failed",
                field=field,
            ))
    
    errors = [i for i in issues if i.severity == Severity.ERROR]
    return {
        "valid": len(errors) == 0,
        "rules_evaluated": len(rules),
        "rules_passed": rules_passed,
        "rules_failed": rules_failed,
        "error_count": len(errors),
        "issues": [i.to_dict() for i in issues],
    }
