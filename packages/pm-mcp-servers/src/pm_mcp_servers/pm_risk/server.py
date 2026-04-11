"""PM-Risk MCP server — Risk Register tools (P16).

Phase 1 tools:
  1. ingest_risk              — Register a risk with IPA/MoJ taxonomy metadata
  2. update_risk_status       — Transition a risk through its lifecycle
  3. get_risk_register        — Full register with mitigations and summary counts
  4. get_risk_heat_map        — 5x5 likelihood/impact matrix with score counts

Phase 2 tools:
  5. ingest_mitigation        — Record a mitigation action against a risk
  6. get_mitigation_progress  — Portfolio-level mitigation tracking and overdue flags

Phase 3 tools:
  7. get_portfolio_risks      — Cross-project HIGH/CRITICAL risk summary

Phase 4 tools:
  8. get_risk_velocity        — Analyse how individual risk scores are changing over successive review cycles
  9. detect_stale_risks       — Identify risks showing compliance-not-management patterns
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

RISK_TOOLS: list[Tool] = [
    # ------------------------------------------------------------------
    # Phase 1: Core register
    # ------------------------------------------------------------------
    Tool(
        name="ingest_risk",
        description=(
            "Register a risk in the project risk register using IPA/MoJ/CDDO taxonomy. "
            "Computes risk_score (likelihood x impact) and assigns a verbal rating: "
            "LOW (1-6), MEDIUM (7-12), HIGH (13-19), CRITICAL (20-25). "
            "Categories are aligned with the IPA risk taxonomy."
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
                    "description": "Concise risk title.",
                },
                "description": {
                    "type": "string",
                    "description": "Narrative explaining the risk, its cause and potential consequences.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "DELIVERY",
                        "FINANCIAL",
                        "STRATEGIC",
                        "LEGAL",
                        "REPUTATIONAL",
                        "TECHNICAL",
                        "RESOURCE",
                    ],
                    "description": "IPA-aligned risk category. Defaults to DELIVERY.",
                    "default": "DELIVERY",
                },
                "likelihood": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": (
                        "Likelihood score 1-5: 1=Rare, 2=Unlikely, 3=Possible, "
                        "4=Likely, 5=Almost Certain. Defaults to 3."
                    ),
                    "default": 3,
                },
                "impact": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": (
                        "Impact score 1-5: 1=Negligible, 2=Minor, 3=Moderate, "
                        "4=Major, 5=Catastrophic. Defaults to 3."
                    ),
                    "default": 3,
                },
                "owner": {
                    "type": "string",
                    "description": "Name or role of the risk owner.",
                },
                "target_date": {
                    "type": "string",
                    "description": "ISO date by which the risk must be mitigated (YYYY-MM-DD).",
                },
                "proximity": {
                    "type": "string",
                    "enum": ["IMMEDIATE", "THIS_QUARTER", "THIS_YEAR", "LONG_TERM"],
                    "description": "When the risk is expected to materialise.",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or context.",
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
        name="update_risk_status",
        description=(
            "Transition a risk to a new lifecycle status. "
            "Valid statuses: OPEN, MITIGATED, ACCEPTED, CLOSED, TRANSFERRED. "
            "Returns the updated risk record, or an error if the risk is not found."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "Unique identifier of the risk to update.",
                },
                "status": {
                    "type": "string",
                    "enum": ["OPEN", "MITIGATED", "ACCEPTED", "CLOSED", "TRANSFERRED"],
                    "description": "New status for the risk.",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes explaining the status change.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["risk_id", "status"],
        },
    ),
    Tool(
        name="get_risk_register",
        description=(
            "Return the full risk register for a project, optionally filtered by status "
            "and/or category. Each risk includes its mitigation actions. Results are "
            "sorted by risk_score descending (highest risks first). "
            "Includes summary counts: total, by_status, by_category, high_and_critical_count."
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
                    "enum": ["OPEN", "MITIGATED", "ACCEPTED", "CLOSED", "TRANSFERRED"],
                    "description": "Optional: filter risks by status.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "DELIVERY",
                        "FINANCIAL",
                        "STRATEGIC",
                        "LEGAL",
                        "REPUTATIONAL",
                        "TECHNICAL",
                        "RESOURCE",
                    ],
                    "description": "Optional: filter risks by category.",
                },
                "min_score": {
                    "type": "integer",
                    "description": "Optional: only return risks with risk_score >= this value.",
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
        name="get_risk_heat_map",
        description=(
            "Generate a 5x5 risk heat map (likelihood vs impact) for a project. "
            "Each cell contains the risk titles at that likelihood/impact position. "
            "Also returns score-band counts: critical_count (20-25), high_count (13-19), "
            "medium_count (7-12), low_count (1-6)."
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
    # ------------------------------------------------------------------
    # Phase 2: Mitigations
    # ------------------------------------------------------------------
    Tool(
        name="ingest_mitigation",
        description=(
            "Record a mitigation action against an existing risk. "
            "Validates that the risk exists before persisting. "
            "If residual_likelihood and residual_impact are both provided, "
            "computes and returns the residual_risk_score."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "ID of the risk this mitigation addresses (must exist).",
                },
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "action": {
                    "type": "string",
                    "description": "Description of the mitigation action to be taken.",
                },
                "owner": {
                    "type": "string",
                    "description": "Name or role of the person responsible for this action.",
                },
                "target_date": {
                    "type": "string",
                    "description": "ISO date by which this action should be completed (YYYY-MM-DD).",
                },
                "status": {
                    "type": "string",
                    "enum": ["PLANNED", "IN_PROGRESS", "COMPLETED", "ABANDONED"],
                    "description": "Current status of the mitigation action. Defaults to PLANNED.",
                    "default": "PLANNED",
                },
                "effectiveness": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                    "description": "Expected effectiveness of the mitigation.",
                },
                "residual_likelihood": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Expected likelihood score after this mitigation is applied.",
                },
                "residual_impact": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Expected impact score after this mitigation is applied.",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes about the mitigation.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["risk_id", "project_id", "action"],
        },
    ),
    Tool(
        name="get_mitigation_progress",
        description=(
            "Return all mitigation actions for a project, grouped by risk. "
            "For each risk group: risk title, original risk_score, mitigation count, "
            "count by status, and any overdue actions (target_date < today and not COMPLETED). "
            "Portfolio totals: total mitigations, completion_rate."
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
    # ------------------------------------------------------------------
    # Phase 3: Portfolio view
    # ------------------------------------------------------------------
    Tool(
        name="get_portfolio_risks",
        description=(
            "Cross-project risk summary for a portfolio. For each project: count of "
            "HIGH and CRITICAL risks (score >= 13) and the top 3 risks by score. "
            "Portfolio summary: total HIGH+CRITICAL count, projects with CRITICAL risks, "
            "projects with no risk data. The min_score parameter filters which risks are "
            "included (defaults to 13, returning HIGH and CRITICAL only)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of project identifiers to include in the portfolio view.",
                },
                "min_score": {
                    "type": "integer",
                    "description": (
                        "Minimum risk_score to include. Defaults to 13 (HIGH and CRITICAL only)."
                    ),
                    "default": 13,
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_ids"],
        },
    ),
    # ------------------------------------------------------------------
    # Phase 4: Velocity and staleness analysis
    # ------------------------------------------------------------------
    Tool(
        name="get_risk_velocity",
        description=(
            "Analyse how individual risk scores are changing over successive review cycles for a project. "
            "Returns risks with accelerating exposure (likelihood or impact increasing across reviews), "
            "decelerating exposure (scores improving), and stable risks. "
            "A risk whose likelihood has increased across three consecutive reviews is more urgent than "
            "one with a higher static score. Use to prioritise which risks require immediate intervention "
            "vs. which are being successfully managed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "min_history_entries": {
                    "type": "integer",
                    "description": "Minimum number of history entries required to compute velocity (default 2).",
                    "default": 2,
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="detect_stale_risks",
        description=(
            "Identify risks on the project register that show signs of compliance-not-management: "
            "risks that have not been updated recently, risks whose scores have not changed across "
            "multiple review cycles, and risks with no active mitigation. "
            "A risk register that appears maintained but is actually static is a governance red flag — "
            "it suggests risks are being reviewed for process compliance rather than actively managed. "
            "Returns a stale register score (0-100) and a categorised list of stale risks."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "stale_days": {
                    "type": "integer",
                    "description": "Number of days without update before a risk is considered stale (default 28).",
                    "default": 28,
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store.",
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
    """Create an AssuranceStore from the optional db_path argument."""
    from pm_data_tools.db.store import AssuranceStore

    raw_db_path = arguments.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    return AssuranceStore(db_path=db_path)


def _verbal_rating(score: int) -> str:
    """Convert a numeric risk score to a verbal rating."""
    if score <= 6:
        return "LOW"
    if score <= 12:
        return "MEDIUM"
    if score <= 19:
        return "HIGH"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _ingest_risk(arguments: dict[str, Any]) -> list[TextContent]:
    """Register a risk with full IPA metadata."""
    try:
        store = _get_store(arguments)

        likelihood = int(arguments.get("likelihood", 3))
        impact = int(arguments.get("impact", 3))
        risk_score = likelihood * impact
        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

        data = {
            "id": str(uuid.uuid4()),
            "project_id": arguments["project_id"],
            "title": arguments["title"],
            "description": arguments.get("description"),
            "category": arguments.get("category", "DELIVERY"),
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": risk_score,
            "status": "OPEN",
            "owner": arguments.get("owner"),
            "target_date": arguments.get("target_date"),
            "proximity": arguments.get("proximity"),
            "notes": arguments.get("notes"),
            "created_at": now,
            "updated_at": now,
        }

        store.upsert_risk(data)

        output = {
            "status": "success",
            "risk_id": data["id"],
            "project_id": data["project_id"],
            "title": data["title"],
            "category": data["category"],
            "likelihood": likelihood,
            "impact": impact,
            "risk_score": risk_score,
            "risk_rating": _verbal_rating(risk_score),
            "risk_status": data["status"],
            "message": (
                f"Risk '{data['title']}' registered with score {risk_score} "
                f"({_verbal_rating(risk_score)})."
            ),
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _update_risk_status(arguments: dict[str, Any]) -> list[TextContent]:
    """Transition a risk to a new lifecycle status."""
    try:
        store = _get_store(arguments)
        risk_id = arguments["risk_id"]
        status = arguments["status"]
        notes = arguments.get("notes")

        # Validate risk exists
        risk = store.get_risk_by_id(risk_id)
        if risk is None:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "error",
                            "code": 404,
                            "message": f"Risk '{risk_id}' not found.",
                        },
                        indent=2,
                    ),
                )
            ]

        store.update_risk_status(risk_id, status, notes=notes)

        # Fetch the updated record
        updated = store.get_risk_by_id(risk_id)

        output = {
            "status": "success",
            "risk_id": risk_id,
            "previous_status": risk.get("status"),
            "new_status": status,
            "risk": updated,
            "message": f"Risk '{risk.get('title')}' status updated to {status}.",
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_risk_register(arguments: dict[str, Any]) -> list[TextContent]:
    """Return the full risk register for a project with mitigations and summary counts."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        status_filter = arguments.get("status")
        category_filter = arguments.get("category")
        min_score = arguments.get("min_score")

        risks = store.get_risks(
            project_id,
            status_filter=status_filter,
            category_filter=category_filter,
        )

        # Apply min_score filter
        if min_score is not None:
            risks = [r for r in risks if (r.get("risk_score") or 0) >= min_score]

        # Sort by risk_score descending
        risks = sorted(risks, key=lambda r: r.get("risk_score") or 0, reverse=True)

        # Attach mitigations and verbal rating to each risk
        enriched = []
        for risk in risks:
            mitigations = store.get_mitigations(risk["id"])
            enriched.append(
                {
                    **risk,
                    "risk_rating": _verbal_rating(risk.get("risk_score") or 0),
                    "mitigations": mitigations,
                }
            )

        # Build summary counts
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        high_and_critical_count = 0

        for risk in enriched:
            s = risk.get("status") or "UNKNOWN"
            by_status[s] = by_status.get(s, 0) + 1

            c = risk.get("category") or "UNKNOWN"
            by_category[c] = by_category.get(c, 0) + 1

            score = risk.get("risk_score") or 0
            if score >= 13:
                high_and_critical_count += 1

        output = {
            "project_id": project_id,
            "filters": {
                "status": status_filter,
                "category": category_filter,
                "min_score": min_score,
            },
            "summary": {
                "total": len(enriched),
                "by_status": by_status,
                "by_category": by_category,
                "high_and_critical_count": high_and_critical_count,
            },
            "risks": enriched,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_risk_heat_map(arguments: dict[str, Any]) -> list[TextContent]:
    """Generate a 5x5 risk heat map for a project."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]

        risks = store.get_risks(project_id)

        # Build 5x5 matrix indexed [likelihood-1][impact-1]
        # Outer list: likelihood 1..5, inner list: impact 1..5
        matrix: list[list[list[str]]] = [[[] for _ in range(5)] for _ in range(5)]

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for risk in risks:
            likelihood = int(risk.get("likelihood") or 3)
            impact = int(risk.get("impact") or 3)
            title = risk.get("title") or risk.get("id", "")
            score = likelihood * impact

            # Clamp to valid range
            li = max(1, min(5, likelihood)) - 1
            ii = max(1, min(5, impact)) - 1
            matrix[li][ii].append(title)

            if score >= 20:
                critical_count += 1
            elif score >= 13:
                high_count += 1
            elif score >= 7:
                medium_count += 1
            else:
                low_count += 1

        output = {
            "project_id": project_id,
            "risk_count": len(risks),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "heat_map": {
                "description": (
                    "5x5 matrix indexed by [likelihood][impact] (both 1-5). "
                    "Each cell contains a list of risk titles at that position."
                ),
                "axes": {
                    "likelihood": ["1=Rare", "2=Unlikely", "3=Possible", "4=Likely", "5=Almost Certain"],
                    "impact": ["1=Negligible", "2=Minor", "3=Moderate", "4=Major", "5=Catastrophic"],
                },
                "matrix": matrix,
            },
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _ingest_mitigation(arguments: dict[str, Any]) -> list[TextContent]:
    """Record a mitigation action against an existing risk."""
    try:
        store = _get_store(arguments)
        risk_id = arguments["risk_id"]

        # Validate that the parent risk exists
        risk = store.get_risk_by_id(risk_id)
        if risk is None:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "error",
                            "code": 404,
                            "message": f"Risk '{risk_id}' not found. Cannot create mitigation.",
                        },
                        indent=2,
                    ),
                )
            ]

        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        residual_likelihood = arguments.get("residual_likelihood")
        residual_impact = arguments.get("residual_impact")

        # Compute residual score if both dimensions are provided
        residual_risk_score: int | None = None
        if residual_likelihood is not None and residual_impact is not None:
            residual_risk_score = int(residual_likelihood) * int(residual_impact)

        data = {
            "id": str(uuid.uuid4()),
            "risk_id": risk_id,
            "project_id": arguments["project_id"],
            "action": arguments["action"],
            "owner": arguments.get("owner"),
            "target_date": arguments.get("target_date"),
            "status": arguments.get("status", "PLANNED"),
            "effectiveness": arguments.get("effectiveness"),
            "residual_likelihood": residual_likelihood,
            "residual_impact": residual_impact,
            "notes": arguments.get("notes"),
            "created_at": now,
            "updated_at": now,
        }

        store.upsert_mitigation(data)

        output: dict[str, Any] = {
            "status": "success",
            "mitigation_id": data["id"],
            "risk_id": risk_id,
            "risk_title": risk.get("title"),
            "action": data["action"],
            "mitigation_status": data["status"],
        }

        if residual_risk_score is not None:
            output["residual_likelihood"] = residual_likelihood
            output["residual_impact"] = residual_impact
            output["residual_risk_score"] = residual_risk_score
            output["residual_risk_rating"] = _verbal_rating(residual_risk_score)

        output["message"] = (
            f"Mitigation recorded for risk '{risk.get('title')}'."
        )

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_mitigation_progress(arguments: dict[str, Any]) -> list[TextContent]:
    """Return mitigation progress for all risks on a project."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        today_str = date.today().isoformat()

        mitigations = store.get_mitigations_by_project(project_id)

        # Group mitigations by risk_id
        groups: dict[str, list[dict[str, Any]]] = {}
        for m in mitigations:
            rid = m.get("risk_id", "")
            groups.setdefault(rid, []).append(m)

        # Fetch all risks to get titles and scores
        risks = store.get_risks(project_id)
        risk_lookup = {r["id"]: r for r in risks}

        risk_groups = []
        total_mitigations = 0
        completed_count = 0

        for rid, mits in groups.items():
            risk_record = risk_lookup.get(rid, {})
            by_status: dict[str, int] = {}
            overdue = []

            for m in mits:
                s = m.get("status") or "UNKNOWN"
                by_status[s] = by_status.get(s, 0) + 1

                if s == "COMPLETED":
                    completed_count += 1

                td = m.get("target_date")
                if td and s != "COMPLETED" and str(td) < today_str:
                    overdue.append(
                        {
                            "mitigation_id": m.get("id"),
                            "action": m.get("action"),
                            "target_date": td,
                            "status": s,
                        }
                    )

            total_mitigations += len(mits)

            risk_groups.append(
                {
                    "risk_id": rid,
                    "risk_title": risk_record.get("title", "Unknown"),
                    "risk_score": risk_record.get("risk_score"),
                    "risk_rating": _verbal_rating(risk_record.get("risk_score") or 0),
                    "mitigation_count": len(mits),
                    "by_status": by_status,
                    "overdue_count": len(overdue),
                    "overdue": overdue,
                    "mitigations": mits,
                }
            )

        # Sort groups by risk_score descending
        risk_groups.sort(
            key=lambda g: g.get("risk_score") or 0, reverse=True
        )

        completion_rate = (
            round(completed_count / total_mitigations, 3) if total_mitigations else 0.0
        )

        output = {
            "project_id": project_id,
            "portfolio_summary": {
                "total_mitigations": total_mitigations,
                "completed_count": completed_count,
                "completion_rate": completion_rate,
                "risk_groups_count": len(risk_groups),
            },
            "risk_groups": risk_groups,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_risk_velocity(arguments: dict[str, Any]) -> list[TextContent]:
    """Analyse how risk scores are changing over successive review cycles."""
    try:
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        min_entries = arguments.get("min_history_entries", 2)

        risks = store.get_risks(project_id=project_id)

        accelerating = []
        decelerating = []
        stable = []
        insufficient_data = []

        for risk in risks:
            history = store.get_risk_score_history(risk["id"])

            if len(history) < min_entries:
                insufficient_data.append({
                    "risk_id": risk["id"],
                    "title": risk["title"],
                    "current_score": risk["risk_score"],
                    "history_entries": len(history),
                })
                continue

            scores = [h["risk_score"] for h in history]
            score_delta = scores[-1] - scores[0]
            recent_delta = scores[-1] - scores[-2] if len(scores) >= 2 else 0

            if len(scores) >= 3:
                recent_trend = scores[-1] - scores[-3]
            else:
                recent_trend = recent_delta

            risk_summary = {
                "risk_id": risk["id"],
                "title": risk["title"],
                "category": risk["category"],
                "current_score": risk["risk_score"],
                "current_likelihood": risk["likelihood"],
                "current_impact": risk["impact"],
                "score_at_first_entry": scores[0],
                "total_delta": score_delta,
                "recent_delta": recent_delta,
                "history_entries": len(history),
                "velocity": "accelerating" if recent_trend > 0 else ("decelerating" if recent_trend < 0 else "stable"),
            }

            if recent_trend > 0:
                accelerating.append(risk_summary)
            elif recent_trend < 0:
                decelerating.append(risk_summary)
            else:
                stable.append(risk_summary)

        accelerating.sort(key=lambda x: x["current_score"], reverse=True)

        result = {
            "project_id": project_id,
            "summary": {
                "total_risks": len(risks),
                "accelerating": len(accelerating),
                "decelerating": len(decelerating),
                "stable": len(stable),
                "insufficient_data": len(insufficient_data),
            },
            "accelerating_risks": accelerating,
            "decelerating_risks": decelerating,
            "stable_risks": stable,
            "insufficient_history": insufficient_data,
            "interpretation": (
                f"{len(accelerating)} risk(s) are accelerating (exposure increasing). "
                f"{len(decelerating)} are decelerating (being managed down). "
                f"{len(stable)} are stable. "
                + (f"{len(insufficient_data)} have insufficient history to assess velocity — "
                   f"consider whether these risks have genuinely not changed or have simply not been reviewed."
                   if insufficient_data else "")
            ),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _detect_stale_risks(arguments: dict[str, Any]) -> list[TextContent]:
    """Identify risks showing compliance-not-management patterns."""
    try:
        from datetime import timedelta
        store = _get_store(arguments)
        project_id = arguments["project_id"]
        stale_days = arguments.get("stale_days", 28)

        risks = store.get_risks(project_id=project_id)

        stale_threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=stale_days)

        not_updated = []
        score_unchanged = []
        no_mitigation = []

        for risk in risks:
            if risk["status"] != "OPEN":
                continue

            try:
                updated = datetime.fromisoformat(str(risk["updated_at"]).replace("Z", ""))
                if updated < stale_threshold:
                    days_since_update = (datetime.now(timezone.utc).replace(tzinfo=None) - updated).days
                    not_updated.append({
                        "risk_id": risk["id"],
                        "title": risk["title"],
                        "risk_score": risk["risk_score"],
                        "days_since_update": days_since_update,
                        "updated_at": risk["updated_at"],
                    })
            except (ValueError, AttributeError):
                pass

            history = store.get_risk_score_history(risk["id"])
            if len(history) >= 3:
                scores = [h["risk_score"] for h in history]
                if len(set(scores)) == 1:
                    score_unchanged.append({
                        "risk_id": risk["id"],
                        "title": risk["title"],
                        "risk_score": risk["risk_score"],
                        "history_entries": len(history),
                        "score_across_all_entries": scores[0],
                    })

            mitigations = store.get_mitigations(risk["id"])
            active_mitigations = [m for m in mitigations if m["status"] not in ("COMPLETED", "CANCELLED")]
            if not active_mitigations and (risk["risk_score"] or 0) >= 6:
                no_mitigation.append({
                    "risk_id": risk["id"],
                    "title": risk["title"],
                    "risk_score": risk["risk_score"],
                    "category": risk["category"],
                })

        open_risks = [r for r in risks if r.get("status") == "OPEN"]
        total_open = len(open_risks)
        if total_open == 0:
            stale_score = 0
            stale_interpretation = "No open risks on the register."
        else:
            stale_factors = len(set([r["risk_id"] for r in not_updated] +
                                     [r["risk_id"] for r in score_unchanged]))
            stale_score = min(100, int(100 * stale_factors / total_open))
            if stale_score == 0:
                stale_interpretation = "The risk register appears actively maintained."
            elif stale_score < 30:
                stale_interpretation = "Most risks are being actively managed. A small number require attention."
            elif stale_score < 60:
                stale_interpretation = "A significant proportion of risks show staleness indicators. The register may be maintained for compliance rather than active management."
            else:
                stale_interpretation = "The risk register is largely stale. This is a governance red flag — risks are not being actively managed."

        result = {
            "project_id": project_id,
            "stale_register_score": stale_score,
            "stale_days_threshold": stale_days,
            "summary": {
                "total_open_risks": total_open,
                "not_updated_in_threshold": len(not_updated),
                "score_unchanged_across_history": len(score_unchanged),
                "high_scoring_with_no_active_mitigation": len(no_mitigation),
            },
            "not_recently_updated": not_updated,
            "score_unchanged": score_unchanged,
            "no_active_mitigation": no_mitigation,
            "interpretation": stale_interpretation,
            "recommended_actions": [
                f"Review the {len(not_updated)} risk(s) not updated in the last {stale_days} days with their owners.",
                f"Challenge the {len(score_unchanged)} risk(s) with unchanged scores — have circumstances genuinely not changed?",
                f"Assign active mitigations to the {len(no_mitigation)} high-scoring open risk(s) with no current mitigation.",
            ] if total_open > 0 else [],
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_portfolio_risks(arguments: dict[str, Any]) -> list[TextContent]:
    """Cross-project HIGH/CRITICAL risk summary."""
    try:
        store = _get_store(arguments)
        project_ids: list[str] = arguments["project_ids"]
        min_score = int(arguments.get("min_score", 13))

        projects_with_critical: list[str] = []
        projects_with_no_data: list[str] = []
        total_high_critical = 0
        project_summaries = []

        for project_id in project_ids:
            risks = store.get_risks(project_id)

            if not risks:
                projects_with_no_data.append(project_id)
                project_summaries.append(
                    {
                        "project_id": project_id,
                        "total_risks": 0,
                        "high_and_critical_count": 0,
                        "has_critical": False,
                        "top_risks": [],
                    }
                )
                continue

            # Filter to min_score threshold
            filtered = [
                r for r in risks if (r.get("risk_score") or 0) >= min_score
            ]
            filtered_sorted = sorted(
                filtered, key=lambda r: r.get("risk_score") or 0, reverse=True
            )

            has_critical = any(
                (r.get("risk_score") or 0) >= 20 for r in filtered
            )
            if has_critical:
                projects_with_critical.append(project_id)

            total_high_critical += len(filtered)

            top_risks = [
                {
                    "risk_id": r.get("id"),
                    "title": r.get("title"),
                    "category": r.get("category"),
                    "risk_score": r.get("risk_score"),
                    "risk_rating": _verbal_rating(r.get("risk_score") or 0),
                    "status": r.get("status"),
                    "owner": r.get("owner"),
                }
                for r in filtered_sorted[:3]
            ]

            project_summaries.append(
                {
                    "project_id": project_id,
                    "total_risks": len(risks),
                    "high_and_critical_count": len(filtered),
                    "has_critical": has_critical,
                    "top_risks": top_risks,
                }
            )

        output = {
            "min_score_threshold": min_score,
            "portfolio_summary": {
                "projects_assessed": len(project_ids),
                "total_high_and_critical": total_high_critical,
                "projects_with_critical_risks": projects_with_critical,
                "projects_with_no_risk_data": projects_with_no_data,
            },
            "projects": project_summaries,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
