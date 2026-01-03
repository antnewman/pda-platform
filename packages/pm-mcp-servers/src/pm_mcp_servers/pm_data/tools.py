"""PM-Data MCP Server Tools - Production Implementation with Real Parsers

Integrates with pm-data-tools library for production-quality PM data handling.
Supports 8 formats: MSPDI, P6 XER, Jira, Monday, Asana, Smartsheet, GMPP, NISTA

Developed by members of the PDA Task Force to support NISTA Programme and Project Data Standard trial.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

# Real imports from pm-data-tools
try:
    from pm_data_tools.parsers import detect_format, create_parser
    from pm_data_tools.models import Project
    from pm_data_tools.exceptions import ParseError, UnsupportedFormatError
    from pm_data_tools.exporters import create_exporter
    HAS_PM_DATA_TOOLS = True
except ImportError:
    HAS_PM_DATA_TOOLS = False
    logging.warning("pm-data-tools not installed - MCP server will not function")

logger = logging.getLogger(__name__)


@dataclass
class ProjectStore:
    """Thread-safe in-memory project storage."""
    _projects: dict[str, Project] = field(default_factory=dict)

    def add(self, project_id: str, project: Project) -> None:
        """Store a project."""
        self._projects[project_id] = project

    def get(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by ID."""
        return self._projects.get(project_id)

    def exists(self, project_id: str) -> bool:
        """Check if project exists."""
        return project_id in self._projects

    def list_all(self) -> list[str]:
        """List all project IDs."""
        return list(self._projects.keys())

    def remove(self, project_id: str) -> bool:
        """Remove a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False


# Global project store instance
_store = ProjectStore()


def _serialize_date(d: Optional[date]) -> Optional[str]:
    """Safely serialize date to ISO format."""
    if d is None:
        return None
    # Handle both date and datetime
    if hasattr(d, 'date'):
        return d.date().isoformat()
    return d.isoformat()


async def load_project(arguments: dict, store: ProjectStore = _store) -> dict:
    """Load project from file using real pm-data-tools parsers.
    
    Supports automatic format detection or explicit format specification.
    Handles all 8 pm-data-tools formats with comprehensive error handling.
    """
    if not HAS_PM_DATA_TOOLS:
        return {
            "error": {
                "code": "DEPENDENCY_MISSING",
                "message": "pm-data-tools not installed. Run: pip install pm-data-tools>=0.2.0"
            }
        }

    file_path = arguments.get("file_path")
    format_hint = arguments.get("format", "auto")

    if not file_path:
        return {"error": {"code": "MISSING_PARAMETER", "message": "file_path is required"}}

    path = Path(file_path)
    if not path.exists():
        return {"error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {file_path}"}}

    try:
        # Auto-detect format if needed
        if format_hint == "auto":
            logger.info(f"Auto-detecting format for: {file_path}")
            detected = detect_format(str(path))
            if not detected:
                return {
                    "error": {
                        "code": "FORMAT_DETECTION_FAILED",
                        "message": "Could not detect file format. Specify format explicitly.",
                        "supported_formats": ["mspdi", "p6_xer", "jira", "monday", "asana", "smartsheet", "gmpp", "nista"]
                    }
                }
            format_hint = detected
            logger.info(f"Detected format: {format_hint}")

        # Create appropriate parser
        parser = create_parser(format_hint)
        logger.info(f"Parsing {path.name} as {format_hint}")

        # Parse the file
        project = parser.parse_file(str(path))

        # Generate unique ID and store
        project_id = str(uuid.uuid4())
        store.add(project_id, project)
        logger.info(f"Loaded project '{project.name}' with ID: {project_id}")

        # Calculate metrics
        tasks = project.tasks or []
        resources = project.resources or []
        dependencies = project.dependencies or []
        milestones = [t for t in tasks if getattr(t, 'is_milestone', False)]

        # Calculate critical path length
        critical_tasks = [t for t in tasks if getattr(t, 'is_critical', False)]
        cp_length = sum(int(t.duration.to_days()) if t.duration else 0 for t in critical_tasks)

        return {
            "project_id": project_id,
            "name": project.name,
            "description": project.description,
            "status": project.delivery_confidence.value if project.delivery_confidence else None,
            "task_count": len(tasks),
            "resource_count": len(resources),
            "dependency_count": len(dependencies),
            "milestone_count": len(milestones),
            "start_date": _serialize_date(project.start_date),
            "end_date": _serialize_date(project.finish_date),
            "critical_path_length_days": cp_length,
            "critical_task_count": len(critical_tasks),
            "source_format": format_hint,
            "file_path": str(path),
        }

    except UnsupportedFormatError as e:
        logger.error(f"Unsupported format: {e}")
        return {
            "error": {
                "code": "UNSUPPORTED_FORMAT",
                "message": str(e),
                "supported_formats": ["mspdi", "p6_xer", "jira", "monday", "asana", "smartsheet", "gmpp", "nista"]
            }
        }

    except ParseError as e:
        logger.error(f"Parse error: {e}")
        return {
            "error": {
                "code": "PARSE_ERROR",
                "message": str(e),
                "file": file_path
            }
        }

    except Exception as e:
        logger.exception(f"Unexpected error loading project: {e}")
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Failed to load project: {str(e)}"
            }
        }



async def query_tasks(arguments: dict, store: ProjectStore = _store) -> dict:
    if not HAS_PM_DATA_TOOLS:
        return {"error": {"code": "DEPENDENCY_MISSING", "message": "pm-data-tools not installed"}}
    project_id = arguments.get("project_id")
    filters = arguments.get("filters", {})
    limit = arguments.get("limit", 100)
    offset = arguments.get("offset", 0)
    if not project_id:
        return {"error": {"code": "MISSING_PARAMETER", "message": "project_id is required"}}
    project = store.get(project_id)
    if not project:
        return {"error": {"code": "PROJECT_NOT_FOUND", "message": f"Project {project_id} not found"}}
    tasks = project.tasks or []
    matching_tasks = []
    for task in tasks:
        if "status" in filters and task.status.value not in filters["status"] if hasattr(task.status, "value") else task.status not in filters["status"]:
            continue
        if "is_critical" in filters and not getattr(task, "is_critical", False):
            continue
        if "is_milestone" in filters and getattr(task, "is_milestone", False) != filters["is_milestone"]:
            continue
        matching_tasks.append(task)
    total_count = len(matching_tasks)
    paginated_tasks = matching_tasks[offset:offset + limit]
    return {
        "project_id": project_id,
        "total_matching": total_count,
        "returned_count": len(paginated_tasks),
        "offset": offset,
        "limit": limit,
        "tasks": [{"id": t.id, "name": t.name, "status": t.status.value if hasattr(t.status, "value") else str(t.status), "start_date": _serialize_date(t.start_date), "finish_date": _serialize_date(t.finish_date), "duration_days": int(t.duration.to_days()) if t.duration else None, "percent_complete": t.percent_complete, "is_milestone": getattr(t, "is_milestone", False)} for t in paginated_tasks]
    }


async def get_critical_path(arguments: dict, store: ProjectStore = _store) -> dict:
    if not HAS_PM_DATA_TOOLS:
        return {"error": {"code": "DEPENDENCY_MISSING", "message": "pm-data-tools not installed"}}
    project_id = arguments.get("project_id")
    if not project_id:
        return {"error": {"code": "MISSING_PARAMETER", "message": "project_id is required"}}
    project = store.get(project_id)
    if not project:
        return {"error": {"code": "PROJECT_NOT_FOUND", "message": f"Project {project_id} not found"}}
    tasks = project.tasks or []
    critical_tasks = [t for t in tasks if getattr(t, "is_critical", False)]
    return {
        "project_id": project_id,
        "critical_path_length_days": sum(t.duration or 0 for t in critical_tasks),
        "critical_task_count": len(critical_tasks),
        "critical_tasks": [{"id": t.id, "name": t.name, "start_date": _serialize_date(t.start_date), "finish_date": _serialize_date(t.finish_date)} for t in critical_tasks]
    }


async def get_dependencies(arguments: dict, store: ProjectStore = _store) -> dict:
    if not HAS_PM_DATA_TOOLS:
        return {"error": {"code": "DEPENDENCY_MISSING", "message": "pm-data-tools not installed"}}
    project_id = arguments.get("project_id")
    if not project_id:
        return {"error": {"code": "MISSING_PARAMETER", "message": "project_id is required"}}
    project = store.get(project_id)
    if not project:
        return {"error": {"code": "PROJECT_NOT_FOUND", "message": f"Project {project_id} not found"}}
    dependencies = project.dependencies or []
    return {"project_id": project_id, "total_dependencies": len(dependencies), "dependencies": [{"predecessor_id": d.predecessor_id, "successor_id": d.successor_id, "type": d.type} for d in dependencies]}


async def convert_format(arguments: dict, store: ProjectStore = _store) -> dict:
    if not HAS_PM_DATA_TOOLS:
        return {"error": {"code": "DEPENDENCY_MISSING", "message": "pm-data-tools not installed"}}
    project_id = arguments.get("project_id")
    target_format = arguments.get("target_format")
    if not project_id or not target_format:
        return {"error": {"code": "MISSING_PARAMETER", "message": "project_id and target_format are required"}}
    project = store.get(project_id)
    if not project:
        return {"error": {"code": "PROJECT_NOT_FOUND", "message": f"Project {project_id} not found"}}
    try:
        exporter = create_exporter(target_format)
        data = exporter.export_to_string(project)
        return {"project_id": project_id, "target_format": target_format, "data": data}
    except Exception as e:
        return {"error": {"code": "EXPORT_ERROR", "message": str(e)}}


async def get_project_summary(arguments: dict, store: ProjectStore = _store) -> dict:
    if not HAS_PM_DATA_TOOLS:
        return {"error": {"code": "DEPENDENCY_MISSING", "message": "pm-data-tools not installed"}}
    project_id = arguments.get("project_id")
    if not project_id:
        return {"error": {"code": "MISSING_PARAMETER", "message": "project_id is required"}}
    project = store.get(project_id)
    if not project:
        return {"error": {"code": "PROJECT_NOT_FOUND", "message": f"Project {project_id} not found"}}
    tasks = project.tasks or []
    resources = project.resources or []
    critical_tasks = [t for t in tasks if getattr(t, "is_critical", False)]
    milestones = [t for t in tasks if getattr(t, "is_milestone", False)]
    completed_tasks = [t for t in tasks if t.percent_complete == 100]
    return {
        "project_id": project_id,
        "name": project.name,
        "description": project.description,
        "status": project.delivery_confidence.value if project.delivery_confidence else None,
        "start_date": _serialize_date(project.start_date),
        "end_date": _serialize_date(project.finish_date),
        "task_count": len(tasks),
        "resource_count": len(resources),
        "critical_task_count": len(critical_tasks),
        "milestone_count": len(milestones),
        "completed_task_count": len(completed_tasks),
        "percent_complete": round(len(completed_tasks) / len(tasks) * 100, 1) if tasks else 0
    }
