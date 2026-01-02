"""Tool implementations for PM-Data MCP Server.

These tools wrap pm-data-tools library functionality for MCP protocol.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


async def load_project(arguments: dict, projects: dict) -> dict:
    """Load a project file and store in session.

    Args:
        arguments: {file_path: str, format: Optional[str]}
        projects: In-memory project store

    Returns:
        dict with project_id and summary info
    """
    file_path = arguments["file_path"]
    format_hint = arguments.get("format", "auto")

    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        return {
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": f"File not found: {file_path}"
            }
        }

    # TODO: Replace with actual pm-data-tools parsers
    # For now, create a mock project structure
    project_id = str(uuid4())[:8]

    # Mock project data
    project = {
        "id": project_id,
        "name": f"Project from {path.name}",
        "source_file": str(path),
        "source_format": format_hint,
        "tasks": [
            {
                "id": "task-1",
                "name": "Planning Phase",
                "status": "completed",
                "is_critical": True,
                "is_milestone": False,
                "start_date": "2026-01-01",
                "finish_date": "2026-01-10",
                "percent_complete": 100,
                "duration": 10,
                "total_float": 0,
            },
            {
                "id": "task-2",
                "name": "Design Gate",
                "status": "in_progress",
                "is_critical": True,
                "is_milestone": True,
                "start_date": "2026-01-11",
                "finish_date": "2026-01-11",
                "percent_complete": 0,
                "duration": 0,
                "total_float": 0,
            },
            {
                "id": "task-3",
                "name": "Implementation",
                "status": "not_started",
                "is_critical": False,
                "is_milestone": False,
                "start_date": "2026-01-12",
                "finish_date": "2026-02-28",
                "percent_complete": 0,
                "duration": 48,
                "total_float": 5,
            },
        ],
        "resources": [
            {"id": "res-1", "name": "John Smith"},
            {"id": "res-2", "name": "Jane Doe"},
        ],
        "dependencies": [
            {"predecessor_id": "task-1", "successor_id": "task-2", "type": "FS", "lag": 0},
            {"predecessor_id": "task-2", "successor_id": "task-3", "type": "FS", "lag": 0},
        ],
        "start_date": "2026-01-01",
        "end_date": "2026-02-28",
    }

    # Store in session
    projects[project_id] = project

    # Get critical path tasks
    critical_tasks = [t for t in project["tasks"] if t["is_critical"]]

    return {
        "project_id": project_id,
        "name": project["name"],
        "source_file": str(path),
        "source_format": format_hint,
        "task_count": len(project["tasks"]),
        "resource_count": len(project["resources"]),
        "milestone_count": len([t for t in project["tasks"] if t["is_milestone"]]),
        "start_date": project["start_date"],
        "end_date": project["end_date"],
        "critical_path_length_days": sum(t["duration"] for t in critical_tasks),
        "message": "Project loaded successfully (using mock data - replace with pm-data-tools parser)"
    }


async def query_tasks(arguments: dict, projects: dict) -> dict:
    """Query tasks with filters.

    Args:
        arguments: {project_id: str, filters: Optional[dict], limit: Optional[int]}
        projects: In-memory project store

    Returns:
        dict with matching tasks
    """
    project_id = arguments["project_id"]
    filters = arguments.get("filters", {})
    limit = arguments.get("limit", 100)

    if project_id not in projects:
        return {
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project {project_id} not found. Use load_project first."
            }
        }

    project = projects[project_id]
    tasks = project["tasks"][:]

    # Apply filters
    if "status" in filters:
        status_list = filters["status"]
        tasks = [t for t in tasks if t["status"] in status_list]

    if "is_critical" in filters:
        tasks = [t for t in tasks if t["is_critical"] == filters["is_critical"]]

    if "is_milestone" in filters:
        tasks = [t for t in tasks if t["is_milestone"] == filters["is_milestone"]]

    if "assignee" in filters:
        # Mock: filter by assignee (would need assignment data in real implementation)
        pass

    if "start_after" in filters:
        start_after = filters["start_after"]
        tasks = [t for t in tasks if t["start_date"] >= start_after]

    if "end_before" in filters:
        end_before = filters["end_before"]
        tasks = [t for t in tasks if t["finish_date"] <= end_before]

    # Limit results
    tasks = tasks[:limit]

    return {
        "project_id": project_id,
        "total_matching": len(tasks),
        "filters_applied": filters,
        "tasks": tasks
    }


async def get_critical_path(arguments: dict, projects: dict) -> dict:
    """Get critical path tasks.

    Args:
        arguments: {project_id: str, include_near_critical: Optional[bool]}
        projects: In-memory project store

    Returns:
        dict with critical path info
    """
    project_id = arguments["project_id"]
    include_near_critical = arguments.get("include_near_critical", False)

    if project_id not in projects:
        return {
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project {project_id} not found"
            }
        }

    project = projects[project_id]

    critical_tasks = [t for t in project["tasks"] if t["is_critical"]]
    near_critical_tasks = []

    if include_near_critical:
        near_critical_tasks = [
            t for t in project["tasks"]
            if not t["is_critical"] and t.get("total_float", 999) <= 5
        ]

    return {
        "project_id": project_id,
        "critical_path_length_days": sum(t["duration"] for t in critical_tasks),
        "critical_task_count": len(critical_tasks),
        "critical_tasks": [
            {
                "id": t["id"],
                "name": t["name"],
                "start_date": t["start_date"],
                "finish_date": t["finish_date"],
                "duration_days": t["duration"],
                "total_float_days": t.get("total_float", 0),
                "percent_complete": t["percent_complete"]
            }
            for t in critical_tasks
        ],
        "near_critical_tasks": [
            {
                "id": t["id"],
                "name": t["name"],
                "total_float_days": t.get("total_float", 0)
            }
            for t in near_critical_tasks
        ] if include_near_critical else []
    }


async def get_dependencies(arguments: dict, projects: dict) -> dict:
    """Get dependency graph.

    Args:
        arguments: {project_id: str, task_id: Optional[str], direction: Optional[str]}
        projects: In-memory project store

    Returns:
        dict with dependency information
    """
    project_id = arguments["project_id"]
    task_id = arguments.get("task_id")
    direction = arguments.get("direction", "both")

    if project_id not in projects:
        return {
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project {project_id} not found"
            }
        }

    project = projects[project_id]
    dependencies = project.get("dependencies", [])

    if task_id:
        predecessors = []
        successors = []

        if direction in ["predecessors", "both"]:
            predecessors = [
                d for d in dependencies
                if d["successor_id"] == task_id
            ]

        if direction in ["successors", "both"]:
            successors = [
                d for d in dependencies
                if d["predecessor_id"] == task_id
            ]

        return {
            "project_id": project_id,
            "task_id": task_id,
            "predecessors": [
                {
                    "id": d["predecessor_id"],
                    "type": d["type"],
                    "lag": d.get("lag", 0)
                }
                for d in predecessors
            ],
            "successors": [
                {
                    "id": d["successor_id"],
                    "type": d["type"],
                    "lag": d.get("lag", 0)
                }
                for d in successors
            ]
        }

    # Return all dependencies
    return {
        "project_id": project_id,
        "total_dependencies": len(dependencies),
        "dependencies": [
            {
                "predecessor_id": d["predecessor_id"],
                "successor_id": d["successor_id"],
                "type": d["type"],
                "lag": d.get("lag", 0)
            }
            for d in dependencies
        ]
    }


async def convert_format(arguments: dict, projects: dict) -> dict:
    """Convert project to different format.

    Args:
        arguments: {project_id: str, target_format: str}
        projects: In-memory project store

    Returns:
        dict with converted data or file path
    """
    project_id = arguments["project_id"]
    target_format = arguments["target_format"]

    if project_id not in projects:
        return {
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project {project_id} not found"
            }
        }

    project = projects[project_id]

    # TODO: Replace with actual exporters from pm-data-tools
    if target_format == "json":
        return {
            "project_id": project_id,
            "target_format": "json",
            "data": project
        }

    elif target_format == "nista_json":
        # Mock NISTA format
        nista_data = {
            "project_id": project_id,
            "project_name": project["name"],
            "start_date_baseline": project["start_date"],
            "end_date_baseline": project["end_date"],
            "whole_life_cost_baseline": 1000.0,  # Mock value
            "delivery_confidence_assessment_ipa": "Amber",
            "department": "Mock Department",
            "category": "Infrastructure and Construction",
            "milestones": [
                {
                    "name": t["name"],
                    "baseline_date": t["start_date"],
                    "status": "Completed" if t["percent_complete"] == 100 else "In Progress"
                }
                for t in project["tasks"]
                if t["is_milestone"]
            ]
        }
        return {
            "project_id": project_id,
            "target_format": "nista_json",
            "data": nista_data,
            "message": "Mock NISTA export - replace with NISTAExporter"
        }

    elif target_format == "mspdi":
        # Mock MSPDI XML
        mspdi_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>{project["name"]}</Name>
    <StartDate>{project["start_date"]}</StartDate>
    <FinishDate>{project["end_date"]}</FinishDate>
    <Tasks>
        <!-- {len(project["tasks"])} tasks -->
    </Tasks>
</Project>'''
        return {
            "project_id": project_id,
            "target_format": "mspdi",
            "data": mspdi_xml,
            "message": "Mock MSPDI export - replace with real exporter"
        }

    else:
        return {
            "error": {
                "code": "UNSUPPORTED_FORMAT",
                "message": f"Format {target_format} not yet implemented"
            }
        }


async def get_project_summary(arguments: dict, projects: dict) -> dict:
    """Get high-level project summary.

    Args:
        arguments: {project_id: str}
        projects: In-memory project store

    Returns:
        dict with project summary
    """
    project_id = arguments["project_id"]

    if project_id not in projects:
        return {
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project {project_id} not found"
            }
        }

    project = projects[project_id]

    critical_tasks = [t for t in project["tasks"] if t["is_critical"]]
    completed_tasks = [t for t in project["tasks"] if t["percent_complete"] == 100]

    return {
        "project_id": project_id,
        "name": project["name"],
        "source_file": project.get("source_file"),
        "source_format": project.get("source_format"),
        "task_count": len(project["tasks"]),
        "resource_count": len(project.get("resources", [])),
        "dependency_count": len(project.get("dependencies", [])),
        "milestone_count": len([t for t in project["tasks"] if t["is_milestone"]]),
        "critical_task_count": len(critical_tasks),
        "completed_task_count": len(completed_tasks),
        "percent_complete": round(len(completed_tasks) / len(project["tasks"]) * 100, 1) if project["tasks"] else 0,
        "start_date": project.get("start_date"),
        "end_date": project.get("end_date"),
        "critical_path_length_days": sum(t["duration"] for t in critical_tasks),
        "status": "Mock data - integrate with pm-data-tools for real projects"
    }
