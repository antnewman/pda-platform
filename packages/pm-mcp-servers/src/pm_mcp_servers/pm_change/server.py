"""PM-Change MCP server — Change Control Log tools (P17).

Tools:
  1. log_change_request       — Register a new change request against a project
  2. update_change_status     — Transition a change request through its lifecycle
  3. get_change_log           — Retrieve all change requests for a project with summary
  4. get_change_impact_summary — Cost and schedule impact analysis across all statuses
  5. analyse_change_pressure  — Change velocity, pressure level, and scope-creep detection
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

CHANGE_TOOLS: list[Tool] = [
    Tool(
        name="log_change_request",
        description=(
            "Register a new change request against a project. Generates a unique ID, "
            "sets the status to SUBMITTED, and records the full metadata including "
            "cost impact (£), schedule impact (days), and scope narrative."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "title": {
                    "type": "string",
                    "description": "Short, descriptive title for the change request.",
                },
                "description": {
                    "type": "string",
                    "description": "What is changing and why.",
                },
                "change_type": {
                    "type": "string",
                    "enum": [
                        "SCOPE",
                        "COST",
                        "SCHEDULE",
                        "RESOURCE",
                        "TECHNICAL",
                        "GOVERNANCE",
                        "RISK",
                    ],
                    "description": "Category of change.",
                    "default": "SCOPE",
                },
                "impact_cost": {
                    "type": "number",
                    "description": (
                        "Financial impact in £. Positive = cost increase, "
                        "negative = saving."
                    ),
                },
                "impact_schedule_days": {
                    "type": "integer",
                    "description": (
                        "Schedule impact in days. Positive = delay, "
                        "negative = acceleration."
                    ),
                },
                "impact_scope": {
                    "type": "string",
                    "description": "Narrative description of the scope change.",
                },
                "raised_by": {
                    "type": "string",
                    "description": "Name or identifier of the person raising the request.",
                },
                "raised_date": {
                    "type": "string",
                    "description": "ISO date the change was raised (defaults to today).",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional additional notes.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id", "title"],
        },
    ),
    Tool(
        name="update_change_status",
        description=(
            "Transition a change request through its lifecycle. Supported statuses: "
            "SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, IMPLEMENTED, WITHDRAWN. "
            "Returns the updated change request record."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "change_id": {
                    "type": "string",
                    "description": "Unique ID of the change request to update.",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "SUBMITTED",
                        "UNDER_REVIEW",
                        "APPROVED",
                        "REJECTED",
                        "IMPLEMENTED",
                        "WITHDRAWN",
                    ],
                    "description": "New status to apply.",
                },
                "approved_by": {
                    "type": "string",
                    "description": "Name or identifier of the approver. Required when status is APPROVED.",
                },
                "decision_date": {
                    "type": "string",
                    "description": "ISO date of the approval or rejection decision.",
                },
                "implementation_date": {
                    "type": "string",
                    "description": "ISO date the change was implemented. Relevant for IMPLEMENTED status.",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about the status change.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["change_id", "status"],
        },
    ),
    Tool(
        name="get_change_log",
        description=(
            "Retrieve all change requests for a project ordered by raised date ascending. "
            "Includes a summary with total counts, status breakdown, type breakdown, "
            "and the total approved cost and schedule impacts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "SUBMITTED",
                        "UNDER_REVIEW",
                        "APPROVED",
                        "REJECTED",
                        "IMPLEMENTED",
                        "WITHDRAWN",
                    ],
                    "description": "Optional status filter.",
                },
                "change_type": {
                    "type": "string",
                    "enum": [
                        "SCOPE",
                        "COST",
                        "SCHEDULE",
                        "RESOURCE",
                        "TECHNICAL",
                        "GOVERNANCE",
                        "RISK",
                    ],
                    "description": "Optional change type filter.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="get_change_impact_summary",
        description=(
            "Analyse all change requests for a project to produce a financial and "
            "schedule impact summary. Breaks down requested vs approved impacts, "
            "approval rate, impact by change type, and pending cost exposure."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="analyse_change_pressure",
        description=(
            "Analyse change velocity and pressure over a configurable look-back window. "
            "Returns change rate per month, pressure level (LOW/MEDIUM/HIGH), "
            "dominant change type, cost pressure trend, scope-creep indicator, "
            "and a plain-English recommendation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "window_days": {
                    "type": "integer",
                    "description": "Look-back window in days for rate calculation.",
                    "default": 90,
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_store(arguments: dict[str, Any]) -> Any:
    """Create an AssuranceStore from optional db_path argument."""
    from pm_data_tools.db.store import AssuranceStore

    raw_db_path = arguments.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    return AssuranceStore(db_path=db_path)


def _today_iso() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _log_change_request(arguments: dict[str, Any]) -> list[TextContent]:
    """Register a new change request."""
    try:
        store = _get_store(arguments)
        now = datetime.now(timezone.utc).isoformat()
        change_id = str(uuid.uuid4())

        data = {
            "id": change_id,
            "project_id": arguments["project_id"],
            "title": arguments["title"],
            "description": arguments.get("description"),
            "change_type": arguments.get("change_type", "SCOPE"),
            "impact_cost": arguments.get("impact_cost"),
            "impact_schedule_days": arguments.get("impact_schedule_days"),
            "impact_scope": arguments.get("impact_scope"),
            "status": "SUBMITTED",
            "raised_by": arguments.get("raised_by"),
            "approved_by": None,
            "raised_date": arguments.get("raised_date") or _today_iso(),
            "decision_date": None,
            "implementation_date": None,
            "notes": arguments.get("notes"),
            "created_at": now,
            "updated_at": now,
        }

        store.upsert_change_request(data)

        output = {
            "status": "success",
            "change_id": change_id,
            "project_id": data["project_id"],
            "title": data["title"],
            "change_type": data["change_type"],
            "status_set": "SUBMITTED",
            "raised_date": data["raised_date"],
            "message": (
                f"Change request '{data['title']}' logged successfully "
                f"with ID {change_id}."
            ),
            "record": data,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _update_change_status(arguments: dict[str, Any]) -> list[TextContent]:
    """Transition a change request to a new status."""
    try:
        store = _get_store(arguments)
        change_id = arguments["change_id"]

        existing = store.get_change_request_by_id(change_id)
        if existing is None:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Change request '{change_id}' not found.",
                )
            ]

        new_status = arguments["status"]
        approved_by = arguments.get("approved_by")
        decision_date = arguments.get("decision_date")
        implementation_date = arguments.get("implementation_date")
        notes = arguments.get("notes")

        # Merge optional notes onto existing notes if both present
        if notes and existing.get("notes"):
            merged_notes = f"{existing['notes']}\n{notes}"
        elif notes:
            merged_notes = notes
        else:
            merged_notes = existing.get("notes")

        store.update_change_status(
            change_id=change_id,
            status=new_status,
            approved_by=approved_by,
            decision_date=decision_date,
        )

        # If implementation_date or merged notes need persisting, do a follow-up upsert
        if implementation_date is not None or notes is not None:
            updated = store.get_change_request_by_id(change_id) or {}
            updated["implementation_date"] = implementation_date or updated.get(
                "implementation_date"
            )
            updated["notes"] = merged_notes
            updated["updated_at"] = datetime.now(timezone.utc).isoformat()
            store.upsert_change_request(updated)

        record = store.get_change_request_by_id(change_id)

        output = {
            "status": "success",
            "change_id": change_id,
            "new_status": new_status,
            "message": (
                f"Change request '{change_id}' updated to status {new_status}."
            ),
            "record": record,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_change_log(arguments: dict[str, Any]) -> list[TextContent]:
    """Retrieve all change requests for a project with summary statistics."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        status_filter = arguments.get("status")
        type_filter = arguments.get("change_type")

        records = store.get_change_requests(
            project_id,
            status_filter=status_filter,
            change_type_filter=type_filter,
        )

        # Sort by raised_date ascending
        records = sorted(records, key=lambda r: r.get("raised_date") or "")

        # Build summary
        approved_statuses = {"APPROVED", "IMPLEMENTED"}

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        total_approved_cost = 0.0
        total_approved_schedule = 0

        for r in records:
            s = r.get("status") or "UNKNOWN"
            by_status[s] = by_status.get(s, 0) + 1

            t = r.get("change_type") or "UNKNOWN"
            by_type[t] = by_type.get(t, 0) + 1

            if s in approved_statuses:
                total_approved_cost += r.get("impact_cost") or 0.0
                total_approved_schedule += r.get("impact_schedule_days") or 0

        summary = {
            "total": len(records),
            "by_status": by_status,
            "by_type": by_type,
            "total_approved_cost_impact": round(total_approved_cost, 2),
            "total_approved_schedule_impact_days": total_approved_schedule,
        }

        output = {
            "project_id": project_id,
            "filters_applied": {
                "status": status_filter,
                "change_type": type_filter,
            },
            "summary": summary,
            "change_requests": records,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_change_impact_summary(arguments: dict[str, Any]) -> list[TextContent]:
    """Analyse cost and schedule impacts across all change requests."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]

        all_records = store.get_change_requests(project_id)

        excluded_statuses = {"WITHDRAWN", "REJECTED"}
        approved_statuses = {"APPROVED", "IMPLEMENTED"}
        pending_statuses = {"SUBMITTED", "UNDER_REVIEW"}

        total_requested_cost = 0.0
        total_approved_cost = 0.0
        total_requested_schedule = 0
        total_approved_schedule = 0
        approved_count = 0
        rejected_count = 0
        pending_count = 0
        pending_cost_exposure = 0.0

        by_type_impact: dict[str, dict[str, Any]] = {}

        for r in all_records:
            status = r.get("status") or ""
            change_type = r.get("change_type") or "UNKNOWN"
            cost = r.get("impact_cost") or 0.0
            schedule = r.get("impact_schedule_days") or 0

            if change_type not in by_type_impact:
                by_type_impact[change_type] = {
                    "cost_total": 0.0,
                    "schedule_days_total": 0,
                    "count": 0,
                }
            by_type_impact[change_type]["count"] += 1
            by_type_impact[change_type]["cost_total"] += cost
            by_type_impact[change_type]["schedule_days_total"] += schedule

            if status not in excluded_statuses:
                total_requested_cost += cost
                total_requested_schedule += schedule

            if status in approved_statuses:
                total_approved_cost += cost
                total_approved_schedule += schedule
                approved_count += 1

            if status == "REJECTED":
                rejected_count += 1

            if status in pending_statuses:
                pending_count += 1
                pending_cost_exposure += cost

        # Approval rate: approved / (approved + rejected); None if no decisions made
        decisions = approved_count + rejected_count
        approval_rate = round(approved_count / decisions, 3) if decisions > 0 else None

        # Round by_type cost totals
        for t in by_type_impact:
            by_type_impact[t]["cost_total"] = round(
                by_type_impact[t]["cost_total"], 2
            )

        output = {
            "project_id": project_id,
            "total_requested_cost": round(total_requested_cost, 2),
            "total_approved_cost": round(total_approved_cost, 2),
            "total_requested_schedule_days": total_requested_schedule,
            "total_approved_schedule_days": total_approved_schedule,
            "approval_rate": approval_rate,
            "by_type_impact": by_type_impact,
            "pending_count": pending_count,
            "pending_cost_exposure": round(pending_cost_exposure, 2),
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _analyse_change_pressure(arguments: dict[str, Any]) -> list[TextContent]:
    """Analyse change velocity and pressure over a look-back window."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        window_days = int(arguments.get("window_days") or 90)

        all_records = store.get_change_requests(project_id)

        cutoff = date.today() - timedelta(days=window_days)

        # Changes within the look-back window
        window_records = []
        for r in all_records:
            raised_raw = r.get("raised_date")
            if raised_raw:
                try:
                    raised = date.fromisoformat(str(raised_raw)[:10])
                    if raised >= cutoff:
                        window_records.append(r)
                except ValueError:
                    pass

        changes_in_window = len(window_records)

        # Monthly rate = count / (window_days / 30.44)
        months_in_window = window_days / 30.44
        change_rate_per_month = (
            round(changes_in_window / months_in_window, 2) if months_in_window > 0 else 0.0
        )

        # Pressure level thresholds
        if change_rate_per_month < 2:
            pressure_level = "LOW"
        elif change_rate_per_month <= 5:
            pressure_level = "MEDIUM"
        else:
            pressure_level = "HIGH"

        # Dominant change type within window
        type_counts: dict[str, int] = {}
        for r in window_records:
            t = r.get("change_type") or "UNKNOWN"
            type_counts[t] = type_counts.get(t, 0) + 1

        dominant_type: str | None = None
        if type_counts:
            dominant_type = max(type_counts, key=lambda k: type_counts[k])

        # Cost pressure trend — last 3 changes (globally, by raised_date)
        sorted_all = sorted(
            all_records,
            key=lambda r: r.get("raised_date") or "",
        )
        last_three = sorted_all[-3:]
        if len(last_three) == 3 and all(
            (r.get("impact_cost") or 0) > 0 for r in last_three
        ):
            cost_pressure_trend = "ESCALATING"
        else:
            cost_pressure_trend = "STABLE"

        # Scope-creep indicator: >50% of window changes are SCOPE type
        scope_count = sum(
            1 for r in window_records if (r.get("change_type") or "") == "SCOPE"
        )
        scope_creep_indicator = (
            (scope_count / changes_in_window) > 0.5
            if changes_in_window > 0
            else False
        )

        # Plain-English recommendation
        recommendation_parts: list[str] = []
        if pressure_level == "HIGH":
            recommendation_parts.append(
                f"Change pressure is HIGH at {change_rate_per_month:.1f} requests/month "
                f"over the last {window_days} days; consider a formal change freeze or "
                f"impact threshold before approving further requests."
            )
        elif pressure_level == "MEDIUM":
            recommendation_parts.append(
                f"Change pressure is MEDIUM at {change_rate_per_month:.1f} requests/month; "
                f"maintain close scrutiny at change board and ensure cumulative impacts "
                f"are tracked against the approved baseline."
            )
        else:
            recommendation_parts.append(
                f"Change pressure is LOW at {change_rate_per_month:.1f} requests/month; "
                f"the project change log is within expected bounds."
            )

        if scope_creep_indicator:
            recommendation_parts.append(
                "Scope creep is indicated — over half of recent changes are classified "
                "as SCOPE; review the project scope baseline and benefits case to ensure "
                "alignment."
            )

        if cost_pressure_trend == "ESCALATING":
            recommendation_parts.append(
                "The last three changes all carry positive cost impacts; "
                "escalate to the Senior Responsible Owner and re-validate the business case."
            )

        recommendation = " ".join(recommendation_parts)

        output = {
            "project_id": project_id,
            "window_days": window_days,
            "changes_in_window": changes_in_window,
            "change_rate_per_month": change_rate_per_month,
            "pressure_level": pressure_level,
            "dominant_type": dominant_type,
            "cost_pressure_trend": cost_pressure_trend,
            "scope_creep_indicator": scope_creep_indicator,
            "recommendation": recommendation,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
