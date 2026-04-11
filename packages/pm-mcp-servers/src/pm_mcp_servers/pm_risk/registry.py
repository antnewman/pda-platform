"""PM-Risk tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import RISK_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _detect_stale_risks,
    _get_mitigation_progress,
    _get_portfolio_risks,
    _get_risk_heat_map,
    _get_risk_register,
    _get_risk_velocity,
    _ingest_mitigation,
    _ingest_risk,
    _update_risk_status,
)

_DISPATCH = {
    "ingest_risk": _ingest_risk,
    "update_risk_status": _update_risk_status,
    "get_risk_register": _get_risk_register,
    "get_risk_heat_map": _get_risk_heat_map,
    "ingest_mitigation": _ingest_mitigation,
    "get_mitigation_progress": _get_mitigation_progress,
    "get_portfolio_risks": _get_portfolio_risks,
    "get_risk_velocity": _get_risk_velocity,
    "detect_stale_risks": _detect_stale_risks,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-risk tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
