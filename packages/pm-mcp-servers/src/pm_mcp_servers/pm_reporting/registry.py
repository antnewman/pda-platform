"""PM-Reporting tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import REPORTING_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _generate_gate_review_summary,
    _generate_sro_dashboard,
    _generate_board_exception_report,
    _generate_portfolio_summary,
    _generate_pir_template,
    _export_sro_dashboard_data,
)

_DISPATCH = {
    "generate_gate_review_summary": _generate_gate_review_summary,
    "generate_sro_dashboard": _generate_sro_dashboard,
    "generate_board_exception_report": _generate_board_exception_report,
    "generate_portfolio_summary": _generate_portfolio_summary,
    "generate_pir_template": _generate_pir_template,
    "export_sro_dashboard_data": _export_sro_dashboard_data,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-reporting tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
