"""PM-BRM tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import BRM_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _assess_benefits_maturity,
    _detect_benefits_drift,
    _forecast_benefit_realisation,
    _forecast_benefits_outturn,
    _generate_benefits_narrative,
    _get_benefit_dependency_network,
    _get_benefits_cascade_impact,
    _get_benefits_health,
    _get_benefits_realisation_trajectory,
    _ingest_benefit,
    _map_benefit_dependency,
    _track_benefit_measurement,
)

_DISPATCH = {
    "ingest_benefit": _ingest_benefit,
    "track_benefit_measurement": _track_benefit_measurement,
    "get_benefits_health": _get_benefits_health,
    "map_benefit_dependency": _map_benefit_dependency,
    "get_benefit_dependency_network": _get_benefit_dependency_network,
    "forecast_benefit_realisation": _forecast_benefit_realisation,
    "detect_benefits_drift": _detect_benefits_drift,
    "get_benefits_cascade_impact": _get_benefits_cascade_impact,
    "generate_benefits_narrative": _generate_benefits_narrative,
    "assess_benefits_maturity": _assess_benefits_maturity,
    "forecast_benefits_outturn": _forecast_benefits_outturn,
    "get_benefits_realisation_trajectory": _get_benefits_realisation_trajectory,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-brm tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
