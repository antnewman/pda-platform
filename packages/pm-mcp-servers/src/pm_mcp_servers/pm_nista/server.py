"""PM NISTA MCP Server.

Provides MCP tools for NISTA integration including GMPP report generation,
AI narrative generation, and quarterly return submission.
"""

import asyncio
import os
import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from pm_data_tools import parse_project
from pm_data_tools.gmpp import GMPPDataAggregator, NarrativeGenerator
from pm_data_tools.integrations.nista import NISTAAuthClient, NISTAAPIClient, NISTAAuthConfig

app = Server("pm-nista-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available NISTA integration tools."""
    return [
        Tool(
            name="generate_gmpp_report",
            description="Generate complete GMPP quarterly report from project data file",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_file": {
                        "type": "string",
                        "description": "Path to project file (MS Project, GMPP CSV, etc.)"
                    },
                    "quarter": {
                        "type": "string",
                        "enum": ["Q1", "Q2", "Q3", "Q4"],
                        "description": "Quarter period (Q1-Q4)"
                    },
                    "financial_year": {
                        "type": "string",
                        "pattern": "^\\d{4}-\\d{2}$",
                        "description": "Financial year (format: 2025-26)"
                    },
                    "generate_narratives": {
                        "type": "boolean",
                        "description": "Generate AI narratives (requires ANTHROPIC_API_KEY)",
                        "default": True
                    }
                },
                "required": ["project_file", "quarter", "financial_year"]
            }
        ),
        Tool(
            name="generate_narrative",
            description="Generate AI-powered narrative with confidence scoring",
            inputSchema={
                "type": "object",
                "properties": {
                    "narrative_type": {
                        "type": "string",
                        "enum": ["dca", "cost", "schedule", "benefits", "risk"],
                        "description": "Type of narrative to generate"
                    },
                    "project_context": {
                        "type": "object",
                        "description": "Project context data (project_name, dca_rating, costs, etc.)",
                        "properties": {
                            "project_name": {"type": "string"},
                            "department": {"type": "string"},
                            "dca_rating": {"type": "string"},
                            "baseline_cost": {"type": "number"},
                            "forecast_cost": {"type": "number"},
                            "cost_variance_percent": {"type": "number"}
                        },
                        "required": ["project_name"]
                    }
                },
                "required": ["narrative_type", "project_context"]
            }
        ),
        Tool(
            name="submit_to_nista",
            description="Submit GMPP quarterly return to NISTA API (sandbox or production)",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_file": {
                        "type": "string",
                        "description": "Path to quarterly report JSON file"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["sandbox", "production"],
                        "description": "NISTA environment",
                        "default": "sandbox"
                    }
                },
                "required": ["report_file", "project_id"]
            }
        ),
        Tool(
            name="fetch_nista_metadata",
            description="Fetch project metadata from NISTA master registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "NISTA project code or internal project ID"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["sandbox", "production"],
                        "description": "NISTA environment",
                        "default": "sandbox"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="validate_gmpp_report",
            description="Validate GMPP quarterly report against NISTA requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_file": {
                        "type": "string",
                        "description": "Path to quarterly report JSON file"
                    },
                    "strictness": {
                        "type": "string",
                        "enum": ["LENIENT", "STANDARD", "STRICT"],
                        "description": "Validation strictness level",
                        "default": "STANDARD"
                    }
                },
                "required": ["report_file"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""

    if name == "generate_gmpp_report":
        return await _generate_gmpp_report(arguments)

    elif name == "generate_narrative":
        return await _generate_narrative(arguments)

    elif name == "submit_to_nista":
        return await _submit_to_nista(arguments)

    elif name == "fetch_nista_metadata":
        return await _fetch_nista_metadata(arguments)

    elif name == "validate_gmpp_report":
        return await _validate_gmpp_report(arguments)

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _generate_gmpp_report(arguments: dict) -> list[TextContent]:
    """Generate complete GMPP quarterly report."""
    try:
        project_file = arguments["project_file"]
        quarter = arguments["quarter"]
        financial_year = arguments["financial_year"]
        generate_narratives = arguments.get("generate_narratives", True)

        # Parse project file
        project = parse_project(project_file)

        # Get API key for narrative generation
        api_key = os.getenv("ANTHROPIC_API_KEY") if generate_narratives else None

        # Generate report
        aggregator = GMPPDataAggregator(api_key=api_key)
        report = await aggregator.aggregate_quarterly_report(
            project=project,
            quarter=quarter,
            financial_year=financial_year,
            generate_narratives=generate_narratives
        )

        # Format output
        output = {
            "success": True,
            "report": report.model_dump(mode="json"),
            "summary": {
                "project_name": report.project_name,
                "quarter": report.quarter,
                "dca_rating": report.dca_rating,
                "dca_narrative_confidence": report.dca_narrative.confidence,
                "review_level": report.dca_narrative.review_level,
                "missing_fields": report.missing_fields,
                "validation_warnings": report.validation_warnings
            }
        }

        return [TextContent(
            type="text",
            text=f"GMPP Quarterly Report Generated Successfully\n\n{json.dumps(output, indent=2, default=str)}"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error generating GMPP report: {str(e)}"
        )]


async def _generate_narrative(arguments: dict) -> list[TextContent]:
    """Generate AI-powered narrative with confidence scoring."""
    try:
        narrative_type = arguments["narrative_type"]
        project_context = arguments["project_context"]

        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return [TextContent(
                type="text",
                text="Error: ANTHROPIC_API_KEY environment variable not set"
            )]

        # Initialize generator
        generator = NarrativeGenerator(api_key)

        # Generate narrative based on type
        if narrative_type == "dca":
            dca_rating = project_context.get("dca_rating", "AMBER")
            narrative = await generator.generate_dca_narrative(project_context, dca_rating)
        elif narrative_type == "cost":
            narrative = await generator.generate_cost_narrative(project_context)
        elif narrative_type == "schedule":
            narrative = await generator.generate_schedule_narrative(project_context)
        elif narrative_type == "benefits":
            narrative = await generator.generate_benefits_narrative(project_context)
        elif narrative_type == "risk":
            narrative = await generator.generate_risk_narrative(project_context)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown narrative type: {narrative_type}"
            )]

        # Format output
        output = f"""
Narrative Type: {narrative_type.upper()}
Confidence: {narrative.confidence:.2%}
Review Level: {narrative.review_level}
Samples Used: {narrative.samples_used}
{f'Review Reason: {narrative.review_reason}' if narrative.review_reason else ''}

Generated Narrative:
{narrative.text}

---
Generated at: {narrative.generated_at.isoformat()}
"""

        return [TextContent(type="text", text=output.strip())]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error generating narrative: {str(e)}"
        )]


async def _submit_to_nista(arguments: dict) -> list[TextContent]:
    """Submit quarterly return to NISTA API."""
    try:
        report_file = arguments["report_file"]
        project_id = arguments["project_id"]
        environment = arguments.get("environment", "sandbox")

        # Load report
        with open(report_file, "r") as f:
            report_data = json.load(f)

        from pm_data_tools.gmpp.models import QuarterlyReport
        report = QuarterlyReport(**report_data)

        # Configure authentication
        try:
            config = NISTAAuthConfig.from_env()
            config.environment = environment
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"NISTA authentication not configured: {str(e)}\n\n"
                     "Please set environment variables:\n"
                     "- NISTA_CLIENT_ID\n"
                     "- NISTA_CLIENT_SECRET\n"
                     "- NISTA_CERT_PATH (optional for mTLS)\n"
                     "- NISTA_KEY_PATH (optional for mTLS)"
            )]

        # Initialize clients
        auth = NISTAAuthClient(config)
        client = NISTAAPIClient(auth)

        # Submit
        result = await client.submit_quarterly_return(project_id, report)

        # Format output
        if result.success:
            output = f"""
Submission Successful!

Submission ID: {result.submission_id}
Timestamp: {result.timestamp.isoformat()}
Environment: {environment}

{f'Validation Warnings: {len(result.validation_warnings)}' if result.validation_warnings else 'No warnings'}
{chr(10).join(f'- {w}' for w in result.validation_warnings) if result.validation_warnings else ''}
"""
        else:
            output = f"""
Submission Failed

Error: {result.error}
Timestamp: {result.timestamp.isoformat()}
Environment: {environment}

{f'Details: {json.dumps(result.details, indent=2)}' if result.details else ''}
"""

        await auth.close()
        await client.close()

        return [TextContent(type="text", text=output.strip())]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error submitting to NISTA: {str(e)}"
        )]


async def _fetch_nista_metadata(arguments: dict) -> list[TextContent]:
    """Fetch project metadata from NISTA."""
    try:
        project_id = arguments["project_id"]
        environment = arguments.get("environment", "sandbox")

        # Configure authentication
        try:
            config = NISTAAuthConfig.from_env()
            config.environment = environment
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"NISTA authentication not configured: {str(e)}"
            )]

        # Initialize clients
        auth = NISTAAuthClient(config)
        client = NISTAAPIClient(auth)

        # Fetch metadata
        metadata = await client.fetch_project_metadata(project_id)

        # Format output
        output = f"""
Project Metadata from NISTA ({environment}):

NISTA Project Code: {metadata.nista_project_code}
Project Name: {metadata.project_name}
Department: {metadata.department}
Category: {metadata.category}

Senior Responsible Owner:
  Name: {metadata.sro_name}
  Email: {metadata.sro_email}

Timeline:
  Start Date: {metadata.start_date}
  Baseline Completion: {metadata.baseline_completion}

Last Updated: {metadata.last_updated.isoformat()}
"""

        await auth.close()
        await client.close()

        return [TextContent(type="text", text=output.strip())]

    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"Project not found: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error fetching metadata: {str(e)}"
        )]


async def _validate_gmpp_report(arguments: dict) -> list[TextContent]:
    """Validate GMPP quarterly report."""
    try:
        report_file = arguments["report_file"]
        strictness = arguments.get("strictness", "STANDARD")

        # Load report
        with open(report_file, "r") as f:
            report_data = json.load(f)

        # Validate using NISTA validator
        from pm_data_tools.schemas.nista import NISTAValidator, StrictnessLevel

        validator = NISTAValidator(strictness=StrictnessLevel[strictness])
        result = validator.validate(report_data)

        # Format output
        if result.compliant:
            output = f"""
Validation Passed ✓

Compliance Score: {result.compliance_score:.1f}%
Strictness Level: {strictness}

{f'Warnings: {len(result.issues)}' if result.issues else 'No warnings'}
{chr(10).join(f'- {issue.message}' for issue in result.issues if issue.severity == 'warning') if result.issues else ''}
"""
        else:
            output = f"""
Validation Failed ✗

Compliance Score: {result.compliance_score:.1f}%
Strictness Level: {strictness}

Missing Required Fields:
{chr(10).join(f'- {field}' for field in result.missing_required_fields)}

{f'Missing Recommended Fields:{chr(10)}{chr(10).join(f"- {field}" for field in result.missing_recommended_fields)}' if result.missing_recommended_fields else ''}

Errors:
{chr(10).join(f'- {issue.message}' for issue in result.issues if issue.severity == 'error')}
"""

        return [TextContent(type="text", text=output.strip())]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error validating report: {str(e)}"
        )]


def main():
    """Run the MCP server."""
    import mcp.server.stdio

    async def arun():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(arun())


if __name__ == "__main__":
    main()
