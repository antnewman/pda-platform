"""PM-Simulation tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import SIMULATION_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _get_simulation_results,
    _run_schedule_simulation,
)

_DISPATCH = {
    "run_schedule_simulation": _run_schedule_simulation,
    "get_simulation_results": _get_simulation_results,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-simulation tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
