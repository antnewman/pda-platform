"""PM-Resource MCP server — Resource & Capacity Planning tools (P18).

Tools:
  1. analyse_resource_loading   — Compute planned days, utilisation, and allocation
                                  status per resource from in-memory schedule data.
  2. detect_resource_conflicts  — Find periods where a resource's overlapping tasks
                                  exceed a combined-load threshold.
  3. get_critical_resources     — Identify resources assigned to critical-path tasks
                                  and flag single points of failure.
  4. log_resource_plan          — Persist a resource allocation plan record to the
                                  AssuranceStore (SQLite).
  5. get_portfolio_capacity     — Aggregate planned/actual days across projects from
                                  the AssuranceStore for a portfolio capacity view.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

RESOURCE_TOOLS: list[Tool] = [
    Tool(
        name="analyse_resource_loading",
        description=(
            "Analyse resource loading for a project from in-memory schedule data. "
            "Computes total planned days, task lists, earliest start, latest finish, "
            "and utilisation percentage per resource. Flags resources as "
            "OVER_ALLOCATED (>100%), AT_RISK (80-100%), or OK (<80%). "
            "Requires the project to have been loaded first via load_project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier returned by load_project.",
                },
                "period_start": {
                    "type": "string",
                    "description": (
                        "Optional ISO date (YYYY-MM-DD) to restrict the analysis "
                        "window start. Defaults to earliest task start in the project."
                    ),
                },
                "period_end": {
                    "type": "string",
                    "description": (
                        "Optional ISO date (YYYY-MM-DD) to restrict the analysis "
                        "window end. Defaults to latest task finish in the project."
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="detect_resource_conflicts",
        description=(
            "Detect scheduling conflicts where a single resource is assigned to "
            "overlapping tasks whose combined load exceeds a threshold. Returns "
            "each conflict pair with overlap period and combined load in days, "
            "plus a plain-English recommendation. "
            "Requires the project to have been loaded first via load_project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier returned by load_project.",
                },
                "threshold_pct": {
                    "type": "number",
                    "description": (
                        "Flag resources whose combined load on overlapping tasks "
                        "exceeds this utilisation percentage. Default 100.0."
                    ),
                    "default": 100.0,
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="get_critical_resources",
        description=(
            "Identify resources assigned to tasks on the critical path "
            "(tasks where is_critical is True or total_float is 0). "
            "Highlights single points of failure — resources who are the "
            "sole assignee on one or more critical tasks. "
            "Requires the project to have been loaded first via load_project."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier returned by load_project.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="log_resource_plan",
        description=(
            "Persist a resource allocation plan record to the AssuranceStore. "
            "Records planned and actual days for a named resource over a defined "
            "period, including role, availability percentage, and optional notes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "resource_name": {
                    "type": "string",
                    "description": "Name of the resource or team member.",
                },
                "role": {
                    "type": "string",
                    "description": "Optional role or job title for this resource.",
                },
                "period_start": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD) — start of the planning period.",
                },
                "period_end": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD) — end of the planning period.",
                },
                "planned_days": {
                    "type": "number",
                    "description": "Number of working days planned for this resource in the period.",
                },
                "actual_days": {
                    "type": "number",
                    "description": "Optional number of working days actually delivered.",
                },
                "availability_pct": {
                    "type": "number",
                    "description": (
                        "Resource availability as a percentage (e.g. 50.0 for half-time). "
                        "Default 100.0."
                    ),
                    "default": 100.0,
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about this allocation.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": [
                "project_id",
                "resource_name",
                "period_start",
                "period_end",
                "planned_days",
            ],
        },
    ),
    Tool(
        name="get_portfolio_capacity",
        description=(
            "Aggregate resource capacity across multiple projects from persisted "
            "resource plans in the AssuranceStore. Returns total planned days, "
            "total actual days, utilisation percentage, and project count per resource, "
            "ordered by planned days descending. Provides a portfolio-wide view of "
            "capacity usage, over-delivery, and resources with no actuals recorded."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional list of project IDs to include. "
                        "If omitted, aggregates across all projects in the store."
                    ),
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": [],
        },
    ),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_store(arguments: dict[str, Any]) -> Any:
    """Return a process-cached AssuranceStore (audit finding P2.F03)."""
    from pm_data_tools.db.store import get_store

    raw_db_path = arguments.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    return get_store(db_path)


def _parse_date(value: Any) -> date | None:
    """Safely coerce a date/datetime/string to a date object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _working_days(start: date, finish: date) -> float:
    """Approximate working days between two dates using the 5/7 rule."""
    if finish <= start:
        return 0.0
    calendar_days = (finish - start).days
    return calendar_days * 5.0 / 7.0


def _extract_resources(task: Any) -> list[str]:
    """
    Extract resource names from a task object.

    Checks, in order:
      1. task.resources  — list of resource names or objects with a .name attribute
      2. task.assigned_to — string or list
    Falls back to "Unassigned" if neither is present.
    """
    resources_attr = getattr(task, "resources", None)
    if resources_attr:
        if isinstance(resources_attr, list) and len(resources_attr) > 0:
            result: list[str] = []
            for r in resources_attr:
                if isinstance(r, str):
                    result.append(r)
                elif hasattr(r, "name"):
                    result.append(str(r.name))
                else:
                    result.append(str(r))
            return result if result else ["Unassigned"]

    assigned_to = getattr(task, "assigned_to", None)
    if assigned_to:
        if isinstance(assigned_to, list):
            return [str(a) for a in assigned_to] if assigned_to else ["Unassigned"]
        return [str(assigned_to)]

    return ["Unassigned"]


def _is_critical(task: Any) -> bool:
    """Return True if a task is on the critical path."""
    if getattr(task, "is_critical", None):
        return True
    total_float = getattr(task, "total_float", None)
    if total_float is not None:
        try:
            return float(total_float) == 0.0
        except (TypeError, ValueError):
            pass
    return False


def _task_name(task: Any) -> str:
    """Return a display name for a task."""
    for attr in ("name", "task_name", "title", "description"):
        val = getattr(task, attr, None)
        if val:
            return str(val)
    return "Unnamed task"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _analyse_resource_loading(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Compute resource loading statistics from in-memory project data."""
    try:
        from pm_mcp_servers.shared import project_store

        project_id = arguments["project_id"]
        project = project_store.get(project_id)
        if project is None:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Error: project '{project_id}' not found in the project store. "
                        "Please call load_project first to load the schedule file."
                    ),
                )
            ]

        tasks = getattr(project, "tasks", None) or []

        # Parse optional analysis window
        window_start_raw = arguments.get("period_start")
        window_end_raw = arguments.get("period_end")
        window_start: date | None = _parse_date(window_start_raw)
        window_end: date | None = _parse_date(window_end_raw)

        # First pass — determine actual project bounds if not supplied
        all_starts: list[date] = []
        all_finishes: list[date] = []
        for task in tasks:
            s = _parse_date(getattr(task, "start_date", None))
            f = _parse_date(
                getattr(task, "finish_date", None)
                or getattr(task, "baseline_finish", None)
            )
            if s:
                all_starts.append(s)
            if f:
                all_finishes.append(f)

        effective_start = window_start or (min(all_starts) if all_starts else date.today())
        effective_end = window_end or (max(all_finishes) if all_finishes else date.today())

        # Available working days in the analysis window at 100% availability
        available_days = _working_days(effective_start, effective_end)
        if available_days <= 0:
            available_days = 1.0  # avoid division by zero

        # Accumulate per-resource data
        resource_data: dict[str, dict[str, Any]] = {}

        for task in tasks:
            start = _parse_date(getattr(task, "start_date", None))
            finish = _parse_date(
                getattr(task, "finish_date", None)
                or getattr(task, "baseline_finish", None)
            )
            if start is None or finish is None:
                continue

            # Apply window filter — skip tasks entirely outside the window
            if window_end and start > window_end:
                continue
            if window_start and finish < window_start:
                continue

            duration = _working_days(start, finish)
            name = _task_name(task)
            resource_names = _extract_resources(task)

            for resource in resource_names:
                if resource not in resource_data:
                    resource_data[resource] = {
                        "resource_name": resource,
                        "planned_days": 0.0,
                        "tasks": [],
                        "earliest_start": None,
                        "latest_finish": None,
                    }
                rd = resource_data[resource]
                rd["planned_days"] += duration
                rd["tasks"].append(name)
                if rd["earliest_start"] is None or start < rd["earliest_start"]:
                    rd["earliest_start"] = start
                if rd["latest_finish"] is None or finish > rd["latest_finish"]:
                    rd["latest_finish"] = finish

        # Second pass — compute utilisation and status
        per_resource: list[dict[str, Any]] = []
        over_allocated_count = 0
        at_risk_count = 0

        for rd in resource_data.values():
            planned = rd["planned_days"]
            utilisation_pct = round(planned / available_days * 100.0, 1)
            if utilisation_pct > 100.0:
                status = "OVER_ALLOCATED"
                over_allocated_count += 1
            elif utilisation_pct >= 80.0:
                status = "AT_RISK"
                at_risk_count += 1
            else:
                status = "OK"

            per_resource.append(
                {
                    "resource_name": rd["resource_name"],
                    "planned_days": round(planned, 2),
                    "available_days": round(available_days, 2),
                    "utilisation_pct": utilisation_pct,
                    "status": status,
                    "task_count": len(rd["tasks"]),
                    "tasks": rd["tasks"],
                    "earliest_start": str(rd["earliest_start"]) if rd["earliest_start"] else None,
                    "latest_finish": str(rd["latest_finish"]) if rd["latest_finish"] else None,
                }
            )

        per_resource.sort(key=lambda x: x["utilisation_pct"], reverse=True)

        output = {
            "project_id": project_id,
            "analysis_window": {
                "period_start": str(effective_start),
                "period_end": str(effective_end),
                "available_days": round(available_days, 2),
            },
            "total_resources": len(per_resource),
            "over_allocated_count": over_allocated_count,
            "at_risk_count": at_risk_count,
            "per_resource": per_resource,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _detect_resource_conflicts(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Find overlapping task assignments that exceed the load threshold."""
    try:
        from pm_mcp_servers.shared import project_store

        project_id = arguments["project_id"]
        threshold_pct = float(arguments.get("threshold_pct", 100.0))

        project = project_store.get(project_id)
        if project is None:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Error: project '{project_id}' not found in the project store. "
                        "Please call load_project first to load the schedule file."
                    ),
                )
            ]

        tasks = getattr(project, "tasks", None) or []

        # Build per-resource task list with dates and duration
        resource_tasks: dict[str, list[dict[str, Any]]] = {}

        for task in tasks:
            start = _parse_date(getattr(task, "start_date", None))
            finish = _parse_date(
                getattr(task, "finish_date", None)
                or getattr(task, "baseline_finish", None)
            )
            if start is None or finish is None:
                continue

            duration = _working_days(start, finish)
            name = _task_name(task)
            resource_names = _extract_resources(task)

            for resource in resource_names:
                if resource not in resource_tasks:
                    resource_tasks[resource] = []
                resource_tasks[resource].append(
                    {"name": name, "start": start, "finish": finish, "duration": duration}
                )

        # Find overlapping pairs per resource
        conflicts: list[dict[str, Any]] = []
        affected_resources: set[str] = set()

        for resource, task_list in resource_tasks.items():
            for i in range(len(task_list)):
                for j in range(i + 1, len(task_list)):
                    a = task_list[i]
                    b = task_list[j]
                    overlap_start = max(a["start"], b["start"])
                    overlap_end = min(a["finish"], b["finish"])
                    if overlap_start < overlap_end:
                        # Tasks overlap — compute combined load in the overlap window
                        overlap_days = _working_days(overlap_start, overlap_end)
                        combined_load_days = a["duration"] + b["duration"]
                        # Compute total available days across the union of both tasks
                        union_start = min(a["start"], b["start"])
                        union_end = max(a["finish"], b["finish"])
                        union_days = _working_days(union_start, union_end)
                        if union_days > 0:
                            combined_pct = combined_load_days / union_days * 100.0
                        else:
                            combined_pct = 0.0

                        if combined_pct > threshold_pct:
                            affected_resources.add(resource)
                            conflicts.append(
                                {
                                    "resource_name": resource,
                                    "task_a": a["name"],
                                    "task_b": b["name"],
                                    "overlap_start": str(overlap_start),
                                    "overlap_end": str(overlap_end),
                                    "overlap_days": round(overlap_days, 2),
                                    "combined_load_days": round(combined_load_days, 2),
                                    "combined_utilisation_pct": round(combined_pct, 1),
                                }
                            )

        affected_list = sorted(affected_resources)
        n = len(affected_list)
        if n == 0:
            recommendation = (
                f"No resource conflicts detected above the {threshold_pct:.0f}% threshold."
            )
        elif n == 1:
            recommendation = (
                f"1 resource is overloaded on overlapping tasks. "
                "Consider resequencing tasks or redistributing workload."
            )
        else:
            recommendation = (
                f"{n} resources are overloaded on overlapping tasks. "
                "Consider resequencing tasks or bringing in additional capacity."
            )

        output = {
            "project_id": project_id,
            "threshold_pct": threshold_pct,
            "conflict_count": len(conflicts),
            "affected_resources": affected_list,
            "conflicts": conflicts,
            "recommendation": recommendation,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_critical_resources(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Identify resources assigned to critical-path tasks."""
    try:
        from pm_mcp_servers.shared import project_store

        project_id = arguments["project_id"]
        project = project_store.get(project_id)
        if project is None:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Error: project '{project_id}' not found in the project store. "
                        "Please call load_project first to load the schedule file."
                    ),
                )
            ]

        tasks = getattr(project, "tasks", None) or []

        # Collect critical-path tasks with their resource assignments
        critical_task_records: list[dict[str, Any]] = []
        for task in tasks:
            if not _is_critical(task):
                continue
            start = _parse_date(getattr(task, "start_date", None))
            finish = _parse_date(
                getattr(task, "finish_date", None)
                or getattr(task, "baseline_finish", None)
            )
            duration = _working_days(start, finish) if start and finish else 0.0
            critical_task_records.append(
                {
                    "name": _task_name(task),
                    "start": str(start) if start else None,
                    "finish": str(finish) if finish else None,
                    "duration_days": round(duration, 2),
                    "resources": _extract_resources(task),
                }
            )

        # Aggregate per resource
        resource_map: dict[str, dict[str, Any]] = {}
        single_points: list[str] = []

        for record in critical_task_records:
            task_resources = record["resources"]
            task_info = {
                "name": record["name"],
                "start": record["start"],
                "finish": record["finish"],
                "duration_days": record["duration_days"],
            }
            # Flag as single point of failure if only one resource is assigned
            if len(task_resources) == 1:
                spof_candidate = task_resources[0]
                if spof_candidate != "Unassigned":
                    single_points.append(spof_candidate)

            for resource in task_resources:
                if resource not in resource_map:
                    resource_map[resource] = {
                        "resource_name": resource,
                        "critical_task_count": 0,
                        "tasks": [],
                    }
                resource_map[resource]["critical_task_count"] += 1
                resource_map[resource]["tasks"].append(task_info)

        critical_resources = sorted(
            resource_map.values(),
            key=lambda x: x["critical_task_count"],
            reverse=True,
        )

        most_critical = critical_resources[0]["resource_name"] if critical_resources else None
        spof_unique = sorted(set(single_points))

        output = {
            "project_id": project_id,
            "critical_task_count": len(critical_task_records),
            "critical_resources": critical_resources,
            "most_critical_resource": most_critical,
            "single_points_of_failure": spof_unique,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _log_resource_plan(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Persist a resource allocation plan to the AssuranceStore."""
    try:
        store = _get_store(arguments)

        data: dict[str, Any] = {
            "project_id": arguments["project_id"],
            "resource_name": arguments["resource_name"],
            "role": arguments.get("role"),
            "period_start": arguments["period_start"],
            "period_end": arguments["period_end"],
            "planned_days": float(arguments["planned_days"]),
            "actual_days": (
                float(arguments["actual_days"])
                if arguments.get("actual_days") is not None
                else None
            ),
            "availability_pct": float(arguments.get("availability_pct", 100.0)),
            "notes": arguments.get("notes"),
        }

        store.upsert_resource_plan(data)
        plans = store.get_resource_plans(
            project_id=data["project_id"],
            resource_name=data["resource_name"],
        )
        # Return the most recently created record for this resource
        created = plans[-1] if plans else data

        output = {
            "status": "success",
            "record": created,
            "message": (
                f"Resource plan logged for '{data['resource_name']}' "
                f"on project '{data['project_id']}': "
                f"{data['planned_days']} planned days "
                f"({data['period_start']} to {data['period_end']})."
            ),
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_portfolio_capacity(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Aggregate capacity data from persisted resource plans across projects."""
    try:
        store = _get_store(arguments)
        project_ids: list[str] | None = arguments.get("project_ids") or None

        if project_ids:
            plans: list[dict[str, Any]] = []
            for pid in project_ids:
                plans.extend(store.get_resource_plans(project_id=pid))
        else:
            plans = store.get_all_resource_plans()

        # Filter by project_ids if supplied (belt-and-braces, store may not filter)
        if project_ids:
            plans = [p for p in plans if p.get("project_id") in project_ids]

        # Aggregate per resource
        agg: dict[str, dict[str, Any]] = {}
        for plan in plans:
            resource = plan.get("resource_name", "Unknown")
            pid = plan.get("project_id")
            planned = float(plan.get("planned_days") or 0)
            actual_raw = plan.get("actual_days")
            actual = float(actual_raw) if actual_raw is not None else None

            if resource not in agg:
                agg[resource] = {
                    "resource_name": resource,
                    "total_planned_days": 0.0,
                    "total_actual_days": 0.0,
                    "has_actual": False,
                    "project_ids": set(),
                }
            agg[resource]["total_planned_days"] += planned
            if actual is not None:
                agg[resource]["total_actual_days"] += actual
                agg[resource]["has_actual"] = True
            if pid:
                agg[resource]["project_ids"].add(pid)

        # Build result rows
        rows: list[dict[str, Any]] = []
        over_delivered: list[str] = []
        no_actuals: list[str] = []

        for resource, data in agg.items():
            planned_total = data["total_planned_days"]
            actual_total = data["total_actual_days"]
            has_actual = data["has_actual"]
            project_count = len(data["project_ids"])

            if has_actual and planned_total > 0:
                utilisation_pct: float | None = round(actual_total / planned_total * 100.0, 1)
            else:
                utilisation_pct = None

            rows.append(
                {
                    "resource_name": resource,
                    "total_planned_days": round(planned_total, 2),
                    "total_actual_days": round(actual_total, 2) if has_actual else None,
                    "utilisation_pct": utilisation_pct,
                    "project_count": project_count,
                    "has_actual": has_actual,
                }
            )

            if has_actual and actual_total > planned_total:
                over_delivered.append(resource)
            if not has_actual:
                no_actuals.append(resource)

        rows.sort(key=lambda x: x["total_planned_days"], reverse=True)

        output = {
            "project_ids_queried": project_ids or "all",
            "total_unique_resources": len(rows),
            "total_planned_days": round(sum(r["total_planned_days"] for r in rows), 2),
            "over_delivered_resources": sorted(over_delivered),
            "no_actuals_resources": sorted(no_actuals),
            "resources": rows,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
