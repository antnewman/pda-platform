"""PM-Knowledge tool registry for unified server aggregation."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from .server import KNOWLEDGE_TOOLS as TOOLS  # noqa: F401 — re-exported for unified server
from .server import (
    _get_benchmark_data,
    _get_benchmark_percentile,
    _get_failure_patterns,
    _get_ipa_guidance,
    _generate_premortem_questions,
    _list_knowledge_categories,
    _run_reference_class_check,
    _search_knowledge_base,
)

_DISPATCH = {
    "list_knowledge_categories": _list_knowledge_categories,
    "get_benchmark_data": _get_benchmark_data,
    "get_failure_patterns": _get_failure_patterns,
    "get_ipa_guidance": _get_ipa_guidance,
    "search_knowledge_base": _search_knowledge_base,
    "run_reference_class_check": _run_reference_class_check,
    "get_benchmark_percentile": _get_benchmark_percentile,
    "generate_premortem_questions": _generate_premortem_questions,
}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-knowledge tool call. Handlers already return list[TextContent]."""
    handler = _DISPATCH.get(name)
    if handler is not None:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
