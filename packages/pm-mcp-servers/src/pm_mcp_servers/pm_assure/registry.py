"""PM-Assure tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import ASSURE_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _analyse_assurance_overhead,
    _analyse_override_patterns,
    _assess_gate_readiness,
    _check_artefact_currency,
    _check_confidence_divergence,
    _classify_project_domain,
    _compare_gate_readiness,
    _create_project_from_profile,
    _export_dashboard_data,
    _export_dashboard_html,
    _get_armm_report,
    _get_assumption_drift,
    _get_cascade_impact,
    _get_gate_readiness_history,
    _get_workflow_history,
    _ingest_assumption,
    _ingest_lesson,
    _log_assurance_activity,
    _log_override_decision,
    _nista_longitudinal_trend,
    _reclassify_from_store,
    _recommend_review_schedule,
    _review_action_status,
    _run_assurance_workflow,
    _scan_for_red_flags,
    _search_lessons,
    _track_review_actions,
    _validate_assumption,
)

_DISPATCH = {
    "nista_longitudinal_trend": _nista_longitudinal_trend,
    "track_review_actions": _track_review_actions,
    "review_action_status": _review_action_status,
    "check_artefact_currency": _check_artefact_currency,
    "check_confidence_divergence": _check_confidence_divergence,
    "recommend_review_schedule": _recommend_review_schedule,
    "log_override_decision": _log_override_decision,
    "analyse_override_patterns": _analyse_override_patterns,
    "ingest_lesson": _ingest_lesson,
    "search_lessons": _search_lessons,
    "log_assurance_activity": _log_assurance_activity,
    "analyse_assurance_overhead": _analyse_assurance_overhead,
    "run_assurance_workflow": _run_assurance_workflow,
    "get_workflow_history": _get_workflow_history,
    "classify_project_domain": _classify_project_domain,
    "reclassify_from_store": _reclassify_from_store,
    "ingest_assumption": _ingest_assumption,
    "validate_assumption": _validate_assumption,
    "get_assumption_drift": _get_assumption_drift,
    "get_cascade_impact": _get_cascade_impact,
    "assess_gate_readiness": _assess_gate_readiness,
    "get_gate_readiness_history": _get_gate_readiness_history,
    "compare_gate_readiness": _compare_gate_readiness,
    "scan_for_red_flags": _scan_for_red_flags,
    "create_project_from_profile": _create_project_from_profile,
    "export_dashboard_data": _export_dashboard_data,
    "export_dashboard_html": _export_dashboard_html,
    "get_armm_report": _get_armm_report,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-assure tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
