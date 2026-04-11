"""PM-Analyse tool registry for unified server aggregation."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.types import TextContent, Tool

from .tools import (
    assess_health,
    compare_baseline,
    detect_narrative_divergence,
    detect_outliers,
    forecast_completion,
    identify_risks,
    suggest_mitigations,
)

logger = logging.getLogger(__name__)

TOOLS: list[Tool] = [
    Tool(
        name="identify_risks",
        description="Identify project risks using AI-powered risk engine across schedule, cost, resource, scope, technical, and external dimensions",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "focus_areas": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["schedule", "cost", "resource", "scope", "technical", "external", "organizational", "stakeholder"],
                    },
                    "description": "Optional list of risk categories to focus on (analyzes all if omitted)",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "default": "standard",
                    "description": "Analysis depth (quick: basic, standard: normal, deep: comprehensive with dependency chains)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="forecast_completion",
        description="Forecast project completion date using multiple methods (EVM, Monte Carlo, Reference Class, ML Ensemble) with confidence intervals",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "method": {
                    "type": "string",
                    "enum": ["earned_value", "monte_carlo", "reference_class", "simple_extrapolation", "ml_ensemble"],
                    "default": "ml_ensemble",
                    "description": "Forecasting method to use (ml_ensemble combines all methods)",
                },
                "confidence_level": {
                    "type": "number",
                    "minimum": 0.50,
                    "maximum": 0.95,
                    "default": 0.80,
                    "description": "Confidence level for prediction interval (0.50-0.95)",
                },
                "scenarios": {
                    "type": "boolean",
                    "default": True,
                    "description": "Generate optimistic/likely/pessimistic scenario forecasts",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "default": "standard",
                    "description": "Analysis depth (affects Monte Carlo iteration count)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="detect_outliers",
        description="Detect anomalies in task data across duration, progress, float, and dates using statistical analysis",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "sensitivity": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 2.0,
                    "default": 1.0,
                    "description": "Detection sensitivity (0.5: less sensitive, 2.0: more sensitive)",
                },
                "focus_areas": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["duration", "progress", "float", "dates"],
                    },
                    "description": "Optional list of areas to check (checks all if omitted)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="assess_health",
        description="Assess multi-dimensional project health across schedule, cost, scope, resource, and quality dimensions with weighted scoring",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "include_trends": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include trend analysis (improving/stable/declining)",
                },
                "weights": {
                    "type": "object",
                    "properties": {
                        "schedule": {"type": "number", "minimum": 0, "maximum": 1},
                        "cost": {"type": "number", "minimum": 0, "maximum": 1},
                        "scope": {"type": "number", "minimum": 0, "maximum": 1},
                        "resource": {"type": "number", "minimum": 0, "maximum": 1},
                        "quality": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "description": "Optional custom weights for dimensions (must sum to 1.0, default: equal weights 0.2 each)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="suggest_mitigations",
        description="Generate AI-powered mitigation strategies for identified risks with effectiveness ratings and implementation steps",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "risk_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific risk IDs to generate mitigations for (from identify_risks)",
                },
                "focus_areas": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["schedule", "cost", "resource", "scope", "technical", "external"],
                    },
                    "description": "Optional list of risk categories to focus on",
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "default": "standard",
                    "description": "Analysis depth for risk identification before mitigation",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="compare_baseline",
        description="Compare current project state against baseline to identify schedule, duration, and cost variances with severity classification",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier from load_project",
                },
                "baseline_type": {
                    "type": "string",
                    "enum": ["current", "original", "approved"],
                    "default": "current",
                    "description": "Type of baseline to compare against",
                },
                "threshold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 0,
                    "description": "Minimum variance percentage to report (0: all variances, higher: filter small changes)",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="detect_narrative_divergence",
        description=(
            "Compare a written project narrative against quantitative assurance data to detect "
            "optimism bias and misrepresentation. Uses AI to identify specific factual claims "
            "in the narrative and classify each as SUPPORTED, CONTRADICTED, or UNVERIFIABLE "
            "against stored risks, gate readiness, financial data, benefits, and change pressure. "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier — used to look up quantitative data in the AssuranceStore",
                },
                "narrative_text": {
                    "type": "string",
                    "description": "The written project narrative or status update to analyse for divergences",
                },
                "confidence_threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                    "description": "Minimum AI confidence (0.0–1.0) required to include a contradiction in the flags list (default: 0.7)",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite AssuranceStore. Defaults to ~/.pm_data_tools/store.db",
                },
            },
            "required": ["project_id", "narrative_text"],
        },
    ),
]

_TOOL_NAMES = {t.name for t in TOOLS}


async def dispatch(name: str, arguments: Any) -> list[TextContent]:
    """Dispatch a pm-analyse tool call and return normalised TextContent."""
    try:
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
        elif name == "detect_narrative_divergence":
            result = await detect_narrative_divergence(arguments)
        else:
            result = {"error": {"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {name}"}}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as exc:
        logger.error("Error executing tool %s: %s", name, exc, exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": {"code": "TOOL_EXECUTION_ERROR", "message": str(exc)}}, indent=2))]
