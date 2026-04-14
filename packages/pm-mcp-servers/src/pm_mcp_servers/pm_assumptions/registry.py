"""Registry for pm-assumptions — exposes TOOLS, _DISPATCH, and dispatch()."""

from __future__ import annotations

from mcp.types import TextContent

from .server import (
    ASSUMPTIONS_TOOLS as TOOLS,
    _DISPATCH,
    _export_assumption_dashboard,
    _export_assumption_graph,
    _fetch_external_signal,
    _detect_external_drift,
    _load_assumption_register,
    _score_assumption_confidence,
)

__all__ = ["TOOLS", "_DISPATCH", "dispatch"]


async def dispatch(name: str, arguments: dict) -> list[TextContent]:
    handler = _DISPATCH.get(name)
    if handler is None:
        from mcp.types import TextContent
        import json
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    return await handler(arguments)
