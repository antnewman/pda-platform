"""PM-Lessons tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import LESSONS_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _extract_lessons,
    _get_project_lessons,
    _search_lessons,
    _get_systemic_patterns,
    _generate_lessons_section,
)

_DISPATCH = {
    "extract_lessons": _extract_lessons,
    "get_project_lessons": _get_project_lessons,
    "search_project_lessons": _search_lessons,
    "get_systemic_patterns": _get_systemic_patterns,
    "generate_lessons_section": _generate_lessons_section,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-lessons tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
