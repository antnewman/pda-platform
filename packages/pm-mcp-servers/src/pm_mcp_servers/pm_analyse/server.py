"""PM-Analyse MCP Server - AI-powered project analysis.

This server provides advanced analysis tools for project management data including:
- Risk identification with confidence scoring
- Multi-method completion forecasting
- Outlier detection across task dimensions
- Multi-dimensional health assessment
- AI-generated mitigation strategies
- Baseline variance analysis

Integrates with pm-data server for project loading.
"""

import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import (
    assess_health,
    compare_baseline,
    detect_outliers,
    forecast_completion,
    identify_risks,
    suggest_mitigations,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("pm-analyse")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available analysis tools."""
    return [
        Tool(
            name="identify_risks",
            description="Identify project risks using AI-powered risk engine across schedule, cost, resource, scope, technical, and external dimensions",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["schedule", "cost", "resource", "scope", "technical", "external", "organizational", "stakeholder"]
                        },
                        "description": "Optional list of risk categories to focus on (analyzes all if omitted)"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "default": "standard",
                        "description": "Analysis depth (quick: basic, standard: normal, deep: comprehensive with dependency chains)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="forecast_completion",
            description="Forecast project completion date using multiple methods (EVM, Monte Carlo, Reference Class, ML Ensemble) with confidence intervals",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["earned_value", "monte_carlo", "reference_class", "simple_extrapolation", "ml_ensemble"],
                        "default": "ml_ensemble",
                        "description": "Forecasting method to use (ml_ensemble combines all methods)"
                    },
                    "confidence_level": {
                        "type": "number",
                        "minimum": 0.50,
                        "maximum": 0.95,
                        "default": 0.80,
                        "description": "Confidence level for prediction interval (0.50-0.95)"
                    },
                    "scenarios": {
                        "type": "boolean",
                        "default": True,
                        "description": "Generate optimistic/likely/pessimistic scenario forecasts"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "default": "standard",
                        "description": "Analysis depth (affects Monte Carlo iteration count)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="detect_outliers",
            description="Detect anomalies in task data across duration, progress, float, and dates using statistical analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "sensitivity": {
                        "type": "number",
                        "minimum": 0.5,
                        "maximum": 2.0,
                        "default": 1.0,
                        "description": "Detection sensitivity (0.5: less sensitive, 2.0: more sensitive)"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["duration", "progress", "float", "dates"]
                        },
                        "description": "Optional list of areas to check (checks all if omitted)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="assess_health",
            description="Assess multi-dimensional project health across schedule, cost, scope, resource, and quality dimensions with weighted scoring",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "include_trends": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include trend analysis (improving/stable/declining)"
                    },
                    "weights": {
                        "type": "object",
                        "properties": {
                            "schedule": {"type": "number", "minimum": 0, "maximum": 1},
                            "cost": {"type": "number", "minimum": 0, "maximum": 1},
                            "scope": {"type": "number", "minimum": 0, "maximum": 1},
                            "resource": {"type": "number", "minimum": 0, "maximum": 1},
                            "quality": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "description": "Optional custom weights for dimensions (must sum to 1.0, default: equal weights 0.2 each)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="suggest_mitigations",
            description="Generate AI-powered mitigation strategies for identified risks with effectiveness ratings and implementation steps",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "risk_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific risk IDs to generate mitigations for (from identify_risks)"
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["schedule", "cost", "resource", "scope", "technical", "external"]
                        },
                        "description": "Optional list of risk categories to focus on"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "default": "standard",
                        "description": "Analysis depth for risk identification before mitigation"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="compare_baseline",
            description="Compare current project state against baseline to identify schedule, duration, and cost variances with severity classification",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier from load_project"
                    },
                    "baseline_type": {
                        "type": "string",
                        "enum": ["current", "original", "approved"],
                        "default": "current",
                        "description": "Type of baseline to compare against"
                    },
                    "threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "default": 0,
                        "description": "Minimum variance percentage to report (0: all variances, higher: filter small changes)"
                    }
                },
                "required": ["project_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls by dispatching to appropriate tool function."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        # Dispatch to appropriate tool
        if name == "identify_risks":
            result = await identify_risks(arguments)
        elif name == "forecast_completion":
            result = await forecast_completion(arguments)
        elif name == "detect_outliers":
            result = await detect_outliers(arguments)
        elif name == "assess_health":
            result = await assess_health(arguments)
        elif name == "suggest_mitigations":
            result = await suggest_mitigations(arguments)
        elif name == "compare_baseline":
            result = await compare_baseline(arguments)
        else:
            result = {
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Unknown tool: {name}",
                    "suggestion": "Use one of: identify_risks, forecast_completion, detect_outliers, assess_health, suggest_mitigations, compare_baseline"
                }
            }

        # Convert result to JSON string for TextContent
        result_text = json.dumps(result, indent=2, default=str)

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {
            "error": {
                "code": "TOOL_EXECUTION_ERROR",
                "message": str(e),
                "suggestion": "Check tool parameters and try again"
            }
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Run the PM-Analyse MCP server."""
    logger.info("Starting PM-Analyse MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
