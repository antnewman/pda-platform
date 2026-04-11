"""PDA Platform — unified MCP server.

Aggregates all fourteen PDA MCP servers into a single endpoint:

  pm-data        ( 6 tools)   Project data loading, querying, conversion
  pm-analyse     ( 6 tools)   AI-powered risk, forecasting, health assessment
  pm-validate    ( 4 tools)   Structural, semantic, and NISTA validation
  pm-nista       ( 5 tools)   GMPP reporting and NISTA integration
  pm-assure      (27 tools)   Assurance quality, compliance, assumptions, workflows, dashboards, ARMM, gate readiness
  pm-brm         (10 tools)   Benefits Realisation Management
  pm-portfolio   ( 5 tools)   Cross-project portfolio aggregation and health rollup
  pm-ev          ( 2 tools)   Earned Value metrics and HTML dashboard generation
  pm-synthesis   ( 2 tools)   AI-generated executive health summaries and comparisons
  pm-risk        ( 9 tools)   Risk register, heat map, mitigations, velocity tracking, stale register detection
  pm-change      ( 5 tools)   Change control log, impact analysis, and change pressure detection
  pm-resource    ( 5 tools)   Resource loading, conflict detection, capacity planning
  pm-financial   ( 5 tools)   Budget baseline, actuals, cost performance, EAC forecasting
  pm-knowledge   ( 8 tools)   IPA benchmarks, failure patterns, guidance, reference class checks, pre-mortem questions

Total: 99 tools accessible through one connection.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from ..pm_analyse.registry import TOOLS as ANALYSE_TOOLS
from ..pm_analyse.registry import dispatch as analyse_dispatch
from ..pm_assure.registry import TOOLS as ASSURE_TOOLS
from ..pm_assure.registry import dispatch as assure_dispatch
from ..pm_brm.registry import TOOLS as BRM_TOOLS
from ..pm_brm.registry import dispatch as brm_dispatch
from ..pm_data.registry import TOOLS as DATA_TOOLS
from ..pm_data.registry import dispatch as data_dispatch
from ..pm_change.registry import TOOLS as CHANGE_TOOLS
from ..pm_change.registry import dispatch as change_dispatch
from ..pm_financial.registry import TOOLS as FINANCIAL_TOOLS
from ..pm_financial.registry import dispatch as financial_dispatch
from ..pm_knowledge.registry import TOOLS as KNOWLEDGE_TOOLS
from ..pm_knowledge.registry import dispatch as knowledge_dispatch
from ..pm_ev.registry import TOOLS as EV_TOOLS
from ..pm_ev.registry import dispatch as ev_dispatch
from ..pm_nista.registry import TOOLS as NISTA_TOOLS
from ..pm_nista.registry import dispatch as nista_dispatch
from ..pm_portfolio.registry import TOOLS as PORTFOLIO_TOOLS
from ..pm_portfolio.registry import dispatch as portfolio_dispatch
from ..pm_resource.registry import TOOLS as RESOURCE_TOOLS
from ..pm_resource.registry import dispatch as resource_dispatch
from ..pm_risk.registry import TOOLS as RISK_TOOLS
from ..pm_risk.registry import dispatch as risk_dispatch
from ..pm_synthesis.registry import TOOLS as SYNTHESIS_TOOLS
from ..pm_synthesis.registry import dispatch as synthesis_dispatch
from ..pm_validate.registry import TOOLS as VALIDATE_TOOLS
from ..pm_validate.registry import dispatch as validate_dispatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("pda-platform")

# Build lookup: tool_name -> dispatch function
_TOOL_DISPATCH: dict[str, Any] = {}
for _tools, _dispatch_fn in [
    (DATA_TOOLS, data_dispatch),
    (ANALYSE_TOOLS, analyse_dispatch),
    (VALIDATE_TOOLS, validate_dispatch),
    (NISTA_TOOLS, nista_dispatch),
    (ASSURE_TOOLS, assure_dispatch),
    (BRM_TOOLS, brm_dispatch),
    (PORTFOLIO_TOOLS, portfolio_dispatch),
    (EV_TOOLS, ev_dispatch),
    (SYNTHESIS_TOOLS, synthesis_dispatch),
    (RISK_TOOLS, risk_dispatch),
    (CHANGE_TOOLS, change_dispatch),
    (RESOURCE_TOOLS, resource_dispatch),
    (FINANCIAL_TOOLS, financial_dispatch),
    (KNOWLEDGE_TOOLS, knowledge_dispatch),
]:
    for _tool in _tools:
        _TOOL_DISPATCH[_tool.name] = _dispatch_fn

ALL_TOOLS: list[Tool] = (
    DATA_TOOLS + ANALYSE_TOOLS + VALIDATE_TOOLS + NISTA_TOOLS
    + ASSURE_TOOLS + BRM_TOOLS + PORTFOLIO_TOOLS + EV_TOOLS + SYNTHESIS_TOOLS
    + RISK_TOOLS + CHANGE_TOOLS + RESOURCE_TOOLS + FINANCIAL_TOOLS + KNOWLEDGE_TOOLS
)

logger.info(
    "PDA Platform unified server: %d tools from %d modules",
    len(ALL_TOOLS),
    14,
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all tools from all PDA modules."""
    return ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Route tool call to the owning module's dispatcher."""
    dispatch_fn = _TOOL_DISPATCH.get(name)
    if dispatch_fn is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    return await dispatch_fn(name, arguments)


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point for pda-platform-server."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
