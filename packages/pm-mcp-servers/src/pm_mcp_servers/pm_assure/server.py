"""PM Assure MCP Server.

Provides MCP tools for the OPAL (Open Project Assurance Library) framework
including longitudinal compliance score trend analysis, review action
lifecycle management, domain classification, assumption drift tracking,
ARMM maturity assessment, and workflow orchestration.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

app = Server("pm-assure-server")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


ASSURE_TOOLS: list[Tool] = [
        Tool(
            name="nista_longitudinal_trend",
            description=(
                "Retrieve NISTA compliance score history, trend direction, and "
                "active threshold breaches for a project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project identifier to query.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": (
                            "Optional path to the SQLite store.  "
                            "Defaults to ~/.pm_data_tools/store.db"
                        ),
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="track_review_actions",
            description=(
                "Extract review actions from project review text, persist "
                "them to the store, and detect any recurrences from prior cycles."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "review_text": {
                        "type": "string",
                        "description": "Full text of the project review document.",
                    },
                    "review_id": {
                        "type": "string",
                        "description": "Unique identifier for this review.",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": (
                            "Confidence threshold below which review actions "
                            "are flagged for human review (default 0.60)."
                        ),
                        "default": 0.60,
                    },
                },
                "required": ["review_text", "review_id", "project_id"],
            },
        ),
        Tool(
            name="review_action_status",
            description=(
                "Retrieve tracked review actions for a project, optionally "
                "filtered by status.  Returns recurrence flags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "status_filter": {
                        "type": "string",
                        "enum": ["OPEN", "IN_PROGRESS", "CLOSED", "RECURRING"],
                        "description": "Optional status to filter by.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="check_artefact_currency",
            description=(
                "Assess whether project artefacts are current against a gate "
                "date.  Detects stale documents and last-minute compliance "
                "updates made suspiciously close to the gate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artefacts": {
                        "type": "array",
                        "description": (
                            "List of artefact descriptors.  Each must have "
                            "``id`` (str), ``type`` (str), and "
                            "``last_modified`` (ISO-8601 string or datetime)."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "last_modified": {"type": "string"},
                            },
                            "required": ["id", "type", "last_modified"],
                        },
                    },
                    "gate_date": {
                        "type": "string",
                        "description": "ISO-8601 gate date to assess currency against.",
                    },
                    "max_staleness_days": {
                        "type": "integer",
                        "description": "Days before gate after which an artefact is OUTDATED (default 90).",
                        "default": 90,
                    },
                    "anomaly_window_days": {
                        "type": "integer",
                        "description": (
                            "Updates this close to the gate date are flagged as "
                            "ANOMALOUS_UPDATE (default 3)."
                        ),
                        "default": 3,
                    },
                },
                "required": ["artefacts", "gate_date"],
            },
        ),
        Tool(
            name="check_confidence_divergence",
            description=(
                "Assess AI extraction confidence for a project review.  "
                "Detects high sample divergence, low consensus, and degrading "
                "confidence trends across review cycles."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "review_id": {
                        "type": "string",
                        "description": "Unique identifier for the review.",
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "Overall consensus confidence score (0–1).",
                    },
                    "sample_scores": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Individual per-sample confidence scores.",
                    },
                    "divergence_threshold": {
                        "type": "number",
                        "description": "Max acceptable sample spread (default 0.20).",
                        "default": 0.20,
                    },
                    "min_consensus": {
                        "type": "number",
                        "description": "Minimum acceptable consensus score (default 0.60).",
                        "default": 0.60,
                    },
                    "db_path": {
                        "type": "string",
                        "description": (
                            "Optional path to the SQLite store.  "
                            "Defaults to ~/.pm_data_tools/store.db"
                        ),
                    },
                },
                "required": ["project_id", "review_id", "confidence_score", "sample_scores"],
            },
        ),
        Tool(
            name="recommend_review_schedule",
            description=(
                "Generate an adaptive review scheduling recommendation for a "
                "project by analysing its P1–P4 assurance signals.  Returns "
                "urgency, recommended date, composite score, and rationale."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "last_review_date": {
                        "type": "string",
                        "description": "ISO-8601 date of the most recent review (optional).",
                    },
                    "artefacts": {
                        "type": "array",
                        "description": (
                            "Optional artefact list for P1 currency check.  "
                            "Each requires ``id``, ``type``, ``last_modified``."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "last_modified": {"type": "string"},
                            },
                            "required": ["id", "type", "last_modified"],
                        },
                    },
                    "gate_date": {
                        "type": "string",
                        "description": "ISO-8601 gate date for the P1 currency check.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": (
                            "Optional path to the SQLite store.  "
                            "Defaults to ~/.pm_data_tools/store.db"
                        ),
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="log_override_decision",
            description=(
                "Log a governance override decision — e.g. proceeding past a "
                "failed gate, dismissing a recommendation, or accepting a risk.  "
                "Captures the full context: authoriser, rationale, conditions, "
                "and evidence references."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "override_type": {
                        "type": "string",
                        "enum": [
                            "GATE_PROGRESSION",
                            "RECOMMENDATION_DISMISSED",
                            "RAG_OVERRIDE",
                            "RISK_ACCEPTANCE",
                            "SCHEDULE_OVERRIDE",
                        ],
                        "description": "Category of the override.",
                    },
                    "decision_date": {
                        "type": "string",
                        "description": "ISO-8601 date of the override decision.",
                    },
                    "authoriser": {
                        "type": "string",
                        "description": "Who authorised the override.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Why the override was approved.",
                    },
                    "overridden_finding_id": {
                        "type": "string",
                        "description": "Optional link to a P3 ReviewAction id, gate, or RAG reference.",
                    },
                    "overridden_value": {
                        "type": "string",
                        "description": "What the assurance advice was (e.g. 'RED').",
                    },
                    "override_value": {
                        "type": "string",
                        "description": "What was decided instead (e.g. 'Proceed with conditions').",
                    },
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Conditions attached to the override.",
                    },
                    "evidence_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Document references supporting the decision.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": [
                    "project_id",
                    "override_type",
                    "decision_date",
                    "authoriser",
                    "rationale",
                ],
            },
        ),
        Tool(
            name="analyse_override_patterns",
            description=(
                "Analyse the governance override history for a project.  "
                "Returns total overrides, breakdown by type and outcome, "
                "impact rate, and top authorisers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="ingest_lesson",
            description=(
                "Ingest a structured lessons learned record into the knowledge "
                "base.  Captures category, sentiment, project type, phase, tags, "
                "and impact description for later search and analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Identifier of the source project.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Short summary of the lesson.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Full lesson narrative.",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "GOVERNANCE",
                            "TECHNICAL",
                            "COMMERCIAL",
                            "STAKEHOLDER",
                            "RESOURCE",
                            "REQUIREMENTS",
                            "ESTIMATION",
                            "RISK_MANAGEMENT",
                            "BENEFITS_REALISATION",
                            "OTHER",
                        ],
                        "description": "Domain classification for the lesson.",
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["POSITIVE", "NEGATIVE"],
                        "description": "Whether this is a positive or negative lesson.",
                    },
                    "project_type": {
                        "type": "string",
                        "description": "Optional project type (e.g. 'ICT', 'Infrastructure').",
                    },
                    "project_phase": {
                        "type": "string",
                        "description": "Optional project phase (e.g. 'Initiation', 'Delivery').",
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional originating department.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Free-form tags for keyword discovery.",
                    },
                    "recorded_by": {
                        "type": "string",
                        "description": "Name or role of the person recording the lesson.",
                    },
                    "impact_description": {
                        "type": "string",
                        "description": "What happened as a result of this lesson.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "title", "description", "category", "sentiment"],
            },
        ),
        Tool(
            name="search_lessons",
            description=(
                "Search the lessons learned corpus by free-text query.  "
                "Uses semantic search when sentence-transformers is available, "
                "otherwise falls back to keyword matching.  Supports filtering "
                "by project type, category, and sentiment."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free-text search query.",
                    },
                    "project_type": {
                        "type": "string",
                        "description": "Optional project type filter.",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "GOVERNANCE",
                            "TECHNICAL",
                            "COMMERCIAL",
                            "STAKEHOLDER",
                            "RESOURCE",
                            "REQUIREMENTS",
                            "ESTIMATION",
                            "RISK_MANAGEMENT",
                            "BENEFITS_REALISATION",
                            "OTHER",
                        ],
                        "description": "Optional category filter.",
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["POSITIVE", "NEGATIVE"],
                        "description": "Optional sentiment filter.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 10).",
                        "default": 10,
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="log_assurance_activity",
            description=(
                "Log an assurance activity with effort tracking.  Records "
                "person-hours, participants, artefacts reviewed, findings "
                "produced, and before/after compliance scores."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "activity_type": {
                        "type": "string",
                        "enum": [
                            "GATE_REVIEW",
                            "DOCUMENT_REVIEW",
                            "COMPLIANCE_CHECK",
                            "RISK_ASSESSMENT",
                            "STAKEHOLDER_REVIEW",
                            "AUDIT",
                            "OTHER",
                        ],
                        "description": "Classification of the activity.",
                    },
                    "description": {
                        "type": "string",
                        "description": "What was done.",
                    },
                    "date": {
                        "type": "string",
                        "description": "ISO-8601 date of the activity.",
                    },
                    "effort_hours": {
                        "type": "number",
                        "description": "Person-hours spent on this activity.",
                    },
                    "participants": {
                        "type": "integer",
                        "description": "Number of people involved (default 1).",
                        "default": 1,
                    },
                    "artefacts_reviewed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Artefact IDs checked during this activity.",
                    },
                    "findings_count": {
                        "type": "integer",
                        "description": "Number of findings or actions produced.",
                        "default": 0,
                    },
                    "confidence_before": {
                        "type": "number",
                        "description": "NISTA compliance score before the activity (0–100).",
                    },
                    "confidence_after": {
                        "type": "number",
                        "description": "NISTA compliance score after the activity (0–100).",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": [
                    "project_id",
                    "activity_type",
                    "description",
                    "date",
                    "effort_hours",
                ],
            },
        ),
        Tool(
            name="analyse_assurance_overhead",
            description=(
                "Run a complete assurance overhead analysis for a project.  "
                "Computes effort metrics, finding rates, duplicate checks, "
                "efficiency rating, and human-readable optimisation "
                "recommendations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="run_assurance_workflow",
            description=(
                "Run a multi-step assurance workflow for a project.  "
                "Orchestrates P1–P8 steps deterministically, computes overall "
                "project health (HEALTHY / ATTENTION_NEEDED / AT_RISK / CRITICAL), "
                "and returns aggregated risk signals, recommended actions, and "
                "an executive summary.  Five workflow types available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "workflow_type": {
                        "type": "string",
                        "enum": [
                            "FULL_ASSURANCE",
                            "COMPLIANCE_FOCUS",
                            "CURRENCY_FOCUS",
                            "TREND_ANALYSIS",
                            "RISK_ASSESSMENT",
                        ],
                        "description": "Which workflow plan to execute.",
                    },
                    "artefacts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "last_modified": {"type": "string"},
                            },
                            "required": ["id", "type", "last_modified"],
                        },
                        "description": (
                            "Optional artefact list for P1 currency check.  "
                            "Each item must have 'id', 'type', and "
                            "'last_modified' (ISO-8601 datetime string)."
                        ),
                    },
                    "gate_date": {
                        "type": "string",
                        "description": (
                            "Optional ISO-8601 gate date for P1 currency check.  "
                            "Required when artefacts is provided."
                        ),
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "workflow_type"],
            },
        ),
        Tool(
            name="get_workflow_history",
            description=(
                "Retrieve the assurance workflow execution history for a project.  "
                "Returns all past workflow results ordered by start time ascending."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="classify_project_domain",
            description=(
                "Classify a project into a complexity domain (CLEAR / COMPLICATED / "
                "COMPLEX / CHAOTIC) using up to seven explicit indicators and "
                "store-derived signals from P2, P3, P6, and P8.  Returns the "
                "domain, composite score, and a tailored assurance profile."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "technical_complexity": {
                        "type": "number",
                        "description": "Technical novelty and integration complexity (0–1).",
                    },
                    "stakeholder_complexity": {
                        "type": "number",
                        "description": "Breadth and diversity of stakeholders (0–1).",
                    },
                    "requirement_clarity": {
                        "type": "number",
                        "description": (
                            "How well-defined requirements are (0–1; high = clearer, "
                            "inverted internally)."
                        ),
                    },
                    "delivery_track_record": {
                        "type": "number",
                        "description": (
                            "Team's prior delivery success rate (0–1; high = better, "
                            "inverted internally)."
                        ),
                    },
                    "organisational_change": {
                        "type": "number",
                        "description": "Degree of organisational change required (0–1).",
                    },
                    "regulatory_exposure": {
                        "type": "number",
                        "description": "Level of regulatory or compliance risk (0–1).",
                    },
                    "dependency_count": {
                        "type": "number",
                        "description": "Normalised count of external dependencies (0–1).",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional free-text notes about this classification.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="reclassify_from_store",
            description=(
                "Reclassify a project's complexity domain using only store-derived "
                "signals (P2 trend, P3 open actions, P6 override rate, P8 efficiency).  "
                "No explicit indicators required.  Useful for automated or scheduled "
                "reclassification."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="ingest_assumption",
            description=(
                "Ingest a project assumption with its baseline value into the "
                "assumption tracker.  Supports cost, schedule, resource, technical, "
                "commercial, regulatory, stakeholder, and external assumption types."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project identifier."},
                    "text": {"type": "string", "description": "Human-readable assumption statement."},
                    "category": {
                        "type": "string",
                        "enum": ["COST", "SCHEDULE", "RESOURCE", "TECHNICAL", "COMMERCIAL", "REGULATORY", "STAKEHOLDER", "EXTERNAL"],
                        "description": "Assumption category.",
                    },
                    "baseline_value": {"type": "number", "description": "The original assumed value."},
                    "unit": {"type": "string", "description": "Measurement unit (e.g. '%', 'GBP', 'days')."},
                    "tolerance_pct": {"type": "number", "description": "Acceptable drift percentage (default 10)."},
                    "source": {
                        "type": "string",
                        "enum": ["MANUAL", "EXTERNAL_API", "DERIVED"],
                        "description": "Source of the assumption value.",
                    },
                    "external_ref": {"type": "string", "description": "External data source identifier (e.g. 'ONS_CPI')."},
                    "owner": {"type": "string", "description": "Name or role responsible for this assumption."},
                    "notes": {"type": "string", "description": "Optional free-text notes."},
                    "db_path": {"type": "string", "description": "Optional path to the SQLite store."},
                },
                "required": ["project_id", "text", "category", "baseline_value"],
            },
        ),
        Tool(
            name="validate_assumption",
            description=(
                "Update an assumption's current value, record the validation, "
                "and compute drift against the baseline.  Returns drift percentage "
                "and severity classification."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "assumption_id": {"type": "string", "description": "UUID of the assumption to update."},
                    "new_value": {"type": "number", "description": "The updated current value."},
                    "source": {
                        "type": "string",
                        "enum": ["MANUAL", "EXTERNAL_API", "DERIVED"],
                        "description": "Source of the new value (default MANUAL).",
                    },
                    "notes": {"type": "string", "description": "Optional notes about this update."},
                    "db_path": {"type": "string", "description": "Optional path to the SQLite store."},
                },
                "required": ["assumption_id", "new_value"],
            },
        ),
        Tool(
            name="get_assumption_drift",
            description=(
                "Run a full assumption health analysis for a project.  "
                "Returns drift status for all assumptions, stale count, "
                "cascade warnings, and an overall drift score (0–1)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project identifier."},
                    "db_path": {"type": "string", "description": "Optional path to the SQLite store."},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="get_cascade_impact",
            description=(
                "Find all assumptions that depend on the given assumption "
                "(direct and transitive).  Returns affected assumption IDs "
                "with their texts and current drift status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "assumption_id": {"type": "string", "description": "UUID of the source assumption."},
                    "db_path": {"type": "string", "description": "Optional path to the SQLite store."},
                },
                "required": ["assumption_id"],
            },
        ),
        # =================================================================
        # Hackathon tools: project creation + dashboard export
        # =================================================================
        Tool(
            name="create_project_from_profile",
            description=(
                "Create a full OPAL assurance project from a Claude-extracted PDF profile.  "
                "Generates 12 months of OPAL-1 to OPAL-12 data (compliance scores, review "
                "actions, divergence snapshots, schedule recommendations, overrides, activities, "
                "assumptions, ARMM assessments, workflow executions, domain classification) "
                "calibrated to the project's complexity domain and indicators.  "
                "Returns the project_id and an executive summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Desired project identifier (e.g. 'PROJ-HACKATHON-001').",
                    },
                    "name": {
                        "type": "string",
                        "description": "Project name.",
                    },
                    "department": {
                        "type": "string",
                        "description": "UK government department.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Project category (ICT, Digital, Infrastructure, etc.).",
                    },
                    "domain": {
                        "type": "string",
                        "enum": ["CLEAR", "COMPLICATED", "COMPLEX", "CHAOTIC"],
                        "description": "Cynefin complexity domain.",
                    },
                    "sro": {
                        "type": "string",
                        "description": "Senior Responsible Owner title.",
                    },
                    "technical_complexity": {
                        "type": "number",
                        "description": "0.0–1.0 technical complexity indicator.",
                    },
                    "stakeholder_complexity": {
                        "type": "number",
                        "description": "0.0–1.0 stakeholder complexity.",
                    },
                    "requirement_clarity": {
                        "type": "number",
                        "description": "0.0–1.0 requirement clarity (1 = very clear).",
                    },
                    "delivery_track_record": {
                        "type": "number",
                        "description": "0.0–1.0 prior delivery success rate.",
                    },
                    "organisational_change": {
                        "type": "number",
                        "description": "0.0–1.0 degree of org change required.",
                    },
                    "regulatory_exposure": {
                        "type": "number",
                        "description": "0.0–1.0 regulatory/compliance risk.",
                    },
                    "dependency_count": {
                        "type": "number",
                        "description": "0.0–1.0 normalised dependency count.",
                    },
                    "whole_life_cost_m": {
                        "type": "number",
                        "description": "Whole life cost in GBP millions.",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Executive summary of the project.",
                    },
                    "key_risks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key risks identified from the document.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "name", "department", "domain"],
            },
        ),
        Tool(
            name="export_dashboard_data",
            description=(
                "Export all assurance data for a project as a static JSON file "
                "that the UDS Renderer can consume directly.  The JSON maps panel "
                "IDs to their data payloads (value, rows, text).  Write to a "
                "specified output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": (
                            "Directory to write the JSON file to "
                            "(e.g. path to uds-renderer/public/data)."
                        ),
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "output_dir"],
            },
        ),
        Tool(
            name="export_dashboard_html",
            description=(
                "Generate a self-contained HTML dashboard file for a project.  "
                "The HTML includes Tailwind CSS, Chart.js, and Inter font via CDN, "
                "all data embedded inline, TortoiseAI branding, and works offline.  "
                "Can be emailed, deployed, or printed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Human-readable project name.",
                    },
                    "department": {
                        "type": "string",
                        "description": "Government department.",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Complexity domain.",
                    },
                    "key_risks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key risks from the document.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": (
                            "Directory to save the HTML file.  "
                            "Defaults to ~/Desktop/pda-dashboards/."
                        ),
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "project_name"],
            },
        ),
        Tool(
            name="get_armm_report",
            description=(
                "Retrieve the ARMM (Agent Readiness Maturity Model) report for a project.  "
                "Returns overall maturity level (0-4), score percentage, criteria met/total, "
                "dimension breakdown (TC, OR, GA, CC), topic scores, blocking topics, "
                "and improvement priorities.  251 criteria across 28 topics and 4 dimensions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "include_criteria": {
                        "type": "boolean",
                        "description": "Include individual criterion results (251 items). Default false.",
                        "default": False,
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        # P14 — Gate Readiness Assessor
        Tool(
            name="assess_gate_readiness",
            description=(
                "Run a full gate readiness assessment synthesising data from all "
                "assurance modules (P1-P12). Returns a composite readiness score "
                "(0.0-1.0), 8-dimension breakdown with gate-specific weighting, "
                "blocking issues, and prioritised recommendations. Supports all "
                "7 IPA review points (Gate 0-5 + PAR)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "gate": {
                        "type": "string",
                        "enum": [
                            "GATE_0", "GATE_1", "GATE_2", "GATE_3",
                            "GATE_4", "GATE_5", "PAR",
                        ],
                        "description": (
                            "IPA gate to assess for. GATE_0=Opportunity Framing, "
                            "GATE_1=SOC, GATE_2=OBC, GATE_3=FBC, "
                            "GATE_4=Readiness for Service, GATE_5=Operations Review, "
                            "PAR=Project Assessment Review."
                        ),
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id", "gate"],
            },
        ),
        Tool(
            name="get_gate_readiness_history",
            description=(
                "Retrieve past gate readiness assessments for a project to show "
                "progression over time. Optionally filter by gate type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier.",
                    },
                    "gate": {
                        "type": "string",
                        "enum": [
                            "GATE_0", "GATE_1", "GATE_2", "GATE_3",
                            "GATE_4", "GATE_5", "PAR",
                        ],
                        "description": "Optional gate filter.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="compare_gate_readiness",
            description=(
                "Compare two gate readiness assessments to show improvement or "
                "regression. Returns score delta, improved/degraded dimensions, "
                "and resolved/new blocking issues."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "assessment_id_before": {
                        "type": "string",
                        "description": "ID of the earlier assessment.",
                    },
                    "assessment_id_after": {
                        "type": "string",
                        "description": "ID of the later assessment.",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["assessment_id_before", "assessment_id_after"],
            },
        ),
        Tool(
            name="scan_for_red_flags",
            description=(
                "Cross-module red flag scanner. Queries risks, benefits, gate "
                "readiness, financials, change requests, and resources in a single "
                "pass and returns a prioritised alert list. Replaces the need to "
                "run 10+ individual tools for a full project health picture."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The project identifier to scan.",
                    },
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM"],
                        "description": (
                            "Only return flags at or above this severity level. "
                            "CRITICAL returns critical only; HIGH returns critical "
                            "and high; MEDIUM returns all flags. Default: MEDIUM."
                        ),
                        "default": "MEDIUM",
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Optional path to the SQLite store.",
                    },
                },
                "required": ["project_id"],
            },
        ),
    ]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available PM Assure tools."""
    return ASSURE_TOOLS


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution."""
    if name == "nista_longitudinal_trend":
        return await _nista_longitudinal_trend(arguments)
    if name == "track_review_actions":
        return await _track_review_actions(arguments)
    if name == "review_action_status":
        return await _review_action_status(arguments)
    if name == "check_artefact_currency":
        return await _check_artefact_currency(arguments)
    if name == "check_confidence_divergence":
        return await _check_confidence_divergence(arguments)
    if name == "recommend_review_schedule":
        return await _recommend_review_schedule(arguments)
    if name == "log_override_decision":
        return await _log_override_decision(arguments)
    if name == "analyse_override_patterns":
        return await _analyse_override_patterns(arguments)
    if name == "ingest_lesson":
        return await _ingest_lesson(arguments)
    if name == "search_lessons":
        return await _search_lessons(arguments)
    if name == "log_assurance_activity":
        return await _log_assurance_activity(arguments)
    if name == "analyse_assurance_overhead":
        return await _analyse_assurance_overhead(arguments)
    if name == "run_assurance_workflow":
        return await _run_assurance_workflow(arguments)
    if name == "get_workflow_history":
        return await _get_workflow_history(arguments)
    if name == "classify_project_domain":
        return await _classify_project_domain(arguments)
    if name == "reclassify_from_store":
        return await _reclassify_from_store(arguments)
    if name == "ingest_assumption":
        return await _ingest_assumption(arguments)
    if name == "validate_assumption":
        return await _validate_assumption(arguments)
    if name == "get_assumption_drift":
        return await _get_assumption_drift(arguments)
    if name == "get_cascade_impact":
        return await _get_cascade_impact(arguments)
    if name == "create_project_from_profile":
        return await _create_project_from_profile(arguments)
    if name == "export_dashboard_data":
        return await _export_dashboard_data(arguments)
    if name == "export_dashboard_html":
        return await _export_dashboard_html(arguments)
    if name == "get_armm_report":
        return await _get_armm_report(arguments)
    if name == "assess_gate_readiness":
        return await _assess_gate_readiness(arguments)
    if name == "get_gate_readiness_history":
        return await _get_gate_readiness_history(arguments)
    if name == "compare_gate_readiness":
        return await _compare_gate_readiness(arguments)
    if name == "scan_for_red_flags":
        return await _scan_for_red_flags(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------


async def _nista_longitudinal_trend(arguments: dict[str, Any]) -> list[TextContent]:
    """Return compliance score history, trend, and active breaches."""
    try:
        from pm_data_tools.db.store import AssuranceStore
        from pm_data_tools.schemas.nista.longitudinal import LongitudinalComplianceTracker

        project_id: str = arguments["project_id"]
        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None

        store = AssuranceStore(db_path=db_path)
        tracker = LongitudinalComplianceTracker(store=store)

        records = tracker.get_history(project_id)
        trend = tracker.compute_trend(project_id)
        breaches = tracker.check_thresholds(project_id)

        output: dict[str, Any] = {
            "project_id": project_id,
            "history": [
                {
                    "run_id": r.run_id,
                    "timestamp": r.timestamp.isoformat(),
                    "score": r.score,
                    "dimension_scores": r.dimension_scores,
                }
                for r in records
            ],
            "trend": trend.value,
            "active_breaches": [
                {
                    "breach_type": b.breach_type,
                    "current_score": b.current_score,
                    "previous_score": b.previous_score,
                    "threshold_value": b.threshold_value,
                    "message": b.message,
                }
                for b in breaches
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _track_review_actions(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Extract and persist review actions from project review text."""
    try:
        import anthropic as _anthropic_module  # noqa: F401 — import check
        from agent_planning.confidence import ConfidenceExtractor
        from agent_planning.providers.anthropic import AnthropicProvider
        from pm_data_tools.assurance import FindingAnalyzer

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return [
                TextContent(
                    type="text",
                    text="Error: ANTHROPIC_API_KEY environment variable not set.",
                )
            ]

        provider = AnthropicProvider(api_key=api_key)
        ce = ConfidenceExtractor(provider)

        analyzer = FindingAnalyzer(
            extractor=ce,
            min_confidence=float(arguments.get("min_confidence", 0.60)),
        )

        result = await analyzer.extract(
            review_text=arguments["review_text"],
            review_id=arguments["review_id"],
            project_id=arguments["project_id"],
        )

        output: dict[str, Any] = {
            "extraction_confidence": result.extraction_confidence,
            "review_level": result.review_level,
            "cost_usd": result.cost_usd,
            "review_actions": [
                {
                    "id": r.id,
                    "text": r.text,
                    "category": r.category,
                    "status": r.status.value,
                    "owner": r.owner,
                    "confidence": r.confidence,
                    "flagged_for_review": r.flagged_for_review,
                    "recurrence_of": r.recurrence_of,
                }
                for r in result.recommendations
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _review_action_status(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Return current review actions for a project."""
    try:
        from pm_data_tools.db.store import AssuranceStore

        project_id: str = arguments["project_id"]
        status_filter: str | None = arguments.get("status_filter")

        store = AssuranceStore()
        rows = store.get_recommendations(
            project_id=project_id,
            status_filter=status_filter,
        )

        output: dict[str, Any] = {
            "project_id": project_id,
            "status_filter": status_filter,
            "count": len(rows),
            "review_actions": rows,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _recommend_review_schedule(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Generate an adaptive review scheduling recommendation."""
    try:
        from datetime import date, datetime, timezone
        from pathlib import Path

        from pm_data_tools.assurance.currency import ArtefactCurrencyValidator
        from pm_data_tools.assurance.divergence import (
            DivergenceResult,
            DivergenceSignal,
            SignalType,
        )
        from pm_data_tools.assurance.scheduler import AdaptiveReviewScheduler
        from pm_data_tools.db.store import AssuranceStore
        from pm_data_tools.schemas.nista.longitudinal import LongitudinalComplianceTracker

        project_id: str = arguments["project_id"]
        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        # Parse optional last_review_date
        last_review_date: date | None = None
        raw_lrd = arguments.get("last_review_date")
        if raw_lrd:
            last_review_date = date.fromisoformat(str(raw_lrd))

        # P1 — artefact currency
        currency_scores = None
        if arguments.get("artefacts") and arguments.get("gate_date"):
            gate_date = datetime.fromisoformat(str(arguments["gate_date"]))
            if gate_date.tzinfo is None:
                gate_date = gate_date.replace(tzinfo=timezone.utc)
            validator = ArtefactCurrencyValidator()
            currency_scores = validator.check_batch(
                artefacts=arguments["artefacts"],
                gate_date=gate_date,
            )

        # P2 — compliance trend
        tracker = LongitudinalComplianceTracker(store=store)
        trend = tracker.compute_trend(project_id)
        breaches = tracker.check_thresholds(project_id)

        # P3 — review action counts
        all_actions = store.get_recommendations(project_id=project_id)
        total_actions = len(all_actions)
        open_actions = sum(1 for a in all_actions if a.get("status") == "OPEN")
        recurring_actions = sum(
            1 for a in all_actions if a.get("status") == "RECURRING"
        )

        # P4 — latest divergence snapshot
        divergence_result: DivergenceResult | None = None
        snapshots = store.get_divergence_history(project_id)
        if snapshots:
            latest = snapshots[-1]
            sig_type = SignalType(str(latest["signal_type"]))
            divergence_result = DivergenceResult(
                project_id=str(latest["project_id"]),
                review_id=str(latest["review_id"]),
                confidence_score=float(latest["confidence_score"]),  # type: ignore[arg-type]
                sample_scores=latest["sample_scores"],  # type: ignore[arg-type]
                signal=DivergenceSignal(
                    signal_type=sig_type,
                    project_id=str(latest["project_id"]),
                    review_id=str(latest["review_id"]),
                    confidence_score=float(latest["confidence_score"]),  # type: ignore[arg-type]
                    spread=0.0,
                    previous_confidence=None,
                    message="",
                ),
                snapshot_id=str(latest["id"]),
            )

        scheduler = AdaptiveReviewScheduler(store=store)
        rec = scheduler.recommend(
            project_id=project_id,
            last_review_date=last_review_date,
            currency_scores=currency_scores,
            trend=trend,
            breaches=breaches,
            open_actions=open_actions if total_actions > 0 else None,
            total_actions=total_actions if total_actions > 0 else None,
            recurring_actions=recurring_actions if total_actions > 0 else None,
            divergence_result=divergence_result,
        )

        output: dict[str, Any] = {
            "project_id": rec.project_id,
            "urgency": rec.urgency.value,
            "recommended_date": rec.recommended_date.isoformat(),
            "days_until_review": rec.days_until_review,
            "composite_score": rec.composite_score,
            "rationale": rec.rationale,
            "signals": [
                {
                    "source": s.source,
                    "signal_name": s.signal_name,
                    "severity": s.severity,
                    "detail": s.detail,
                }
                for s in rec.signals
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _log_override_decision(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Log a governance override decision."""
    try:
        from datetime import date
        from pathlib import Path

        from pm_data_tools.assurance.overrides import (
            OverrideDecision,
            OverrideDecisionLogger,
            OverrideType,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        decision = OverrideDecision(
            project_id=arguments["project_id"],
            override_type=OverrideType(arguments["override_type"]),
            decision_date=date.fromisoformat(str(arguments["decision_date"])),
            authoriser=arguments["authoriser"],
            rationale=arguments["rationale"],
            overridden_finding_id=arguments.get("overridden_finding_id"),
            overridden_value=arguments.get("overridden_value"),
            override_value=arguments.get("override_value"),
            conditions=list(arguments.get("conditions", [])),
            evidence_refs=list(arguments.get("evidence_refs", [])),
        )

        log_obj = OverrideDecisionLogger(store=store)
        logged = log_obj.log_override(decision)

        output: dict[str, Any] = {
            "id": logged.id,
            "project_id": logged.project_id,
            "override_type": logged.override_type.value,
            "decision_date": logged.decision_date.isoformat(),
            "authoriser": logged.authoriser,
            "outcome": logged.outcome.value,
            "message": f"Override decision logged with id '{logged.id}'.",
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _analyse_override_patterns(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Return override pattern summary for a project."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.overrides import OverrideDecisionLogger
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        project_id: str = arguments["project_id"]
        log_obj = OverrideDecisionLogger(store=store)
        summary = log_obj.analyse_patterns(project_id)

        output: dict[str, Any] = {
            "project_id": summary.project_id,
            "total_overrides": summary.total_overrides,
            "by_type": summary.by_type,
            "by_outcome": summary.by_outcome,
            "pending_outcomes": summary.pending_outcomes,
            "impact_rate": summary.impact_rate,
            "top_authorisers": summary.top_authorisers,
            "message": summary.message,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _check_artefact_currency(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Assess artefact currency against a gate date."""
    try:
        from datetime import datetime, timezone

        from pm_data_tools.assurance.currency import (
            ArtefactCurrencyValidator,
            CurrencyConfig,
        )

        gate_date = datetime.fromisoformat(arguments["gate_date"])
        if gate_date.tzinfo is None:
            gate_date = gate_date.replace(tzinfo=timezone.utc)

        config = CurrencyConfig(
            max_staleness_days=int(arguments.get("max_staleness_days", 90)),
            anomaly_window_days=int(arguments.get("anomaly_window_days", 3)),
        )
        validator = ArtefactCurrencyValidator(config=config)

        results = validator.check_batch(
            artefacts=arguments["artefacts"],
            gate_date=gate_date,
        )

        summary: dict[str, Any] = {
            "gate_date": gate_date.isoformat(),
            "total": len(results),
            "current": sum(1 for r in results if r.status.value == "CURRENT"),
            "outdated": sum(1 for r in results if r.status.value == "OUTDATED"),
            "anomalous_update": sum(
                1 for r in results if r.status.value == "ANOMALOUS_UPDATE"
            ),
            "artefacts": [
                {
                    "artefact_id": r.artefact_id,
                    "artefact_type": r.artefact_type,
                    "status": r.status.value,
                    "staleness_days": r.staleness_days,
                    "anomaly_window_days": r.anomaly_window_days,
                    "message": r.message,
                }
                for r in results
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(summary, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _check_confidence_divergence(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Assess AI confidence divergence for a review."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.divergence import DivergenceConfig, DivergenceMonitor
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        config = DivergenceConfig(
            divergence_threshold=float(arguments.get("divergence_threshold", 0.20)),
            min_consensus=float(arguments.get("min_consensus", 0.60)),
        )
        monitor = DivergenceMonitor(config=config, store=store)

        result = monitor.check(
            project_id=arguments["project_id"],
            review_id=arguments["review_id"],
            confidence_score=float(arguments["confidence_score"]),
            sample_scores=[float(s) for s in arguments["sample_scores"]],
        )

        output: dict[str, Any] = {
            "project_id": result.project_id,
            "review_id": result.review_id,
            "confidence_score": result.confidence_score,
            "sample_scores": result.sample_scores,
            "signal_type": result.signal.signal_type.value,
            "spread": result.signal.spread,
            "previous_confidence": result.signal.previous_confidence,
            "message": result.signal.message,
            "snapshot_id": result.snapshot_id,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _ingest_lesson(arguments: dict[str, Any]) -> list[TextContent]:
    """Ingest a structured lesson into the knowledge base."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.lessons import (
            LessonCategory,
            LessonRecord,
            LessonSentiment,
            LessonsKnowledgeEngine,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        lesson = LessonRecord(
            project_id=arguments["project_id"],
            title=arguments["title"],
            description=arguments["description"],
            category=LessonCategory(arguments["category"]),
            sentiment=LessonSentiment(arguments["sentiment"]),
            project_type=arguments.get("project_type"),
            project_phase=arguments.get("project_phase"),
            department=arguments.get("department"),
            tags=list(arguments.get("tags", [])),
            recorded_by=arguments.get("recorded_by"),
            impact_description=arguments.get("impact_description"),
        )

        engine = LessonsKnowledgeEngine(store=store)
        ingested = engine.ingest(lesson)

        output: dict[str, Any] = {
            "id": ingested.id,
            "project_id": ingested.project_id,
            "title": ingested.title,
            "category": ingested.category.value,
            "sentiment": ingested.sentiment.value,
            "date_recorded": ingested.date_recorded.isoformat(),
            "message": f"Lesson ingested with id '{ingested.id}'.",
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _search_lessons(arguments: dict[str, Any]) -> list[TextContent]:
    """Search the lessons corpus by free-text query."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.lessons import (
            LessonCategory,
            LessonSentiment,
            LessonsKnowledgeEngine,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        raw_category = arguments.get("category")
        raw_sentiment = arguments.get("sentiment")

        engine = LessonsKnowledgeEngine(store=store)
        response = engine.search(
            query=arguments["query"],
            project_type=arguments.get("project_type"),
            category=LessonCategory(raw_category) if raw_category else None,
            sentiment=LessonSentiment(raw_sentiment) if raw_sentiment else None,
            limit=int(arguments.get("limit", 10)),
        )

        output: dict[str, Any] = {
            "query": response.query,
            "search_method": response.search_method,
            "total_in_corpus": response.total_in_corpus,
            "results_count": len(response.results),
            "results": [
                {
                    "id": r.lesson.id,
                    "project_id": r.lesson.project_id,
                    "title": r.lesson.title,
                    "category": r.lesson.category.value,
                    "sentiment": r.lesson.sentiment.value,
                    "project_type": r.lesson.project_type,
                    "relevance_score": r.relevance_score,
                    "match_reason": r.match_reason,
                }
                for r in response.results
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _log_assurance_activity(arguments: dict[str, Any]) -> list[TextContent]:
    """Log an assurance activity with effort tracking."""
    try:
        from datetime import date
        from pathlib import Path

        from pm_data_tools.assurance.overhead import (
            ActivityType,
            AssuranceActivity,
            AssuranceOverheadOptimiser,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        cb = arguments.get("confidence_before")
        ca = arguments.get("confidence_after")

        activity = AssuranceActivity(
            project_id=arguments["project_id"],
            activity_type=ActivityType(arguments["activity_type"]),
            description=arguments["description"],
            date=date.fromisoformat(str(arguments["date"])),
            effort_hours=float(arguments["effort_hours"]),
            participants=int(arguments.get("participants", 1)),
            artefacts_reviewed=list(arguments.get("artefacts_reviewed", [])),
            findings_count=int(arguments.get("findings_count", 0)),
            confidence_before=float(cb) if cb is not None else None,
            confidence_after=float(ca) if ca is not None else None,
        )

        optimiser = AssuranceOverheadOptimiser(store=store)
        logged = optimiser.log_activity(activity)

        output: dict[str, Any] = {
            "id": logged.id,
            "project_id": logged.project_id,
            "activity_type": logged.activity_type.value,
            "date": logged.date.isoformat(),
            "effort_hours": logged.effort_hours,
            "findings_count": logged.findings_count,
            "message": f"Activity logged with id '{logged.id}'.",
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _analyse_assurance_overhead(arguments: dict[str, Any]) -> list[TextContent]:
    """Run a complete assurance overhead analysis for a project."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.overhead import AssuranceOverheadOptimiser
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        project_id: str = arguments["project_id"]
        optimiser = AssuranceOverheadOptimiser(store=store)
        analysis = optimiser.analyse(project_id)

        output: dict[str, Any] = {
            "project_id": analysis.project_id,
            "timestamp": analysis.timestamp.isoformat(),
            "total_activities": analysis.total_activities,
            "total_effort_hours": analysis.total_effort_hours,
            "total_participants_hours": analysis.total_participants_hours,
            "effort_by_type": analysis.effort_by_type,
            "activities_with_findings": analysis.activities_with_findings,
            "activities_without_findings": analysis.activities_without_findings,
            "finding_rate": analysis.finding_rate,
            "avg_confidence_lift": analysis.avg_confidence_lift,
            "efficiency_rating": analysis.efficiency_rating.value,
            "duplicate_checks": [
                {
                    "activity_id": d.activity_id,
                    "duplicate_of": d.duplicate_of,
                    "overlap_type": d.overlap_type,
                    "detail": d.detail,
                }
                for d in analysis.duplicate_checks
            ],
            "recommendations": analysis.recommendations,
            "message": analysis.message,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _run_assurance_workflow(arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a multi-step assurance workflow for a project."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.workflows import AssuranceWorkflowEngine, WorkflowType
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        project_id: str = arguments["project_id"]
        workflow_type = WorkflowType(arguments["workflow_type"])
        artefacts = list(arguments.get("artefacts") or []) or None
        gate_date = arguments.get("gate_date")

        engine = AssuranceWorkflowEngine(store=store)
        result = engine.execute(
            project_id=project_id,
            workflow_type=workflow_type,
            artefacts=artefacts,
            gate_date=gate_date,
        )

        output: dict[str, Any] = {
            "id": result.id,
            "project_id": result.project_id,
            "workflow_type": result.workflow_type.value,
            "health": result.health.value,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "duration_ms": round(result.duration_ms, 1),
            "steps": [
                {
                    "step_name": s.step_name,
                    "status": s.status.value,
                    "duration_ms": round(s.duration_ms, 1),
                    "risk_signal": (
                        {
                            "source": s.risk_signal.source,
                            "signal_name": s.risk_signal.signal_name,
                            "severity": s.risk_signal.severity,
                            "detail": s.risk_signal.detail,
                        }
                        if s.risk_signal
                        else None
                    ),
                    "error_message": s.error_message,
                }
                for s in result.steps
            ],
            "aggregated_risk_signals": [
                {
                    "source": sig.source,
                    "signal_name": sig.signal_name,
                    "severity": sig.severity,
                    "detail": sig.detail,
                }
                for sig in result.aggregated_risk_signals
            ],
            "recommended_actions": result.recommended_actions,
            "executive_summary": result.executive_summary,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_workflow_history(arguments: dict[str, Any]) -> list[TextContent]:
    """Retrieve workflow execution history for a project."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.workflows import AssuranceWorkflowEngine
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        project_id: str = arguments["project_id"]
        engine = AssuranceWorkflowEngine(store=store)
        history = engine.get_workflow_history(project_id)

        output: dict[str, Any] = {
            "project_id": project_id,
            "total_executions": len(history),
            "executions": [
                {
                    "id": r.id,
                    "workflow_type": r.workflow_type.value,
                    "health": r.health.value,
                    "started_at": r.started_at.isoformat(),
                    "duration_ms": round(r.duration_ms, 1),
                    "steps_completed": sum(
                        1 for s in r.steps
                        if s.status.value == "COMPLETED"
                    ),
                    "signals_count": len(r.aggregated_risk_signals),
                }
                for r in history
            ],
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _classify_project_domain(arguments: dict[str, Any]) -> list[TextContent]:
    """Classify a project into a complexity domain."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.classifier import (
            ClassificationInput,
            ProjectDomainClassifier,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        def _opt_float(key: str) -> float | None:
            val = arguments.get(key)
            return float(val) if val is not None else None

        inp = ClassificationInput(
            project_id=arguments["project_id"],
            technical_complexity=_opt_float("technical_complexity"),
            stakeholder_complexity=_opt_float("stakeholder_complexity"),
            requirement_clarity=_opt_float("requirement_clarity"),
            delivery_track_record=_opt_float("delivery_track_record"),
            organisational_change=_opt_float("organisational_change"),
            regulatory_exposure=_opt_float("regulatory_exposure"),
            dependency_count=_opt_float("dependency_count"),
            notes=arguments.get("notes"),
        )

        clf = ProjectDomainClassifier(store=store)
        result = clf.classify(inp)

        output: dict[str, Any] = {
            "id": result.id,
            "project_id": result.project_id,
            "domain": result.domain.value,
            "composite_score": round(result.composite_score, 3),
            "explicit_score": (
                round(result.explicit_score, 3) if result.explicit_score is not None else None
            ),
            "derived_score": (
                round(result.derived_score, 3) if result.derived_score is not None else None
            ),
            "classified_at": result.classified_at.isoformat(),
            "indicators": [
                {
                    "name": i.name,
                    "raw_value": i.raw_value,
                    "complexity_contribution": round(i.complexity_contribution, 3),
                }
                for i in result.indicators
            ],
            "profile": {
                "review_frequency_days": result.profile.review_frequency_days,
                "recommended_tools": result.profile.recommended_tools,
                "confidence_threshold": result.profile.confidence_threshold,
                "compliance_floor": result.profile.compliance_floor,
                "notes": result.profile.notes,
            },
            "rationale": result.rationale,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _reclassify_from_store(arguments: dict[str, Any]) -> list[TextContent]:
    """Reclassify a project using only store-derived signals."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.classifier import ProjectDomainClassifier
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        project_id: str = arguments["project_id"]
        clf = ProjectDomainClassifier(store=store)
        result = clf.reclassify_from_store(project_id)

        output: dict[str, Any] = {
            "id": result.id,
            "project_id": result.project_id,
            "domain": result.domain.value,
            "composite_score": round(result.composite_score, 3),
            "derived_score": (
                round(result.derived_score, 3) if result.derived_score is not None else None
            ),
            "classified_at": result.classified_at.isoformat(),
            "profile": {
                "review_frequency_days": result.profile.review_frequency_days,
                "recommended_tools": result.profile.recommended_tools,
                "confidence_threshold": result.profile.confidence_threshold,
                "compliance_floor": result.profile.compliance_floor,
                "notes": result.profile.notes,
            },
            "rationale": result.rationale,
        }

        return [
            TextContent(
                type="text",
                text=json.dumps(output, indent=2, default=str),
            )
        ]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


# ---------------------------------------------------------------------------
# P11 — Assumption Drift Tracker handlers
# ---------------------------------------------------------------------------


async def _ingest_assumption(arguments: dict[str, Any]) -> list[TextContent]:
    """Ingest a project assumption with its baseline value."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.assumptions import (
            Assumption,
            AssumptionCategory,
            AssumptionSource,
            AssumptionTracker,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        tracker = AssumptionTracker(store=store)

        assumption = Assumption(
            project_id=arguments["project_id"],
            text=arguments["text"],
            category=AssumptionCategory(arguments["category"]),
            baseline_value=float(arguments["baseline_value"]),
            unit=arguments.get("unit", ""),
            tolerance_pct=float(arguments.get("tolerance_pct", 10.0)),
            source=AssumptionSource(arguments.get("source", "MANUAL")),
            external_ref=arguments.get("external_ref"),
            owner=arguments.get("owner"),
            notes=arguments.get("notes"),
        )
        tracker.ingest(assumption)

        output: dict[str, Any] = {
            "id": assumption.id,
            "project_id": assumption.project_id,
            "text": assumption.text,
            "category": assumption.category.value,
            "baseline_value": assumption.baseline_value,
            "unit": assumption.unit,
            "tolerance_pct": assumption.tolerance_pct,
            "source": assumption.source.value,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _validate_assumption(arguments: dict[str, Any]) -> list[TextContent]:
    """Update an assumption's current value and record the validation."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.assumptions import AssumptionSource, AssumptionTracker
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        tracker = AssumptionTracker(store=store)

        validation = tracker.update_value(
            assumption_id=arguments["assumption_id"],
            new_value=float(arguments["new_value"]),
            source=AssumptionSource(arguments.get("source", "MANUAL")),
            notes=arguments.get("notes"),
        )

        output: dict[str, Any] = {
            "id": validation.id,
            "assumption_id": validation.assumption_id,
            "validated_at": validation.validated_at.isoformat(),
            "previous_value": validation.previous_value,
            "new_value": validation.new_value,
            "drift_pct": validation.drift_pct,
            "severity": validation.severity.value,
            "notes": validation.notes,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_assumption_drift(arguments: dict[str, Any]) -> list[TextContent]:
    """Run a full assumption health analysis for a project."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.assumptions import AssumptionTracker
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        tracker = AssumptionTracker(store=store)

        report = tracker.analyse_project(arguments["project_id"])

        output: dict[str, Any] = {
            "project_id": report.project_id,
            "timestamp": report.timestamp.isoformat(),
            "total_assumptions": report.total_assumptions,
            "validated_count": report.validated_count,
            "stale_count": report.stale_count,
            "overall_drift_score": report.overall_drift_score,
            "by_severity": report.by_severity,
            "by_category": report.by_category,
            "cascade_warnings": report.cascade_warnings,
            "message": report.message,
            "drift_results": [
                {
                    "assumption_id": dr.assumption.id,
                    "text": dr.assumption.text,
                    "category": dr.assumption.category.value,
                    "baseline_value": dr.assumption.baseline_value,
                    "current_value": dr.assumption.current_value,
                    "unit": dr.assumption.unit,
                    "drift_pct": dr.drift_pct,
                    "severity": dr.severity.value,
                    "days_since_validation": dr.days_since_validation,
                    "cascade_impact_count": len(dr.cascade_impact),
                    "message": dr.message,
                }
                for dr in report.drift_results
            ],
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_cascade_impact(arguments: dict[str, Any]) -> list[TextContent]:
    """Find all assumptions affected by drift in the given assumption."""
    try:
        from pathlib import Path

        from pm_data_tools.assurance.assumptions import (
            AssumptionTracker,
            _row_to_assumption,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        tracker = AssumptionTracker(store=store)

        assumption_id: str = arguments["assumption_id"]
        impacted_ids = tracker.get_cascade_impact(assumption_id)

        items: list[dict[str, Any]] = []
        for aid in impacted_ids:
            row = store.get_assumption_by_id(aid)
            if row is not None:
                a = _row_to_assumption(row)
                dr = tracker.compute_drift(a)
                items.append({
                    "assumption_id": aid,
                    "text": a.text,
                    "category": a.category.value,
                    "baseline_value": a.baseline_value,
                    "current_value": a.current_value,
                    "drift_pct": dr.drift_pct,
                    "severity": dr.severity.value,
                })

        output: dict[str, Any] = {
            "source_assumption_id": assumption_id,
            "impacted_count": len(items),
            "impacted_assumptions": items,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


# ---------------------------------------------------------------------------
# Hackathon: create_project_from_profile
# ---------------------------------------------------------------------------


async def _create_project_from_profile(arguments: dict[str, Any]) -> list[TextContent]:
    """Create a full P1-P12 project from a Claude-extracted profile."""
    try:
        from pm_data_tools.db.store import AssuranceStore
        from pm_data_tools.assurance.generator import generate_single_project
        from pm_data_tools.assurance.classifier import ClassificationInput

        project_id: str = arguments["project_id"]
        name: str = arguments["name"]
        department: str = arguments["department"]
        domain: str = arguments["domain"]
        sro: str = arguments.get("sro", "Programme Director")

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        # Build ClassificationInput from profile indicators
        classifier_input = ClassificationInput(
            project_id=project_id,
            technical_complexity=arguments.get("technical_complexity", 0.5),
            stakeholder_complexity=arguments.get("stakeholder_complexity", 0.5),
            requirement_clarity=arguments.get("requirement_clarity", 0.5),
            delivery_track_record=arguments.get("delivery_track_record", 0.5),
            organisational_change=arguments.get("organisational_change", 0.5),
            regulatory_exposure=arguments.get("regulatory_exposure", 0.3),
            dependency_count=arguments.get("dependency_count", 0.5),
            notes=arguments.get("summary", ""),
        )

        meta = {"name": name, "sro": sro}

        # Run the full P1-P12 pipeline
        generate_single_project(
            store=store,
            project_id=project_id,
            domain=domain,
            meta=meta,
            classifier_input=classifier_input,
        )

        # Gather summary stats
        scores = store.get_confidence_scores(project_id)
        latest_score = scores[-1]["score"] if scores else None
        recs = store.get_recommendations(project_id)
        open_actions = sum(1 for r in recs if r.get("status") in ("OPEN", "RECURRING"))
        armm = store.get_armm_assessments(project_id)
        armm_level = None
        if armm:
            last_a = armm[-1]
            armm_level = last_a.get("overall_level")
        workflows = store.get_workflow_history(project_id)
        latest_health = None
        if workflows:
            latest_health = workflows[-1].get("health")

        record_count = (
            len(scores) + len(recs) + len(store.get_divergence_history(project_id))
            + len(store.get_schedule_history(project_id))
            + len(store.get_override_decisions(project_id))
            + len(store.get_assurance_activities(project_id))
            + len(store.get_assumptions(project_id))
            + len(armm) + len(workflows)
            + len(store.get_domain_classifications(project_id))
        )

        output: dict[str, Any] = {
            "project_id": project_id,
            "name": name,
            "department": department,
            "domain": domain,
            "latest_compliance_score": latest_score,
            "open_actions": open_actions,
            "armm_level": armm_level,
            "latest_health": latest_health,
            "records_created": record_count,
            "message": (
                f"Project '{name}' created with {record_count} assurance records.  "
                f"Domain: {domain}.  Compliance: {latest_score}.  "
                f"ARMM Level: {armm_level}.  Health: {latest_health}."
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


# ---------------------------------------------------------------------------
# Hackathon: export_dashboard_data
# ---------------------------------------------------------------------------


def _health_to_score(health: str) -> int:
    return {"HEALTHY": 90, "ATTENTION_NEEDED": 65, "AT_RISK": 40, "CRITICAL": 20}.get(health, 50)


async def _export_dashboard_data(arguments: dict[str, Any]) -> list[TextContent]:
    """Export all assurance data as static JSON for the UDS Renderer."""
    try:
        from pm_data_tools.db.store import AssuranceStore

        project_id: str = arguments["project_id"]
        output_dir: str = arguments["output_dir"]
        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        # --- Gather all P1-P12 data ---
        scores = store.get_confidence_scores(project_id)
        recs = store.get_recommendations(project_id)
        divergence = store.get_divergence_history(project_id)
        schedule = store.get_schedule_history(project_id)
        workflows = store.get_workflow_history(project_id)
        classifications = store.get_domain_classifications(project_id)
        assumptions = store.get_assumptions(project_id)

        # --- Build panel data ---
        panels: dict[str, Any] = {}

        # overall_health (gauge) — from latest workflow
        latest_wf = workflows[-1] if workflows else {}
        health_str = str(latest_wf.get("health", "ATTENTION_NEEDED"))
        panels["overall_health"] = {"value": _health_to_score(health_str)}

        # domain_classification (kpi) — from latest P10
        latest_cls = classifications[-1] if classifications else {}
        panels["domain_classification"] = {"value": str(latest_cls.get("domain", "UNKNOWN"))}

        # review_urgency (kpi) — from latest P5
        latest_sched = schedule[-1] if schedule else {}
        rec_date_str = str(latest_sched.get("recommended_date", ""))
        if rec_date_str:
            from datetime import datetime as _dt, date as _date
            try:
                rec_date = _dt.fromisoformat(rec_date_str).date() if "T" in rec_date_str else _date.fromisoformat(rec_date_str)
                days_until = max(0, (rec_date - _date.today()).days)
            except Exception:
                days_until = 42
        else:
            days_until = 42
        panels["review_urgency"] = {"value": days_until}

        # artefact_currency (kpi) — derive from scores
        if scores:
            avg = sum(s["score"] for s in scores[-3:]) / min(3, len(scores))
            panels["artefact_currency"] = {"value": round(min(1.0, avg / 100 * 0.92), 2)}
        else:
            panels["artefact_currency"] = {"value": 0.5}

        # compliance_score (kpi) — latest P2
        latest_score = scores[-1]["score"] if scores else None
        panels["compliance_score"] = {"value": latest_score}

        # action_closure (kpi) — derived from P3
        total_recs = len(recs)
        closed_recs = sum(1 for r in recs if r.get("status") == "CLOSED")
        panels["action_closure"] = {
            "value": round(closed_recs / max(1, total_recs), 2)
        }

        # ai_confidence (kpi) — latest P4
        latest_div = divergence[-1] if divergence else {}
        panels["ai_confidence"] = {
            "value": latest_div.get("confidence_score", 0.75)
        }

        # confidence_divergence (kpi) — spread from latest P4
        spread_map = {"STABLE": 0.08, "CONVERGENT": 0.05, "LOW_CONSENSUS": 0.22, "HIGH_DIVERGENCE": 0.30}
        panels["confidence_divergence"] = {
            "value": spread_map.get(str(latest_div.get("signal_type", "STABLE")), 0.10)
        }

        # compliance_trend (trend) — from P2 scores over time
        panels["compliance_trend"] = {
            "rows": [
                {
                    "label": str(s.get("timestamp", ""))[:7],
                    "compliance_score": s["score"],
                }
                for s in scores
            ]
        }

        # confidence_trend (trend) — from P4 divergence over time
        panels["confidence_trend"] = {
            "rows": [
                {
                    "label": str(d.get("timestamp", ""))[:7],
                    "confidence_score": d.get("confidence_score", 0),
                    "confidence_spread": spread_map.get(
                        str(d.get("signal_type", "STABLE")), 0.10
                    ),
                }
                for d in divergence
            ]
        }

        # artefact_status_bar (bar) — synthesise from score data
        if scores:
            avg_score = sum(s["score"] for s in scores) / len(scores)
            current_count = max(1, round(12 * avg_score / 100))
            outdated_count = max(0, 12 - current_count - 1)
            missing_count = max(0, 12 - current_count - outdated_count)
        else:
            current_count, outdated_count, missing_count = 8, 3, 1
        panels["artefact_status_bar"] = {
            "rows": [
                {"assurance.currency_status": "CURRENT", "assurance.artefact_count": current_count},
                {"assurance.currency_status": "OUTDATED", "assurance.artefact_count": outdated_count},
                {"assurance.currency_status": "MISSING", "assurance.artefact_count": missing_count},
            ]
        }

        # open_actions_table (table) — from P3 recommendations
        panels["open_actions_table"] = {
            "rows": [
                {
                    "assurance.action_id": str(r.get("id", ""))[:8],
                    "assurance.action_text": r.get("text", ""),
                    "assurance.action_category": r.get("category", ""),
                    "assurance.action_status": r.get("status", "OPEN"),
                    "assurance.action_confidence": r.get("confidence", 0),
                    "assurance.action_review_date": r.get("review_date", ""),
                    "assurance.action_owner": r.get("owner", ""),
                    "assurance.recurring": "YES" if r.get("recurrence_of") else "NO",
                }
                for r in recs
            ]
        }

        # --- Write to file ---
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{project_id}-data.json"
        file_path.write_text(json.dumps(panels, indent=2, default=str))

        output: dict[str, Any] = {
            "file_path": str(file_path),
            "panel_count": len(panels),
            "project_id": project_id,
            "url": f"http://localhost:5173/?dashboard=assurance-overview.uds.yaml&project_id={project_id}&data_mode=static&branded=true",
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=f"Error: {exc}\n{traceback.format_exc()}")]


# ---------------------------------------------------------------------------
# ARMM report
# ---------------------------------------------------------------------------


_LEVEL_LABELS = {0: "EXPERIMENTING", 1: "SUPERVISED", 2: "RELIABLE", 3: "RESILIENT", 4: "MISSION_CRITICAL"}
_DIMENSION_NAMES = {"TC": "Technical Controls", "OR": "Operational Resilience", "GA": "Governance & Accountability", "CC": "Capability & Culture"}


async def _get_armm_report(arguments: dict[str, Any]) -> list[TextContent]:
    """Return the full ARMM maturity report for a project."""
    try:
        from pm_data_tools.db.store import AssuranceStore

        project_id: str = arguments["project_id"]
        include_criteria: bool = arguments.get("include_criteria", False)
        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        assessments = store.get_armm_assessments(project_id)
        if not assessments:
            return [TextContent(type="text", text=json.dumps({
                "error": "NO_ARMM_DATA",
                "message": f"No ARMM assessments found for {project_id}. Run create_project_from_profile first.",
            }, indent=2))]

        latest = assessments[-1]

        # Parse stored JSON fields
        topic_scores = json.loads(latest.get("topic_scores_json", "{}"))
        topic_levels = json.loads(latest.get("topic_levels_json", "{}"))
        dim_scores = json.loads(latest.get("dimension_scores_json", "{}"))
        dim_levels = json.loads(latest.get("dimension_levels_json", "{}"))
        dim_blocking = json.loads(latest.get("dimension_blocking_json", "{}"))

        # Build dimension breakdown
        dimensions = []
        for code in ["TC", "OR", "GA", "CC"]:
            level = dim_levels.get(code, 0)
            dimensions.append({
                "code": code,
                "name": _DIMENSION_NAMES.get(code, code),
                "score_pct": round(dim_scores.get(code, 0), 1),
                "level": level,
                "level_label": _LEVEL_LABELS.get(level, "UNKNOWN"),
                "blocking_topic": dim_blocking.get(code),
            })

        # Build topic breakdown
        topics = []
        for topic_code, score in sorted(topic_scores.items()):
            dim_code = topic_code.split("-")[0]
            topics.append({
                "topic_code": topic_code,
                "dimension": dim_code,
                "score_pct": round(score, 1),
                "level": topic_levels.get(topic_code, 0),
                "level_label": _LEVEL_LABELS.get(topic_levels.get(topic_code, 0), "UNKNOWN"),
            })

        # Identify improvement priorities (lowest scoring topics)
        priorities = sorted(topics, key=lambda t: t["score_pct"])[:5]

        overall_level = latest.get("overall_level", 0)

        report: dict[str, Any] = {
            "project_id": project_id,
            "assessment_id": latest["id"],
            "assessed_at": latest.get("assessed_at"),
            "assessed_by": latest.get("assessed_by"),
            "overall_level": overall_level,
            "overall_level_label": _LEVEL_LABELS.get(overall_level, "UNKNOWN"),
            "overall_score_pct": round(latest.get("overall_score_pct", 0), 1),
            "criteria_met": latest.get("criteria_met", 0),
            "criteria_total": latest.get("criteria_total", 251),
            "assessment_count": len(assessments),
            "dimensions": dimensions,
            "topics": topics,
            "improvement_priorities": [
                {
                    "topic": p["topic_code"],
                    "dimension": p["dimension"],
                    "current_score": p["score_pct"],
                    "current_level": p["level_label"],
                }
                for p in priorities
            ],
        }

        # Optionally include individual criterion results
        if include_criteria:
            criteria = store.get_armm_criterion_results(latest["id"])
            report["criteria"] = [
                {
                    "criterion_id": c["criterion_id"],
                    "topic": c.get("topic_code", ""),
                    "dimension": c.get("dimension_code", ""),
                    "met": bool(c.get("met")),
                    "evidence_ref": c.get("evidence_ref", ""),
                }
                for c in criteria
            ]

        return [TextContent(type="text", text=json.dumps(report, indent=2, default=str))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=f"Error: {exc}\n{traceback.format_exc()}")]


# ---------------------------------------------------------------------------
# Hackathon: export_dashboard_html
# ---------------------------------------------------------------------------


async def _export_dashboard_html(arguments: dict[str, Any]) -> list[TextContent]:
    """Generate a self-contained HTML dashboard file."""
    try:
        from pm_data_tools.db.store import AssuranceStore
        from pm_mcp_servers.pm_assure.html_template import render_html

        project_id: str = arguments["project_id"]
        project_name: str = arguments["project_name"]
        department: str = arguments.get("department", "")
        domain: str = arguments.get("domain", "UNKNOWN")
        key_risks: list[str] = arguments.get("key_risks", [])

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)

        output_dir = arguments.get("output_dir")
        if not output_dir:
            output_dir = str(Path.home() / "Desktop" / "pda-dashboards")

        # Build the same panel data as export_dashboard_data
        spread_map = {"STABLE": 0.08, "CONVERGENT": 0.05, "LOW_CONSENSUS": 0.22, "HIGH_DIVERGENCE": 0.30}

        scores = store.get_confidence_scores(project_id)
        recs = store.get_recommendations(project_id)
        divergence = store.get_divergence_history(project_id)
        schedule = store.get_schedule_history(project_id)
        workflows = store.get_workflow_history(project_id)
        classifications = store.get_domain_classifications(project_id)

        latest_wf = workflows[-1] if workflows else {}
        health_str = str(latest_wf.get("health", "ATTENTION_NEEDED"))

        latest_cls = classifications[-1] if classifications else {}
        domain_val = str(latest_cls.get("domain", domain))

        latest_sched = schedule[-1] if schedule else {}
        rec_date_str = str(latest_sched.get("recommended_date", ""))
        if rec_date_str:
            from datetime import datetime as _dt, date as _date
            try:
                rec_date = _dt.fromisoformat(rec_date_str).date() if "T" in rec_date_str else _date.fromisoformat(rec_date_str)
                days_until = max(0, (rec_date - _date.today()).days)
            except Exception:
                days_until = 42
        else:
            days_until = 42

        latest_div = divergence[-1] if divergence else {}
        total_recs = len(recs)
        closed_recs = sum(1 for r in recs if r.get("status") == "CLOSED")

        data = {
            "project_name": project_name,
            "department": department,
            "domain": domain,
            "project_id": project_id,
            "key_risks": key_risks,
            "overall_health": {"value": _health_to_score(health_str)},
            "domain_classification": {"value": domain_val},
            "review_urgency": {"value": days_until},
            "artefact_currency": {
                "value": round(min(1.0, (sum(s["score"] for s in scores[-3:]) / max(1, min(3, len(scores)))) / 100 * 0.92), 2)
                if scores else 0.5
            },
            "compliance_score": {"value": scores[-1]["score"] if scores else None},
            "action_closure": {"value": round(closed_recs / max(1, total_recs), 2)},
            "ai_confidence": {"value": latest_div.get("confidence_score", 0.75)},
            "compliance_trend": {
                "rows": [
                    {"label": str(s.get("timestamp", ""))[:7], "compliance_score": s["score"]}
                    for s in scores
                ]
            },
            "confidence_trend": {
                "rows": [
                    {
                        "label": str(d.get("timestamp", ""))[:7],
                        "confidence_score": d.get("confidence_score", 0),
                    }
                    for d in divergence
                ]
            },
            "artefact_status_bar": {
                "rows": (lambda: [
                    {"assurance.currency_status": "CURRENT", "assurance.artefact_count": max(1, round(12 * (sum(s["score"] for s in scores) / len(scores)) / 100)) if scores else 8},
                    {"assurance.currency_status": "OUTDATED", "assurance.artefact_count": max(0, 12 - (max(1, round(12 * (sum(s["score"] for s in scores) / len(scores)) / 100)) if scores else 8) - 1)},
                    {"assurance.currency_status": "MISSING", "assurance.artefact_count": 1},
                ])()
            },
            "open_actions_table": {
                "rows": [
                    {
                        "assurance.action_id": str(r.get("id", ""))[:8],
                        "assurance.action_text": r.get("text", ""),
                        "assurance.action_category": r.get("category", ""),
                        "assurance.action_status": r.get("status", "OPEN"),
                        "assurance.action_confidence": r.get("confidence", 0),
                        "assurance.action_review_date": r.get("review_date", ""),
                        "assurance.action_owner": r.get("owner", ""),
                        "assurance.recurring": "YES" if r.get("recurrence_of") else "NO",
                    }
                    for r in recs
                ]
            },
        }

        html = render_html(data)

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{project_id}-dashboard.html"
        file_path.write_text(html, encoding="utf-8")

        output: dict[str, Any] = {
            "file_path": str(file_path),
            "project_id": project_id,
            "message": (
                f"HTML dashboard saved to {file_path}.  "
                "Open in any browser — works offline.  "
                "Would you like me to deploy this to a public URL?"
            ),
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=f"Error: {exc}\n{traceback.format_exc()}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the pm-assure MCP server."""
    import mcp.server.stdio

    async def arun() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )

    asyncio.run(arun())


# ---------------------------------------------------------------------------
# P14 — Gate Readiness Assessor handlers
# ---------------------------------------------------------------------------


async def _assess_gate_readiness(arguments: dict[str, Any]) -> list[TextContent]:
    """Run a full gate readiness assessment."""
    try:
        from pm_data_tools.assurance.gate_readiness import (
            GateReadinessAssessor,
            GateType,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        assessor = GateReadinessAssessor(store=store)

        gate = GateType(arguments["gate"])
        result = assessor.assess(arguments["project_id"], gate)

        output = {
            "id": result.id,
            "project_id": result.project_id,
            "gate": result.gate.value,
            "readiness": result.readiness.value,
            "composite_score": round(result.composite_score, 3),
            "dimensions_scored": result.dimensions_scored,
            "dimensions_total": result.dimensions_total,
            "dimension_scores": {
                k: {
                    "score": round(v.score, 3),
                    "status": v.status.value,
                    "weight": round(v.weight, 3),
                    "sources_available": v.sources_available,
                    "sources_missing": v.sources_missing,
                    "detail": v.detail,
                }
                for k, v in result.dimension_scores.items()
            },
            "blocking_issues": result.blocking_issues,
            "risk_signals": [
                {
                    "dimension": s.dimension.value,
                    "source": s.source,
                    "severity": round(s.severity, 3),
                    "is_blocking": s.is_blocking,
                    "detail": s.detail,
                }
                for s in result.risk_signals
            ],
            "recommended_actions": result.recommended_actions,
            "data_availability": result.data_availability,
            "executive_summary": result.executive_summary,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _get_gate_readiness_history(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Retrieve past gate readiness assessments."""
    try:
        from pm_data_tools.assurance.gate_readiness import (
            GateReadinessAssessor,
            GateType,
        )
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        assessor = GateReadinessAssessor(store=store)

        gate = GateType(arguments["gate"]) if arguments.get("gate") else None
        history = assessor.get_history(arguments["project_id"], gate)

        output = {
            "project_id": arguments["project_id"],
            "gate_filter": arguments.get("gate"),
            "total_assessments": len(history),
            "assessments": [
                {
                    "id": a.id,
                    "gate": a.gate.value,
                    "readiness": a.readiness.value,
                    "composite_score": round(a.composite_score, 3),
                    "assessed_at": a.assessed_at.isoformat(),
                    "dimensions_scored": a.dimensions_scored,
                    "blocking_count": len(a.blocking_issues),
                }
                for a in history
            ],
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _compare_gate_readiness(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Compare two gate readiness assessments."""
    try:
        from pm_data_tools.assurance.gate_readiness import GateReadinessAssessor
        from pm_data_tools.db.store import AssuranceStore

        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None
        store = AssuranceStore(db_path=db_path)
        assessor = GateReadinessAssessor(store=store)

        result = assessor.compare(
            arguments["assessment_id_before"],
            arguments["assessment_id_after"],
        )

        output = {
            "project_id": result.project_id,
            "gate": result.gate.value,
            "before_score": round(result.before_score, 3),
            "after_score": round(result.after_score, 3),
            "score_delta": round(result.score_delta, 3),
            "before_readiness": result.before_readiness.value,
            "after_readiness": result.after_readiness.value,
            "readiness_changed": result.readiness_changed,
            "improved_dimensions": result.improved_dimensions,
            "degraded_dimensions": result.degraded_dimensions,
            "resolved_blockers": result.resolved_blockers,
            "new_blockers": result.new_blockers,
            "message": result.message,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _scan_for_red_flags(arguments: dict[str, Any]) -> list[TextContent]:
    """Cross-module red flag scanner returning a prioritised alert list."""
    from datetime import datetime, timezone

    try:
        from pm_data_tools.db.store import AssuranceStore

        project_id: str = arguments["project_id"]
        severity_threshold: str = arguments.get("severity_threshold", "MEDIUM")
        raw_db_path = arguments.get("db_path")
        db_path = Path(raw_db_path) if raw_db_path else None

        store = AssuranceStore(db_path=db_path)

        # Severity ordering: higher number = higher severity
        _SEVERITY_ORDER = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
        threshold_level = _SEVERITY_ORDER.get(severity_threshold, 1)

        flags: list[dict[str, Any]] = []
        data_gaps: list[str] = []
        flag_counter = 0

        def _next_flag_id() -> str:
            nonlocal flag_counter
            flag_counter += 1
            return f"RF{flag_counter:03d}"

        def _severity_passes(sev: str) -> bool:
            return _SEVERITY_ORDER.get(sev, 0) >= threshold_level

        # ------------------------------------------------------------------
        # 1. RISK checks
        # ------------------------------------------------------------------
        try:
            all_risks = store.get_risks(project_id)
            open_risks = [r for r in all_risks if r.get("status", "OPEN") == "OPEN"]

            if not all_risks:
                data_gaps.append("no risks loaded for this project")
            else:
                # Check for risks with score >= 8 with no active mitigations
                critical_unmitigated: list[str] = []
                for risk in open_risks:
                    if (risk.get("risk_score") or 0) >= 8:
                        mitigations = store.get_mitigations(risk["id"])
                        active_mits = [
                            m for m in mitigations
                            if m.get("status") in ("IN_PROGRESS", "COMPLETE", "COMPLETED")
                        ]
                        if not active_mits:
                            critical_unmitigated.append(risk["id"])

                if critical_unmitigated and _severity_passes("CRITICAL"):
                    max_score = max(
                        (r.get("risk_score") or 0)
                        for r in open_risks
                        if r["id"] in critical_unmitigated
                    )
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "CRITICAL",
                        "category": "RISK",
                        "description": (
                            f"{len(critical_unmitigated)} critical risk(s) (score >= 8) "
                            "have no active mitigations"
                        ),
                        "evidence": {
                            "risk_ids": critical_unmitigated,
                            "max_score": max_score,
                        },
                        "recommended_action": (
                            f"Assign active mitigations to "
                            f"{', '.join(critical_unmitigated)} before next review"
                        ),
                    })

                # More than 3 open risks with score 6-7
                mid_risks = [r for r in open_risks if 6 <= (r.get("risk_score") or 0) <= 7]
                if len(mid_risks) > 3 and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "RISK",
                        "description": (
                            f"{len(mid_risks)} open risks have scores in the 6–7 range "
                            "(elevated but unmanaged cluster)"
                        ),
                        "evidence": {
                            "risk_ids": [r["id"] for r in mid_risks],
                            "count": len(mid_risks),
                        },
                        "recommended_action": (
                            "Review and consolidate mitigations for elevated risk cluster"
                        ),
                    })

                # Risk register not updated in >30 days
                now = datetime.now(tz=timezone.utc)
                stale_risks: list[str] = []
                for risk in open_risks:
                    updated_at = risk.get("updated_at")
                    if updated_at:
                        try:
                            updated_dt = datetime.fromisoformat(
                                str(updated_at).replace("Z", "+00:00")
                            )
                            if updated_dt.tzinfo is None:
                                updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                            age_days = (now - updated_dt).days
                            if age_days > 30:
                                stale_risks.append(risk["id"])
                        except (ValueError, TypeError):
                            pass

                if stale_risks and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "RISK",
                        "description": (
                            f"{len(stale_risks)} open risk(s) have not been updated "
                            "in over 30 days"
                        ),
                        "evidence": {
                            "risk_ids": stale_risks,
                            "count": len(stale_risks),
                        },
                        "recommended_action": (
                            "Review and refresh stale risks in the risk register"
                        ),
                    })

        except Exception as exc:
            data_gaps.append(f"risk data unavailable: {exc}")

        # ------------------------------------------------------------------
        # 2. BENEFITS checks
        # ------------------------------------------------------------------
        try:
            benefits = store.get_benefits(project_id)

            if not benefits:
                data_gaps.append("no benefits loaded for this project")
            else:
                # Benefits with no owner
                unowned = [b for b in benefits if not b.get("benefits_owner")]
                if unowned and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "BENEFITS",
                        "description": (
                            f"{len(unowned)} benefit(s) have no benefits owner assigned"
                        ),
                        "evidence": {
                            "benefit_ids": [b["id"] for b in unowned],
                            "count": len(unowned),
                        },
                        "recommended_action": (
                            "Assign a benefits owner to all unowned benefits"
                        ),
                    })

                # Benefits that are AT_RISK or OFF_TRACK
                at_risk_benefits = [
                    b for b in benefits
                    if b.get("status") in ("AT_RISK", "OFF_TRACK")
                ]
                if at_risk_benefits and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "BENEFITS",
                        "description": (
                            f"{len(at_risk_benefits)} benefit(s) are AT_RISK or OFF_TRACK"
                        ),
                        "evidence": {
                            "benefit_ids": [b["id"] for b in at_risk_benefits],
                            "statuses": {
                                b["id"]: b.get("status") for b in at_risk_benefits
                            },
                        },
                        "recommended_action": (
                            "Investigate root causes of at-risk benefits and update "
                            "realisation plans"
                        ),
                    })

                # Benefits behind their declared realisation profile
                now_str = datetime.now(tz=timezone.utc).date().isoformat()
                behind_realisation: list[str] = []
                for b in benefits:
                    target_date = b.get("target_date")
                    target_value = b.get("target_value")
                    current_actual = b.get("current_actual_value")
                    baseline_value = b.get("baseline_value") or 0.0
                    if (
                        target_date
                        and target_value is not None
                        and current_actual is not None
                        and target_date <= now_str
                    ):
                        # Compute expected fraction based on time elapsed since baseline
                        baseline_date = b.get("baseline_date") or b.get("created_at", "")[:10]
                        try:
                            from datetime import date as _date
                            td = _date.fromisoformat(str(target_date))
                            bd = _date.fromisoformat(str(baseline_date)[:10])
                            today = _date.fromisoformat(now_str)
                            total_days = (td - bd).days
                            elapsed_days = (today - bd).days
                            if total_days > 0:
                                expected_fraction = min(elapsed_days / total_days, 1.0)
                                expected_value = (
                                    baseline_value
                                    + (float(target_value) - baseline_value)
                                    * expected_fraction
                                )
                                if float(current_actual) < expected_value * 0.9:
                                    behind_realisation.append(b["id"])
                        except (ValueError, TypeError):
                            pass

                if behind_realisation and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "BENEFITS",
                        "description": (
                            f"{len(behind_realisation)} benefit(s) are behind their "
                            "declared realisation profile"
                        ),
                        "evidence": {
                            "benefit_ids": behind_realisation,
                            "count": len(behind_realisation),
                        },
                        "recommended_action": (
                            "Review realisation plans and escalate to benefits owner "
                            "and SRO"
                        ),
                    })

        except Exception as exc:
            data_gaps.append(f"benefits data unavailable: {exc}")

        # ------------------------------------------------------------------
        # 3. GOVERNANCE / GATE READINESS checks
        # ------------------------------------------------------------------
        try:
            gate_history = store.get_gate_readiness_history(project_id)

            if not gate_history:
                data_gaps.append("no gate readiness data loaded")
            else:
                # Use the most recent assessment
                latest_gate = sorted(gate_history, key=lambda g: g.get("assessed_at", ""))[-1]
                composite_score = float(latest_gate.get("composite_score") or 0.0)

                # Parse result_json for outstanding conditions
                result_json_raw = latest_gate.get("result_json")
                outstanding_conditions: list[str] = []
                if result_json_raw:
                    try:
                        result_data = json.loads(str(result_json_raw))
                        blocking = result_data.get("blocking_issues") or []
                        outstanding_conditions = list(blocking)
                    except (json.JSONDecodeError, TypeError):
                        pass

                if outstanding_conditions and _severity_passes("CRITICAL"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "CRITICAL",
                        "category": "GOVERNANCE",
                        "description": (
                            f"{len(outstanding_conditions)} outstanding gate condition(s) "
                            "must be resolved before progression"
                        ),
                        "evidence": {
                            "gate": latest_gate.get("gate"),
                            "assessed_at": latest_gate.get("assessed_at"),
                            "blocking_issues": outstanding_conditions,
                        },
                        "recommended_action": (
                            "Address all blocking gate conditions before the next "
                            "gate review"
                        ),
                    })

                # Gate readiness score < 60 (composite_score is 0.0–1.0, threshold 0.60)
                score_pct = composite_score * 100 if composite_score <= 1.0 else composite_score
                if score_pct < 60 and _severity_passes("HIGH"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "HIGH",
                        "category": "GOVERNANCE",
                        "description": (
                            f"Gate readiness score is {score_pct:.1f}% — below the 60% "
                            "minimum threshold"
                        ),
                        "evidence": {
                            "gate": latest_gate.get("gate"),
                            "composite_score": round(composite_score, 3),
                            "score_pct": round(score_pct, 1),
                            "assessed_at": latest_gate.get("assessed_at"),
                        },
                        "recommended_action": (
                            "Run assess_gate_readiness for a full dimension breakdown "
                            "and improvement priorities"
                        ),
                    })

        except Exception as exc:
            data_gaps.append(f"gate readiness data unavailable: {exc}")

        # ------------------------------------------------------------------
        # 4. COST / FINANCIAL checks
        # ------------------------------------------------------------------
        try:
            baselines = store.get_financial_baselines(project_id)
            actuals = store.get_financial_actuals(project_id)

            if not baselines:
                if _severity_passes("MEDIUM"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "MEDIUM",
                        "category": "COST",
                        "description": "No financial baseline has been set for this project",
                        "evidence": {},
                        "recommended_action": (
                            "Set a financial baseline using set_financial_baseline "
                            "to enable cost variance tracking"
                        ),
                    })
                data_gaps.append("no financial baseline loaded")
            elif actuals:
                # Compute total baseline budget vs total actuals
                total_budget = sum(
                    float(b.get("total_budget") or 0.0)
                    for b in baselines
                    if b.get("cost_category") == "TOTAL"
                    or not any(
                        bb.get("cost_category") == "TOTAL" for bb in baselines
                    )
                )
                # Fall back to any baseline if no TOTAL category
                if total_budget == 0.0:
                    total_budget = sum(
                        float(b.get("total_budget") or 0.0) for b in baselines
                    )

                total_actuals = sum(float(a.get("actual_spend") or 0.0) for a in actuals)

                if total_budget > 0:
                    variance_pct = ((total_actuals - total_budget) / total_budget) * 100
                    if variance_pct > 10 and _severity_passes("HIGH"):
                        flags.append({
                            "flag_id": _next_flag_id(),
                            "severity": "HIGH",
                            "category": "COST",
                            "description": (
                                f"Cost variance is {variance_pct:.1f}% unfavourable "
                                f"(actuals £{total_actuals:,.0f} vs baseline £{total_budget:,.0f})"
                            ),
                            "evidence": {
                                "total_budget": round(total_budget, 2),
                                "total_actuals": round(total_actuals, 2),
                                "variance_pct": round(variance_pct, 1),
                            },
                            "recommended_action": (
                                "Investigate cost overrun drivers and review forecast "
                                "to completion with the finance team"
                            ),
                        })
            else:
                data_gaps.append("no financial actuals loaded")

        except Exception as exc:
            data_gaps.append(f"financial data unavailable: {exc}")

        # ------------------------------------------------------------------
        # 5. CHANGE checks
        # ------------------------------------------------------------------
        try:
            open_changes = store.get_change_requests(project_id, status_filter="SUBMITTED")
            # Also include UNDER_REVIEW / PENDING statuses if present
            all_open_changes = store.get_change_requests(project_id)
            pending_changes = [
                c for c in all_open_changes
                if c.get("status") in ("SUBMITTED", "UNDER_REVIEW", "PENDING", "OPEN")
            ]

            if len(pending_changes) > 5 and _severity_passes("MEDIUM"):
                flags.append({
                    "flag_id": _next_flag_id(),
                    "severity": "MEDIUM",
                    "category": "CHANGE",
                    "description": (
                        f"{len(pending_changes)} open change requests are awaiting decision "
                        "(change pressure is high)"
                    ),
                    "evidence": {
                        "change_ids": [c["id"] for c in pending_changes],
                        "count": len(pending_changes),
                    },
                    "recommended_action": (
                        "Prioritise and resolve the change request backlog to reduce "
                        "delivery uncertainty"
                    ),
                })
            elif not all_open_changes:
                data_gaps.append("no change request data loaded")

        except Exception as exc:
            data_gaps.append(f"change request data unavailable: {exc}")

        # ------------------------------------------------------------------
        # 6. RESOURCE checks
        # ------------------------------------------------------------------
        try:
            resource_plans = store.get_resource_plans(project_id)

            if not resource_plans:
                data_gaps.append("no resource plan data loaded")
            else:
                # Detect critical resources at >100% loading
                # Group by resource_name, compute loading as planned_days / availability_pct
                from collections import defaultdict as _defaultdict
                resource_loading: dict[str, dict[str, Any]] = _defaultdict(
                    lambda: {"planned_days": 0.0, "availability_pct": 100.0, "periods": 0}
                )
                for plan in resource_plans:
                    rname = str(plan.get("resource_name") or "UNKNOWN")
                    resource_loading[rname]["planned_days"] += float(
                        plan.get("planned_days") or 0.0
                    )
                    resource_loading[rname]["availability_pct"] = float(
                        plan.get("availability_pct") or 100.0
                    )
                    resource_loading[rname]["periods"] = (
                        resource_loading[rname]["periods"] + 1
                    )

                overloaded: list[dict[str, Any]] = []
                for rname, data in resource_loading.items():
                    avail = data["availability_pct"]
                    if avail <= 0:
                        continue
                    # loading_pct: ratio of planned relative to full availability
                    # A resource with availability_pct=80 and planned_days covering
                    # their full calendar days is at 100%/0.80 = 125% loading.
                    # Simpler heuristic: flag when planned_days exceed (periods * avail/100 * 5)
                    # (assuming 5-day working week per period).
                    periods = data["periods"]
                    available_days = periods * (avail / 100.0) * 5
                    if available_days > 0 and data["planned_days"] > available_days:
                        loading_pct = (data["planned_days"] / available_days) * 100
                        if loading_pct > 100:
                            overloaded.append({
                                "resource_name": rname,
                                "loading_pct": round(loading_pct, 1),
                                "planned_days": round(data["planned_days"], 1),
                                "available_days": round(available_days, 1),
                            })

                if overloaded and _severity_passes("MEDIUM"):
                    flags.append({
                        "flag_id": _next_flag_id(),
                        "severity": "MEDIUM",
                        "category": "RESOURCES",
                        "description": (
                            f"{len(overloaded)} critical resource(s) are loaded above 100%"
                        ),
                        "evidence": {"overloaded_resources": overloaded},
                        "recommended_action": (
                            "Review resource allocation and resolve overloading before "
                            "it impacts delivery"
                        ),
                    })

        except Exception as exc:
            data_gaps.append(f"resource data unavailable: {exc}")

        # ------------------------------------------------------------------
        # Sort and filter flags by severity
        # ------------------------------------------------------------------
        severity_sort = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        flags.sort(key=lambda f: severity_sort.get(f["severity"], 99))

        # Re-assign sequential IDs after sort
        for idx, flag in enumerate(flags, start=1):
            flag["flag_id"] = f"RF{idx:03d}"

        # Build summary counts
        critical_count = sum(1 for f in flags if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in flags if f["severity"] == "HIGH")
        medium_count = sum(1 for f in flags if f["severity"] == "MEDIUM")

        output: dict[str, Any] = {
            "project_id": project_id,
            "severity_threshold": severity_threshold,
            "summary": {
                "total": len(flags),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
            },
            "flags": flags,
            "data_gaps": data_gaps,
            "scan_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


if __name__ == "__main__":  # pragma: no cover
    main()
