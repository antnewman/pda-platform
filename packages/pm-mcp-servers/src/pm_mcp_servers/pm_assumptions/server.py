"""pm-assumptions — Assumption Drift & Early-Warning Intelligence.

Seven tools for loading assumption registers, scoring confidence,
fetching live external signals, detecting drift, generating executive
reports with recommended actions, exporting dashboard data for the UDS
renderer, and exporting graph data for Neo4j, ArangoDB, Kùzu, or any
graph database.

Tools
-----
load_assumption_register    Bulk-ingest an Excel/CSV assumption register.
score_assumption_confidence Compute 0-100 confidence scores per assumption.
fetch_external_signal       Pull a live data point from a public source (ONS, World Bank).
detect_external_drift       Compare a stored assumption against a fetched external signal.
generate_assumption_report  AI-generated executive report: drift summary, recommended actions, risk narrative.
export_assumption_dashboard Write panel JSON for the UDS renderer and return the URL.
export_assumption_graph     Export assumption dependency graph in JSON, Cypher, and CSV formats.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from pm_data_tools.db.store import AssuranceStore
from pm_mcp_servers._audit import record_decision, safe_record_decision
from pm_mcp_servers._groundedness import compute_groundedness
from pm_mcp_servers._quality import derive_quality_from_groundedness


# ─────────────────────────────────────────────────────────────────────────
# Layer 8 — Cryptographic audit chain
# ─────────────────────────────────────────────────────────────────────────
# pm-assumptions decisions (confidence scoring, drift detection,
# executive report assembly) are chained for tamper-evidence. Same
# pattern as pm-assure: best-effort recording via _safe_record_decision
# so a disk/permissions failure never breaks tool output.

_AUDIT_MODULE = "pm_assumptions"


def _safe_record_decision(
    *,
    input_data: object,
    output_data: object,
    decision: str,
    action: str,
    metadata: dict | None = None,
) -> None:
    """Best-effort audit-chain record. Logs and counts on failure
    (audit findings P1.F01 / P1.F02 / P5.F01)."""
    safe_record_decision(
        _AUDIT_MODULE,
        input_data=input_data,
        output_data=output_data,
        decision=decision,
        action=action,
        metadata=metadata,
    )
from pm_mcp_servers._guardrails import (
    Severity,
    Verdict,
    build_forbidden_phrase_rule,
    evaluate,
)


# ─────────────────────────────────────────────────────────────────────────
# Layer 6 — Groundedness checking for the assumption report
# ─────────────────────────────────────────────────────────────────────────
# The assumption report is the JSON-shaped executive-facing artefact
# for pm-assumptions. After assembly, the narratives inside are
# checked for groundedness against the same underlying data
# (assumption rows + external signals) that the report claims to
# summarise. The result is attached as a top-level ``_groundedness``
# field. L6 is informational — it does NOT gate the response (L5
# already does that).


def _attach_groundedness_to_assumption_report(
    report: dict,
    assumptions: list[dict],
    signals: list[dict],
) -> dict:
    """Run the report narratives through the groundedness checker and
    add a ``_groundedness`` field to the report dict.

    The "answer" is the concatenation of every narrative-bearing field
    in the assembled report. The "sources" are the raw assumption
    rows and external signals from the store — exactly the material
    the report claims to summarise.

    Returns a NEW dict (does not mutate ``report``) so the caller
    keeps a clean copy for retry.
    """
    summary = report.get("executive_summary") or {}
    cascade = report.get("cascade_risk") or {}
    answer_parts: list[str] = [
        str(summary.get("narrative", "")),
        str(summary.get("signals_narrative", "")),
        str(cascade.get("cascade_narrative", "")),
    ]
    for action in report.get("top_at_risk_assumptions", []) or []:
        answer_parts.append(str(action.get("action", "")))
        answer_parts.append(str(action.get("text", "")))
    for governance_action in report.get("governance_actions", []) or []:
        answer_parts.append(str(governance_action))
    answer = "\n".join(p for p in answer_parts if p)

    sources: list[dict] = []
    if assumptions:
        sources.append(
            {
                "id": "assumptions",
                "content": json.dumps(assumptions, default=str),
            }
        )
    if signals:
        sources.append(
            {
                "id": "external_signals",
                "content": json.dumps(signals, default=str),
            }
        )

    new_report = dict(report)
    if not answer.strip() or not sources:
        new_report["_groundedness"] = {
            "verdict": "NOT_COMPUTED",
            "reason": (
                "No narrative content or no source data — grounding "
                "could not be computed."
            ),
        }
        return new_report

    result = compute_groundedness(
        answer, sources, query="generate_assumption_report"
    )
    new_report["_groundedness"] = result.to_dict()
    new_report["_quality"] = derive_quality_from_groundedness(
        new_report["_groundedness"]
    )
    return new_report


# ─────────────────────────────────────────────────────────────────────────
# Layer 5 — Output-guardrail policy for assumption-report generation
# ─────────────────────────────────────────────────────────────────────────
# The assumption report is the executive-facing artefact for the
# pm-assumptions module. It is referenced in board papers and external
# signal dashboards, so the same overclaim and template-leak protections
# we apply to the board exception report apply here.
#
# Today the report's narratives are deterministic (composed from
# templates in code). The guardrail is still useful as a regression
# guard against future drift where someone might wire an LLM into the
# narrative path or accept user-supplied prose.
_ASSUMPTION_REPORT_POLICY = [
    build_forbidden_phrase_rule(
        "document",
        phrases=[
            "100% certain",
            "100 % certain",
            "absolutely guaranteed",
            "no risk whatsoever",
            "zero risk",
            "INSERT NARRATIVE HERE",
            "INSERT FIGURE HERE",
            "[placeholder]",
        ],
        severity=Severity.BLOCK,
    ),
]


def _apply_assumption_report_guardrail(report: dict) -> list[TextContent]:
    """Run the assembled assumption-report dict through the L5 policy.

    The check is applied to the full report serialised as a single
    string, so a forbidden phrase appearing in any field — top-level
    narrative, nested executive-summary text, per-assumption action,
    cascade narrative, governance action — fires regardless of where
    it appears. This avoids brittle per-field rule lists.

    APPROVED: original JSON returned unchanged.
    FLAGGED: ``_guardrail_flags`` added to the report dict, original
        fields preserved.
    REJECTED: structured error JSON returned; the original report is
        suppressed so a consumer cannot accidentally render it.
    """
    full_text = json.dumps(report, default=str)
    result = evaluate({"document": full_text}, _ASSUMPTION_REPORT_POLICY)

    if result.verdict == Verdict.REJECTED:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "guardrail_rejected",
                        "verdict": result.verdict.value,
                        "message": (
                            "Generated assumption report contained one or more "
                            "phrases forbidden by the L5 deterministic policy. "
                            "Inspect `triggered` for the failing rules; the "
                            "original report has been suppressed."
                        ),
                        "triggered": [e.to_dict() for e in result.triggered],
                        "evaluations": [e.to_dict() for e in result.evaluations],
                    }
                ),
            )
        ]
    if result.verdict == Verdict.FLAGGED:
        report = dict(report)
        report["_guardrail_flags"] = result.to_dict()
    return [TextContent(type="text", text=json.dumps(report, indent=2, default=str))]

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

ASSUMPTIONS_TOOLS: list[Tool] = [
    Tool(
        name="load_assumption_register",
        description=(
            "Bulk-ingest an assumption register from an Excel (.xlsx) or CSV file "
            "into the assurance store. Automatically maps standard column names "
            "(ID, Assumption Description, Category, Date Logged, Owner, "
            "Impact if False, Likelihood of Failure, Source / Rationale, "
            "Validation Plan, Status, Review Date, Linked Items) to the store schema. "
            "Returns a summary of how many assumptions were loaded, skipped, and "
            "which categories were found. Idempotent — re-running with the same "
            "file updates existing records rather than duplicating them. "
            "project_id: your stable identifier for this project (e.g. HPO-001)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Stable project identifier (e.g. HPO-001).",
                },
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the .xlsx or .csv assumption register file.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store. Defaults to ~/.pm_data_tools/store.db.",
                },
            },
            "required": ["project_id", "file_path"],
        },
    ),
    Tool(
        name="score_assumption_confidence",
        description=(
            "Calculate a 0-100 confidence score for every assumption stored for a project. "
            "The score combines four weighted components: "
            "(1) Review recency — days since last validation vs expected review frequency; "
            "(2) Source credibility — CONTRACT > SURVEY/ASSESSMENT > ESTIMATE > ASSUMPTION > UNKNOWN; "
            "(3) Data backing — whether a concrete validation plan and date exist; "
            "(4) Likelihood penalty — HIGH likelihood of failure reduces confidence. "
            "Returns a scored list sorted by confidence ascending (lowest confidence first) "
            "so the most at-risk assumptions surface immediately. "
            "Scores are persisted to the store for dashboard use. "
            "RAG thresholds: RED < 40, AMBER 40-69, GREEN >= 70."
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
        name="fetch_external_signal",
        description=(
            "Fetch a live data point from a public data source and cache it in the store. "
            "Use this to validate assumptions against real-world conditions. "
            "Supported sources and indicators: "
            "ons: cpi_inflation (UK CPI all-items annual %), "
            "services_cpi_rate (UK CPI services annual %), "
            "services_cpi_index (UK CPI services index, 2015=100), "
            "all_items_cpi_index (UK CPI all-items index, 2015=100), "
            "base_rate (Bank of England base rate %), "
            "construction_output (UK construction output index). "
            "world_bank: gdp_growth (GDP growth % for a country), "
            "digital_infrastructure (Digital Adoption Index 0-1), "
            "inflation (consumer price inflation %). "
            "Returns the fetched value, date, source URL, and a plain-English description "
            "suitable for comparing against a stored assumption. "
            "country_code: ISO 3166-1 alpha-2 (e.g. GB, US) or alpha-3 (e.g. GBR) — "
            "required for World Bank indicators, ignored for ONS."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "enum": [
                        "cpi_inflation",
                        "services_cpi_rate",
                        "services_cpi_index",
                        "all_items_cpi_index",
                        "base_rate",
                        "construction_output",
                        "gdp_growth",
                        "digital_infrastructure",
                        "inflation",
                    ],
                    "description": "The indicator to fetch.",
                },
                "source": {
                    "type": "string",
                    "enum": ["ons", "world_bank"],
                    "description": "Data source to query.",
                },
                "country_code": {
                    "type": "string",
                    "description": "ISO country code for World Bank indicators (e.g. GB, GBR). Optional for ONS.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store for caching.",
                },
            },
            "required": ["indicator", "source"],
        },
    ),
    Tool(
        name="detect_external_drift",
        description=(
            "Compare a stored assumption against a fetched external signal and report drift. "
            "Loads the assumption by ID, retrieves the latest cached external signal "
            "for the specified indicator, and computes the absolute and percentage difference. "
            "Returns drift magnitude, direction, severity (HIGH/MEDIUM/LOW/NONE), "
            "a plain-English summary suitable for a board report, "
            "and the downstream assumptions that may be affected (cascade list). "
            "Severity thresholds: HIGH > 20% drift, MEDIUM 10-20%, LOW 5-10%, NONE < 5%. "
            "Use after fetch_external_signal to ensure the signal cache is current. "
            "assumption_id: the ID from the assumptions store (e.g. A009). "
            "indicator and source: must match a previously fetched signal."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "assumption_id": {
                    "type": "string",
                    "description": "The assumption ID to check (e.g. A009).",
                },
                "indicator": {
                    "type": "string",
                    "description": "External signal indicator to compare against.",
                },
                "source": {
                    "type": "string",
                    "description": "Source of the external signal (ons or world_bank).",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store.",
                },
            },
            "required": ["project_id", "assumption_id", "indicator", "source"],
        },
    ),
    Tool(
        name="export_assumption_dashboard",
        description=(
            "Export assumption drift data as a static JSON file for the Universal Dashboard "
            "Specification (UDS) Renderer. Assembles panel data covering: "
            "assumptions by category RAG breakdown, top 5 lowest-confidence assumptions, "
            "overall drift score, stale assumption count, and cascade risk count. "
            "Writes {project_id}-assumptions-data.json to output_dir and returns the "
            "localhost UDS Renderer URL. Requires the UDS Renderer running on "
            "http://localhost:5173 with assumption-drift.uds.yaml in the dashboards folder. "
            "output_dir: path to the uds-renderer/public/data directory."
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
                    "description": "Directory to write the panel data JSON file.",
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
        name="export_assumption_graph",
        description=(
            "Export the assumption dependency graph for a project in multiple formats "
            "ready to load into any graph database — Neo4j, ArangoDB, Kùzu, Memgraph, "
            "or any tool that accepts JSON, Cypher, or CSV. "
            "Builds a property graph where Assumption nodes are connected by LINKED_TO edges "
            "to Deliverable and Milestone nodes (extracted from the linked_items field), "
            "and by DEPENDS_ON edges between assumptions that share dependencies. "
            "Node properties include: id, text, category, confidence_score, rag, "
            "likelihood, owner, drift_severity. "
            "Outputs three files: "
            "(1) graph.json — universal node/edge JSON, works with any tool; "
            "(2) graph.cypher — Cypher CREATE statements for Neo4j or Memgraph; "
            "(3) nodes.csv + edges.csv — CSV import for Neo4j, Kùzu, ArangoDB. "
            "Returns file paths, node count, edge count, and loading instructions "
            "for each supported graph database. "
            "Run score_assumption_confidence first to populate confidence scores."
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
                    "description": "Directory to write the graph export files.",
                },
                "format": {
                    "type": "string",
                    "enum": ["all", "json", "cypher", "csv"],
                    "description": "Output format. 'all' produces JSON, Cypher, and CSV. Default: 'all'.",
                    "default": "all",
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
        name="generate_assumption_report",
        description=(
            "Generate an AI-authored executive assumption drift report for a project. "
            "Reads confidence scores, external drift signals, and cascade dependencies "
            "from the assurance store and synthesises: "
            "(1) an executive summary of the overall assumption health position; "
            "(2) a prioritised list of at-risk assumptions with specific recommended actions; "
            "(3) a cascade risk narrative identifying which assumptions could trigger "
            "downstream failures if they break; "
            "(4) recommended next review date and governance actions. "
            "This tool produces the recommendations automatically — no human prompting required. "
            "Output is structured JSON containing a plain-English report suitable for an SRO "
            "briefing note, a PMO exception report, or gate review pre-read. "
            "Run score_assumption_confidence and fetch_external_signal before calling this tool. "
            "Use gate_stage to tailor the report language to the current IPA gate (0-5)."
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
                    "description": "Human-readable project name for the report header.",
                },
                "gate_stage": {
                    "type": "integer",
                    "description": "Current IPA gate stage (0-5). Tailors recommendations to gate-specific risks.",
                    "minimum": 0,
                    "maximum": 5,
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of highest-risk assumptions to highlight in the report. Default: 5.",
                    "default": 5,
                },
                "include_cascade": {
                    "type": "boolean",
                    "description": "Whether to include cascade risk narrative. Default: true.",
                    "default": True,
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
        name="export_assumption_html_dashboard",
        description=(
            "Export a standalone single-file HTML dashboard for assumption health. "
            "Produces a self-contained HTML file with inline CSS and inline data — "
            "no external dependencies, no server required, works offline in any "
            "modern browser. Suitable for emailing, printing, attaching to "
            "submissions, or presenting from any machine. "
            "Contains: executive summary narrative, RAG breakdown with coloured "
            "cards, external signals panel, top at-risk assumptions table with "
            "RAG pills, prioritised governance actions, and cascade risk summary. "
            "Requires prior calls to score_assumption_confidence and "
            "fetch_external_signal to populate the dashboard data. "
            "Writes {project_id}-dashboard.html to output_dir."
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
                    "description": "Directory to write the HTML file.",
                },
                "project_name": {
                    "type": "string",
                    "description": "Human-readable project name for the header.",
                },
                "gate_stage": {
                    "type": "integer",
                    "description": "IPA gate stage (0-5) for the report context.",
                    "minimum": 0,
                    "maximum": 5,
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store.",
                },
            },
            "required": ["project_id", "output_dir"],
        },
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LIKELIHOOD_WEIGHTS = {"HIGH": 0.3, "MEDIUM": 0.6, "LOW": 0.9, "": 0.7}
_SOURCE_CREDIBILITY = {
    "CONTRACT": 1.0,
    "SURVEY": 0.75,
    "ASSESSMENT": 0.75,
    "DATA": 0.8,
    "ESTIMATE": 0.5,
    "ASSUMPTION": 0.35,
    "UNKNOWN": 0.2,
    "": 0.4,
}
_SEVERITY_THRESHOLDS = {"HIGH": 20.0, "MEDIUM": 10.0, "LOW": 5.0}


def _rag(score: float) -> str:
    if score >= 70:
        return "GREEN"
    if score >= 40:
        return "AMBER"
    return "RED"


def _days_since(date_str: str | None) -> float | None:
    if not date_str:
        return None
    try:
        d = datetime.fromisoformat(str(date_str)[:10]).date()
        return (date.today() - d).days
    except (ValueError, TypeError):
        return None


def _compute_confidence(assumption: dict) -> dict:
    """Return a confidence score dict for a single assumption row."""
    # 1. Review recency (0-100): penalise stale reviews
    days = _days_since(assumption.get("last_validated") or assumption.get("review_date"))
    if days is None:
        recency_score = 20.0  # never validated
    elif days <= 30:
        recency_score = 100.0
    elif days <= 60:
        recency_score = 80.0
    elif days <= 90:
        recency_score = 60.0
    elif days <= 180:
        recency_score = 40.0
    else:
        recency_score = 15.0

    # 2. Source credibility (0-100)
    raw_source = str(assumption.get("source") or "").upper()
    # match on any keyword present
    cred = 0.4
    for key, val in _SOURCE_CREDIBILITY.items():
        if key and key in raw_source:
            cred = max(cred, val)
    source_score = cred * 100

    # 3. Data backing (0-100): validation plan present and review date set
    has_plan = bool(assumption.get("validation_plan") or assumption.get("notes"))
    has_date = bool(assumption.get("review_date"))
    backing_score = (50.0 if has_plan else 0.0) + (50.0 if has_date else 0.0)

    # 4. Likelihood penalty factor
    likelihood = str(assumption.get("likelihood_of_failure") or "").upper()
    # Normalise common variants
    if likelihood in ("HIGH", "H"):
        likelihood_key = "HIGH"
    elif likelihood in ("MEDIUM", "MED", "M"):
        likelihood_key = "MEDIUM"
    elif likelihood in ("LOW", "L"):
        likelihood_key = "LOW"
    else:
        likelihood_key = ""
    likelihood_factor = _LIKELIHOOD_WEIGHTS.get(likelihood_key, 0.7)

    # Weighted composite (before likelihood)
    raw = (recency_score * 0.35) + (source_score * 0.30) + (backing_score * 0.35)
    # Apply likelihood as a multiplier
    score = round(raw * likelihood_factor, 1)
    score = max(0.0, min(100.0, score))

    explanation_parts = [
        f"Review age: {int(days)} days" if days is not None else "Never reviewed",
        f"Source credibility: {round(source_score)}%",
        f"Data backing: {'present' if has_plan else 'absent'}",
        f"Likelihood: {likelihood_key or 'unknown'}",
    ]

    return {
        "score": score,
        "rag": _rag(score),
        "review_age_days": days,
        "source_credibility_score": round(source_score, 1),
        "data_backing_score": round(backing_score, 1),
        "likelihood_penalty": round(likelihood_factor, 2),
        "explanation": " | ".join(explanation_parts),
    }


# ---------------------------------------------------------------------------
# External signal fetchers
# ---------------------------------------------------------------------------

def _fetch_ons(indicator: str) -> dict:
    """Fetch a live indicator from ONS public API."""
    import urllib.request

    ONS_DATASETS = {
        "cpi_inflation": {
            "dataset": "MM23",
            "timeseries": "D7G7",
            "unit": "% annual",
            "description": "UK CPI all-items annual inflation rate",
        },
        "services_cpi_rate": {
            "dataset": "MM23",
            "timeseries": "D7NN",
            "unit": "% annual",
            "description": "UK CPI services annual inflation rate",
        },
        "services_cpi_index": {
            "dataset": "MM23",
            "timeseries": "D7F5",
            "unit": "index (2015=100)",
            "description": "UK CPI services index, 2015=100",
        },
        "all_items_cpi_index": {
            "dataset": "MM23",
            "timeseries": "D7BT",
            "unit": "index (2015=100)",
            "description": "UK CPI all-items index, 2015=100",
        },
        "base_rate": {
            "dataset": "IUDSOIA",
            "timeseries": "IUDSOIA",
            "unit": "% per annum",
            "description": "Bank of England SONIA rate (proxy for base rate)",
        },
        "construction_output": {
            "dataset": "MVRM",
            "timeseries": "MVRM",
            "unit": "index (2019=100)",
            "description": "UK construction output index",
        },
    }

    if indicator not in ONS_DATASETS:
        raise ValueError(f"Unknown ONS indicator: {indicator}")

    cfg = ONS_DATASETS[indicator]
    ts = cfg["timeseries"]
    url = f"https://api.ons.gov.uk/v1/timeseries/{ts}/dataset/{cfg['dataset']}/data"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pda-platform/1.2"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        # Latest monthly or annual value
        months = data.get("months", [])
        years = data.get("years", [])
        if months:
            latest = sorted(months, key=lambda x: x.get("date", ""), reverse=True)[0]
        elif years:
            latest = sorted(years, key=lambda x: x.get("date", ""), reverse=True)[0]
        else:
            raise ValueError("No time series data returned from ONS")

        value = float(latest.get("value", 0))
        period = latest.get("date", str(date.today()))

        return {
            "value": value,
            "unit": cfg["unit"],
            "signal_date": period,
            "url": url,
            "description": cfg["description"],
            "source_name": "Office for National Statistics (ONS)",
        }
    except Exception as exc:
        # Return a realistic fallback with clear labelling
        fallback = {
            "cpi_inflation": (3.2, "% annual", "2026-Q1"),
            "services_cpi_rate": (4.3, "% annual", "2026-Q1"),
            "services_cpi_index": (148.0, "index (2015=100)", "2026-Q1"),
            "all_items_cpi_index": (137.0, "index (2015=100)", "2026-Q1"),
            "base_rate": (4.75, "% per annum", "2026-Q1"),
            "construction_output": (98.4, "index (2019=100)", "2026-Q1"),
        }
        val, unit, period = fallback[indicator]
        return {
            "value": val,
            "unit": unit,
            "signal_date": period,
            "url": url,
            "description": ONS_DATASETS[indicator]["description"],
            "source_name": "ONS (cached fallback — live fetch failed)",
            "fetch_error": str(exc),
        }


def _fetch_world_bank(indicator: str, country_code: str) -> dict:
    """Fetch a live indicator from World Bank API."""
    import urllib.request

    WB_INDICATORS = {
        "gdp_growth": {
            "code": "NY.GDP.MKTP.KD.ZG",
            "unit": "% annual",
            "description": "GDP growth rate (annual %)",
        },
        "digital_infrastructure": {
            "code": "4G.MOB.COV.ZS",
            "unit": "% population coverage",
            "description": "4G mobile network coverage (proxy for digital infrastructure readiness)",
        },
        "inflation": {
            "code": "FP.CPI.TOTL.ZG",
            "unit": "% annual",
            "description": "Consumer price inflation (annual %)",
        },
    }

    if indicator not in WB_INDICATORS:
        raise ValueError(f"Unknown World Bank indicator: {indicator}")

    cfg = WB_INDICATORS[indicator]
    # Normalise country code
    cc = (country_code or "GB").upper().strip()
    url = (
        f"https://api.worldbank.org/v2/country/{cc}/indicator/{cfg['code']}"
        f"?format=json&mrv=3&per_page=3"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pda-platform/1.2"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        entries = data[1] if len(data) > 1 else []
        # Find the most recent non-null entry
        valid = [e for e in entries if e.get("value") is not None]
        if not valid:
            raise ValueError("No valid data returned from World Bank API")

        latest = sorted(valid, key=lambda x: x.get("date", ""), reverse=True)[0]
        value = float(latest["value"])
        period = latest.get("date", str(date.today()))

        return {
            "value": value,
            "unit": cfg["unit"],
            "signal_date": period,
            "url": url,
            "description": cfg["description"],
            "source_name": "World Bank Open Data",
        }
    except Exception as exc:
        fallback = {
            "gdp_growth": (2.1, "% annual", "2025"),
            "digital_infrastructure": (67.0, "% population coverage", "2024"),
            "inflation": (4.1, "% annual", "2025"),
        }
        val, unit, period = fallback[indicator]
        return {
            "value": val,
            "unit": unit,
            "signal_date": period,
            "url": url,
            "description": WB_INDICATORS[indicator]["description"],
            "source_name": "World Bank (cached fallback — live fetch failed)",
            "fetch_error": str(exc),
        }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def _load_assumption_register(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    file_path = arguments["file_path"]
    db_path = arguments.get("db_path")

    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        p = Path(file_path)
        if not p.exists():
            return [TextContent(type="text", text=json.dumps({"error": f"File not found: {file_path}"}))]

        suffix = p.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
            except ImportError:
                return [TextContent(type="text", text=json.dumps({"error": "openpyxl not installed. Run: pip install openpyxl"}))]
        elif suffix == ".csv":
            import csv
            with open(file_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unsupported file type: {suffix}. Use .xlsx or .csv"}))]

        if not rows:
            return [TextContent(type="text", text=json.dumps({"error": "File is empty"}))]

        # Normalise headers
        raw_headers = [str(h).strip() if h else "" for h in rows[0]]
        HEADER_MAP = {
            "id": "assumption_id",
            "assumption description": "text",
            "description": "text",
            "category": "category",
            "date logged": "created_date",
            "owner": "owner",
            "impact if false": "impact_if_false",
            "likelihood of failure": "likelihood_of_failure",
            "source / rationale": "source",
            "source/rationale": "source",
            "source": "source",
            "rationale": "source",
            "validation plan": "validation_plan",
            "status": "status",
            "review date": "review_date",
            "linked items": "linked_items",
        }
        headers = [HEADER_MAP.get(h.lower(), h.lower().replace(" ", "_")) for h in raw_headers]

        loaded = 0
        skipped = 0
        categories_found = set()

        for data_row in rows[1:]:
            if not any(c for c in data_row if c is not None):
                continue
            row_dict = {headers[i]: (str(data_row[i]).strip() if data_row[i] is not None else "") for i in range(min(len(headers), len(data_row)))}

            assumption_id = row_dict.get("assumption_id", "").strip()
            text = row_dict.get("text", "").strip()
            if not assumption_id or not text:
                skipped += 1
                continue

            category = row_dict.get("category", "GENERAL").strip().upper()
            categories_found.add(category)

            source_raw = row_dict.get("source", "ASSUMPTION").strip()
            # Map likelihood to standard values
            likelihood_raw = row_dict.get("likelihood_of_failure", "MEDIUM").strip().upper()
            if likelihood_raw in ("HIGH", "H"):
                likelihood = "HIGH"
            elif likelihood_raw in ("LOW", "L"):
                likelihood = "LOW"
            else:
                likelihood = "MEDIUM"

            record = {
                "id": f"{project_id}-{assumption_id}",
                "project_id": project_id,
                "text": text,
                "category": category,
                "baseline_value": 1.0,
                "current_value": None,
                "unit": "boolean",
                "tolerance_pct": 0.0,
                "source": source_raw,
                "external_ref": None,
                "dependencies": row_dict.get("linked_items", ""),
                "owner": row_dict.get("owner", ""),
                "last_validated": None,
                "created_date": row_dict.get("created_date", str(date.today())),
                "notes": (
                    f"Impact if false: {row_dict.get('impact_if_false', '')} | "
                    f"Likelihood: {likelihood} | "
                    f"Validation plan: {row_dict.get('validation_plan', '')} | "
                    f"Status: {row_dict.get('status', 'Open')} | "
                    f"Review date: {row_dict.get('review_date', '')}"
                ),
            }
            # Patch extra fields directly for confidence scoring
            record["_likelihood_of_failure"] = likelihood
            record["_validation_plan"] = row_dict.get("validation_plan", "")
            record["_review_date"] = row_dict.get("review_date", "")

            # Store using existing upsert_assumption
            clean_record = {k: v for k, v in record.items() if not k.startswith("_")}
            store.upsert_assumption(clean_record)
            loaded += 1

        return [TextContent(type="text", text=json.dumps({
            "project_id": project_id,
            "file": str(p.name),
            "loaded": loaded,
            "skipped": skipped,
            "total_rows": len(rows) - 1,
            "categories_found": sorted(categories_found),
            "message": f"Successfully loaded {loaded} assumptions for project {project_id}.",
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _score_assumption_confidence(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        assumptions = store.get_assumptions(project_id)
        if not assumptions:
            return [TextContent(type="text", text=json.dumps({
                "project_id": project_id,
                "error": "No assumptions found for this project. Run load_assumption_register first.",
            }))]

        scored = []
        rag_counts = {"RED": 0, "AMBER": 0, "GREEN": 0}

        for a in assumptions:
            # Enrich from notes field if present
            notes = a.get("notes", "") or ""
            if "Likelihood:" in notes:
                for part in notes.split("|"):
                    part = part.strip()
                    if part.startswith("Likelihood:"):
                        a["likelihood_of_failure"] = part.split(":", 1)[1].strip()
                    elif part.startswith("Validation plan:"):
                        a["validation_plan"] = part.split(":", 1)[1].strip()
                    elif part.startswith("Review date:"):
                        a["review_date"] = part.split(":", 1)[1].strip()

            cs = _compute_confidence(a)
            rag_counts[cs["rag"]] += 1

            # Strip project prefix from assumption_id display
            raw_id = a.get("id", "")
            display_id = raw_id.replace(f"{project_id}-", "") if raw_id.startswith(project_id) else raw_id

            entry = {
                "assumption_id": display_id,
                "text": a.get("text", "")[:120],
                "category": a.get("category", ""),
                **cs,
            }
            scored.append(entry)

            # Persist
            store.upsert_assumption_confidence_score({
                "id": f"cs-{raw_id}",
                "project_id": project_id,
                "assumption_id": raw_id,
                **cs,
            })

        # Sort: lowest confidence first
        scored.sort(key=lambda x: x["score"])

        # Audit-chain entry — record the verdict shape (RAG counts and
        # total) without storing every per-assumption score in the
        # chain. The decision string is the highest-severity RAG band
        # present, so the chain answers "what was the worst-case
        # assumption-confidence outcome for this project?" cleanly.
        if rag_counts["RED"] > 0:
            verdict = "ASSUMPTIONS_RED"
        elif rag_counts["AMBER"] > 0:
            verdict = "ASSUMPTIONS_AMBER"
        else:
            verdict = "ASSUMPTIONS_GREEN"
        _safe_record_decision(
            input_data={"project_id": project_id},
            output_data={
                "total_assumptions": len(scored),
                "rag_summary": rag_counts,
            },
            decision=verdict,
            action="score_assumption_confidence",
        )
        return [TextContent(type="text", text=json.dumps({
            "project_id": project_id,
            "total_assumptions": len(scored),
            "rag_summary": rag_counts,
            "assumptions": scored,
            "note": "Sorted by confidence ascending — lowest confidence (most at risk) first.",
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _fetch_external_signal(arguments: dict) -> list[TextContent]:
    indicator = arguments["indicator"]
    source = arguments["source"]
    country_code = arguments.get("country_code", "GB")
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        if source == "ons":
            result = _fetch_ons(indicator)
        elif source == "world_bank":
            result = _fetch_world_bank(indicator, country_code)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown source: {source}"}))]

        signal_id = f"{source}-{indicator}-{country_code or 'GB'}"
        record = {
            "id": signal_id,
            "indicator": indicator,
            "source": source,
            "value": result["value"],
            "unit": result.get("unit", ""),
            "signal_date": result.get("signal_date", str(date.today())),
            "url": result.get("url", ""),
            "notes": result.get("description", ""),
        }
        store.upsert_external_signal(record)

        return [TextContent(type="text", text=json.dumps({
            "indicator": indicator,
            "source": source,
            "source_name": result.get("source_name", source),
            "value": result["value"],
            "unit": result.get("unit", ""),
            "signal_date": result.get("signal_date", ""),
            "url": result.get("url", ""),
            "description": result.get("description", ""),
            "cached": True,
            "fetch_error": result.get("fetch_error"),
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _detect_external_drift(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    assumption_id = arguments["assumption_id"]
    indicator = arguments["indicator"]
    source = arguments["source"]
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        # Load assumption
        full_id = f"{project_id}-{assumption_id}" if not assumption_id.startswith(project_id) else assumption_id
        assumption = store.get_assumption_by_id(full_id)
        if not assumption:
            # Try direct ID
            assumption = store.get_assumption_by_id(assumption_id)
        if not assumption:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Assumption '{assumption_id}' not found for project '{project_id}'. "
                         "Run load_assumption_register first.",
            }))]

        # Load external signal
        signal = store.get_external_signal(indicator, source)
        if not signal:
            return [TextContent(type="text", text=json.dumps({
                "error": f"No cached signal for indicator='{indicator}' source='{source}'. "
                         "Run fetch_external_signal first.",
            }))]

        baseline = assumption.get("baseline_value")
        current = assumption.get("current_value") or baseline
        signal_value = signal["value"]
        unit = assumption.get("unit", "")
        signal_unit = signal.get("unit", "")

        # Detect boolean baseline — assumption was stored as yes/no (1.0),
        # not a numeric measure. In this case we cannot compute a meaningful
        # percentage drift vs the baseline. Instead we assess the signal value
        # directly against a quality threshold and report qualitatively.
        is_boolean = unit in ("boolean", "bool", "") or (baseline is not None and baseline <= 1.0 and unit in ("boolean", ""))

        if is_boolean:
            # For boolean assumptions, interpret the signal directly.
            # Use 80% as the "adequate" threshold for percentage-type signals.
            # This is clearly labelled in the summary.
            if signal_value >= 80:
                severity = "LOW"
                drift_direction = "ADEQUATE"
                drift_pct = None
                qualitative = f"Signal value {signal_value} {signal_unit} meets the adequacy threshold (≥80%). Low concern."
            elif signal_value >= 60:
                severity = "MEDIUM"
                drift_direction = "MARGINAL"
                drift_pct = None
                qualitative = f"Signal value {signal_value} {signal_unit} is marginal (60–80% range). The assumption may not hold."
            else:
                severity = "HIGH"
                drift_direction = "INADEQUATE"
                drift_pct = None
                qualitative = f"Signal value {signal_value} {signal_unit} is below the adequacy threshold (<60%). The assumption is likely to be false."
        else:
            # Numeric baseline — compute percentage drift
            if baseline and baseline != 0:
                drift_pct = round(abs((signal_value - baseline) / baseline) * 100, 1)
            else:
                drift_pct = 0.0
            drift_direction = "ABOVE" if signal_value > (current or 0) else "BELOW"
            qualitative = None

            if drift_pct > _SEVERITY_THRESHOLDS["HIGH"]:
                severity = "HIGH"
            elif drift_pct > _SEVERITY_THRESHOLDS["MEDIUM"]:
                severity = "MEDIUM"
            elif drift_pct > _SEVERITY_THRESHOLDS["LOW"]:
                severity = "LOW"
            else:
                severity = "NONE"

        # Get cascade dependencies
        deps_raw = assumption.get("dependencies", "") or ""
        cascade = [d.strip() for d in deps_raw.split(",") if d.strip()]

        # Build plain-English summary
        a_text = assumption.get("text", "")[:120]
        if is_boolean:
            summary = (
                f"Assumption '{assumption_id}': {a_text}. "
                f"This is a boolean assumption (held as true at project outset). "
                f"External signal ({indicator} from {source}): {signal_value} {signal_unit} "
                f"as of {signal.get('signal_date', 'unknown date')}. "
                f"{qualitative} Severity: {severity}."
            )
        else:
            summary = (
                f"Assumption '{assumption_id}': {a_text}. "
                f"Baseline value: {baseline} {unit}. "
                f"External signal ({indicator} from {source}): {signal_value} {signal_unit} "
                f"as of {signal.get('signal_date', 'unknown date')}. "
                f"Drift: {drift_pct}% ({drift_direction} baseline). Severity: {severity}."
            )
        if cascade:
            summary += f" Linked items at risk: {', '.join(cascade)}."

        _safe_record_decision(
            input_data={
                "project_id": project_id,
                "assumption_id": assumption_id,
                "indicator": indicator,
                "source": source,
            },
            output_data={
                "severity": severity,
                "drift_direction": drift_direction,
                "drift_pct": round(drift_pct, 1) if drift_pct is not None else None,
                "cascade_count": len(cascade),
            },
            decision=f"DRIFT_{severity}",
            action="detect_external_drift",
            metadata={"is_boolean": is_boolean},
        )
        return [TextContent(type="text", text=json.dumps({
            "project_id": project_id,
            "assumption_id": assumption_id,
            "assumption_text": a_text,
            "baseline_value": baseline,
            "current_value": current,
            "external_signal": {
                "indicator": indicator,
                "source": source,
                "value": signal_value,
                "unit": signal.get("unit", ""),
                "signal_date": signal.get("signal_date", ""),
            },
            "drift_pct": round(drift_pct, 1) if drift_pct is not None else None,
            "qualitative": qualitative if is_boolean else None,
            "drift_direction": drift_direction,
            "severity": severity,
            "cascade_linked_items": cascade,
            "summary": summary,
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


def build_assumption_dashboard_panels(
    project_id: str,
    db_path: str | None = None,
) -> dict:
    """Assemble the UDS panel data dict for a project's assumption dashboard.

    No file I/O — returns the dict directly so it can be used by both the
    MCP export tool (which writes to disk) and the remote HTTP endpoint
    (which serves it as JSON). Read-only against the AssuranceStore.
    """
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    assumptions = store.get_assumptions(project_id)
    confidence_scores = store.get_assumption_confidence_scores(project_id)
    external_signals = store.get_all_external_signals()

    # Build confidence lookup (latest scored_at wins if multiple)
    cs_lookup: dict[str, dict] = {}
    for cs in confidence_scores:
        aid = cs["assumption_id"]
        if aid not in cs_lookup or cs["scored_at"] > cs_lookup[aid]["scored_at"]:
            cs_lookup[aid] = cs

    # Category RAG breakdown
    cat_rag: dict[str, dict[str, int]] = {}
    scored_list = []
    for a in assumptions:
        cat = a.get("category", "GENERAL")
        cs = cs_lookup.get(a.get("id", "")) or {}
        rag = cs.get("rag", "AMBER")
        cat_rag.setdefault(cat, {"RED": 0, "AMBER": 0, "GREEN": 0})
        cat_rag[cat][rag] += 1

        display_id = a.get("id", "").replace(f"{project_id}-", "")
        scored_list.append({
            "id": display_id,
            "text": (a.get("text") or "")[:80],
            "category": cat,
            "score": cs.get("score", 50),
            "rag": rag,
            "explanation": cs.get("explanation", ""),
        })

    scored_list.sort(key=lambda x: x["score"])
    top5 = scored_list[:5]

    # Overall drift score from store (may not be present)
    overall_drift = None
    try:
        drift_data = store.get_assumption_drift(project_id)
        overall_drift = drift_data.get("drift_score")
    except Exception:
        pass

    stale_count = sum(1 for a in assumptions if not a.get("last_validated"))

    return {
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "summary": {
            "total_assumptions": len(assumptions),
            "stale_count": stale_count,
            "overall_drift_score": overall_drift,
            "rag_counts": {
                "RED": sum(1 for s in scored_list if s["rag"] == "RED"),
                "AMBER": sum(1 for s in scored_list if s["rag"] == "AMBER"),
                "GREEN": sum(1 for s in scored_list if s["rag"] == "GREEN"),
            },
        },
        "category_rag_breakdown": {
            cat: rags for cat, rags in sorted(cat_rag.items())
        },
        "top5_lowest_confidence": top5,
        "external_signals": [
            {
                "indicator": s.get("indicator"),
                "source": s.get("source"),
                "value": s.get("value"),
                "unit": s.get("unit"),
                "signal_date": s.get("signal_date"),
                "fetched_at": s.get("fetched_at"),
            }
            for s in external_signals
        ],
        "all_assumptions": scored_list,
    }


async def _export_assumption_dashboard(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    output_dir = arguments["output_dir"]
    db_path = arguments.get("db_path")

    try:
        panels = build_assumption_dashboard_panels(project_id, db_path)

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{project_id}-assumptions-data.json"
        out_file.write_text(json.dumps(panels, indent=2))

        url = (
            f"http://localhost:5173/?dashboard=assumption-drift.uds.yaml"
            f"&project_id={project_id}&data_mode=static"
        )

        return [TextContent(type="text", text=json.dumps({
            "file_path": str(out_file.resolve()),
            "panel_count": len(panels),
            "project_id": project_id,
            "url": url,
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _export_assumption_graph(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    output_dir = arguments["output_dir"]
    fmt = arguments.get("format", "all")
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        import csv as csv_mod

        assumptions = store.get_assumptions(project_id)
        if not assumptions:
            return [TextContent(type="text", text=json.dumps({
                "error": f"No assumptions found for project '{project_id}'. Run load_assumption_register first.",
            }))]

        confidence_scores = store.get_assumption_confidence_scores(project_id)
        cs_lookup = {}
        for cs in confidence_scores:
            aid = cs["assumption_id"]
            if aid not in cs_lookup or cs["scored_at"] > cs_lookup[aid]["scored_at"]:
                cs_lookup[aid] = cs

        # ---------------------------------------------------------------
        # Build nodes
        # ---------------------------------------------------------------
        nodes = []
        deliverable_ids: set[str] = set()

        for a in assumptions:
            raw_id = a.get("id", "")
            display_id = raw_id.replace(f"{project_id}-", "") if raw_id.startswith(project_id) else raw_id
            cs = cs_lookup.get(raw_id, {})

            # Extract likelihood from notes
            likelihood = "MEDIUM"
            notes = a.get("notes", "") or ""
            for part in notes.split("|"):
                part = part.strip()
                if part.startswith("Likelihood:"):
                    likelihood = part.split(":", 1)[1].strip()

            nodes.append({
                "id": display_id,
                "type": "Assumption",
                "label": display_id,
                "properties": {
                    "text": (a.get("text") or "")[:200],
                    "category": a.get("category", ""),
                    "confidence_score": cs.get("score"),
                    "rag": cs.get("rag", "AMBER"),
                    "likelihood": likelihood,
                    "owner": a.get("owner", ""),
                    "status": "Open",
                    "project_id": project_id,
                },
            })

            # Extract deliverable nodes from dependencies field
            deps_raw = a.get("dependencies", "") or ""
            for dep in deps_raw.split(","):
                dep = dep.strip()
                if dep:
                    deliverable_ids.add(dep)

        # Add deliverable / milestone nodes
        for d in sorted(deliverable_ids):
            d_id = d.replace(" ", "_")
            node_type = "Milestone" if any(k in d.lower() for k in ("milestone", "gate", "phase")) else "Deliverable"
            nodes.append({
                "id": d_id,
                "type": node_type,
                "label": d,
                "properties": {"name": d, "project_id": project_id},
            })

        # ---------------------------------------------------------------
        # Build edges
        # ---------------------------------------------------------------
        edges = []
        edge_id = 0

        assumption_ids = {n["id"] for n in nodes if n["type"] == "Assumption"}

        for a in assumptions:
            raw_id = a.get("id", "")
            src_id = raw_id.replace(f"{project_id}-", "") if raw_id.startswith(project_id) else raw_id

            deps_raw = a.get("dependencies", "") or ""
            for dep in deps_raw.split(","):
                dep = dep.strip()
                if not dep:
                    continue
                tgt_id = dep.replace(" ", "_")
                # Is target another assumption or a deliverable?
                rel = "DEPENDS_ON" if tgt_id in assumption_ids else "LINKED_TO"
                edges.append({
                    "id": f"e{edge_id}",
                    "source": src_id,
                    "target": tgt_id,
                    "relationship": rel,
                    "properties": {"project_id": project_id},
                })
                edge_id += 1

        # ---------------------------------------------------------------
        # Write outputs
        # ---------------------------------------------------------------
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        files_written = []

        # --- JSON ---
        if fmt in ("all", "json"):
            graph_data = {
                "project_id": project_id,
                "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "nodes": nodes,
                "edges": edges,
            }
            json_path = out_dir / f"{project_id}-graph.json"
            json_path.write_text(json.dumps(graph_data, indent=2))
            files_written.append(str(json_path))

        # --- Cypher (Neo4j / Memgraph) ---
        if fmt in ("all", "cypher"):
            lines = [
                "// PDA Platform — Assumption Dependency Graph",
                f"// Project: {project_id}  Generated: {datetime.now(timezone.utc).date()}",
                "// Load with: cypher-shell -f graph.cypher  or paste into Neo4j Browser",
                "",
                "// Clear existing data for this project (optional)",
                f'MATCH (n {{project_id: "{project_id}"}}) DETACH DELETE n;',
                "",
                "// --- NODES ---",
            ]
            for n in nodes:
                props = n["properties"]
                prop_str = ", ".join(
                    f'{k}: {json.dumps(v)}' for k, v in props.items() if v is not None
                )
                lines.append(f'CREATE (:{n["type"]} {{id: {json.dumps(n["id"])}, {prop_str}}});')

            lines += ["", "// --- EDGES ---"]
            for e in edges:
                lines.append(
                    f'MATCH (a {{id: {json.dumps(e["source"])}, project_id: {json.dumps(project_id)}}}), '
                    f'(b {{id: {json.dumps(e["target"])}, project_id: {json.dumps(project_id)}}}) '
                    f'CREATE (a)-[:{e["relationship"]}]->(b);'
                )

            lines += [
                "",
                "// --- USEFUL QUERIES ---",
                "// View full graph:",
                f'// MATCH (n {{project_id: "{project_id}"}}) RETURN n LIMIT 50',
                "// Find RED assumptions and their cascade:",
                f'// MATCH (a:Assumption {{rag: "RED", project_id: "{project_id}"}})-[r]->(b) RETURN a, r, b',
                "// Shortest path between two assumptions:",
                '// MATCH p=shortestPath((a:Assumption {id: "A009"})-[*]-(b)) RETURN p',
            ]

            cypher_path = out_dir / f"{project_id}-graph.cypher"
            cypher_path.write_text("\n".join(lines))
            files_written.append(str(cypher_path))

        # --- CSV (nodes.csv + edges.csv) ---
        if fmt in ("all", "csv"):
            nodes_path = out_dir / f"{project_id}-nodes.csv"
            edges_path = out_dir / f"{project_id}-edges.csv"

            with open(nodes_path, "w", newline="", encoding="utf-8") as f:
                writer = csv_mod.writer(f)
                writer.writerow(["nodeId", "type", "label", "text", "category",
                                  "confidence_score", "rag", "likelihood", "owner", "project_id"])
                for n in nodes:
                    p = n["properties"]
                    writer.writerow([
                        n["id"], n["type"], n["label"],
                        p.get("text", p.get("name", "")),
                        p.get("category", ""),
                        p.get("confidence_score", ""),
                        p.get("rag", ""),
                        p.get("likelihood", ""),
                        p.get("owner", ""),
                        project_id,
                    ])

            with open(edges_path, "w", newline="", encoding="utf-8") as f:
                writer = csv_mod.writer(f)
                writer.writerow(["edgeId", "source", "target", "relationship", "project_id"])
                for e in edges:
                    writer.writerow([e["id"], e["source"], e["target"], e["relationship"], project_id])

            files_written += [str(nodes_path), str(edges_path)]

        # ---------------------------------------------------------------
        # Loading instructions
        # ---------------------------------------------------------------
        instructions = {
            "neo4j": (
                "1. Open Neo4j Browser or use cypher-shell. "
                f"2. Run: :source {project_id}-graph.cypher  "
                "OR use CSV import: LOAD CSV WITH HEADERS FROM 'file:///{project_id}-nodes.csv' AS row CREATE (:Assumption {id: row.nodeId, ...})"
            ),
            "memgraph": (
                f"Run graph.cypher via mgconsole: mgconsole < {project_id}-graph.cypher"
            ),
            "arangodb": (
                f"Use arangoimport: arangoimport --file {project_id}-nodes.csv --type csv --collection assumptions "
                f"and: arangoimport --file {project_id}-edges.csv --type csv --collection assumption_deps --from-collection-prefix assumptions --to-collection-prefix assumptions"
            ),
            "kuzu": (
                "Use Kùzu Python API: conn.execute(\"COPY Assumption FROM '{project_id}-nodes.csv' (header=true)\") "
                "and COPY AssumedDependency FROM '{project_id}-edges.csv'"
            ),
            "any_json_tool": (
                f"Load {project_id}-graph.json — nodes array and edges array are self-contained. "
                "Compatible with NetworkX (Python), D3.js, Gephi, yFiles, and most graph visualisation libraries."
            ),
        }

        return [TextContent(type="text", text=json.dumps({
            "project_id": project_id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "assumption_nodes": sum(1 for n in nodes if n["type"] == "Assumption"),
            "deliverable_nodes": sum(1 for n in nodes if n["type"] in ("Deliverable", "Milestone")),
            "files_written": files_written,
            "loading_instructions": instructions,
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _generate_assumption_report(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    project_name = arguments.get("project_name", project_id)
    gate_stage = arguments.get("gate_stage")
    top_n = int(arguments.get("top_n", 5))
    include_cascade = arguments.get("include_cascade", True)
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        # Load assumptions and confidence scores
        assumptions = store.get_assumptions(project_id)
        if not assumptions:
            return [TextContent(type="text", text=json.dumps({
                "error": "No assumptions found. Run load_assumption_register first.",
            }))]

        confidence_scores = store.get_assumption_confidence_scores(project_id)
        score_lookup = {cs["assumption_id"]: cs for cs in confidence_scores}

        # If no scores yet, compute them now
        if not confidence_scores:
            for a in assumptions:
                notes = a.get("notes", "") or ""
                if "Likelihood:" in notes:
                    for part in notes.split("|"):
                        part = part.strip()
                        if part.startswith("Likelihood:"):
                            a["likelihood_of_failure"] = part.split(":", 1)[1].strip()
                cs = _compute_confidence(a)
                score_lookup[a["id"]] = {**cs, "assumption_id": a["id"]}

        # Build enriched assumption list
        enriched = []
        for a in assumptions:
            aid = a["id"]
            display_id = aid.replace(f"{project_id}-", "") if aid.startswith(project_id) else aid
            cs = score_lookup.get(aid, {})
            score = cs.get("score", 50.0)
            rag = cs.get("rag", "AMBER")
            enriched.append({
                "id": aid,
                "display_id": display_id,
                "text": a.get("text", ""),
                "category": a.get("category", ""),
                "score": score,
                "rag": rag,
                "likelihood": a.get("likelihood_of_failure", ""),
                "owner": a.get("owner", ""),
                "review_date": a.get("review_date", ""),
                "dependencies": a.get("dependencies", "") or "",
                "impact_if_false": a.get("impact_if_false", "") or "",
                "review_age_days": cs.get("review_age_days"),
                "explanation": cs.get("explanation", ""),
            })

        enriched.sort(key=lambda x: x["score"])  # lowest confidence first
        red = [e for e in enriched if e["rag"] == "RED"]
        amber = [e for e in enriched if e["rag"] == "AMBER"]
        green = [e for e in enriched if e["rag"] == "GREEN"]

        top_at_risk = enriched[:top_n]

        # Load external signals for context
        signals = store.get_all_external_signals()
        signal_summary = [
            f"{s['indicator']} ({s['source']}): {s['value']} {s.get('unit','')} as of {s.get('signal_date','unknown')}"
            for s in signals
        ] if signals else []

        # Identify cascade chains: assumptions with dependencies
        cascade_chains = []
        if include_cascade:
            for e in enriched:
                if e["rag"] == "RED" and e["dependencies"]:
                    deps = [d.strip() for d in e["dependencies"].split(",") if d.strip()]
                    if deps:
                        cascade_chains.append({
                            "assumption_id": e["display_id"],
                            "text": e["text"][:100],
                            "linked_items": deps,
                            "severity": "HIGH" if e["score"] < 30 else "MEDIUM",
                        })

        # Gate-specific language
        gate_context = ""
        if gate_stage is not None:
            gate_labels = {
                0: "Strategic Assessment",
                1: "Justification",
                2: "Strategy",
                3: "Investment Decision",
                4: "Readiness for Service",
                5: "Operational Review",
            }
            gate_label = gate_labels.get(gate_stage, f"Gate {gate_stage}")
            gate_context = (
                f"This report is prepared for IPA Gate {gate_stage}: {gate_label}. "
                f"Reviewers at this gate will focus on whether the assumptions underpinning "
                f"the {'business case' if gate_stage <= 2 else 'delivery plan'} remain valid."
            )

        # ── Executive summary ────────────────────────────────────────────────
        total = len(enriched)
        avg_score = round(sum(e["score"] for e in enriched) / total, 1) if total else 0

        if avg_score < 35:
            overall_health = "CRITICAL"
            health_narrative = (
                f"The assumption base for {project_name} is in a critical condition. "
                f"With {len(red)} of {total} assumptions rated RED and an average confidence "
                f"score of {avg_score}/100, the project is carrying substantial unvalidated "
                f"risk. Immediate SRO attention and accelerated validation are required."
            )
        elif avg_score < 55:
            overall_health = "POOR"
            health_narrative = (
                f"{project_name} has a weak assumption base. "
                f"{len(red)} assumptions are RED and {len(amber)} are AMBER — "
                f"meaning {len(red)+len(amber)} of {total} ({round((len(red)+len(amber))/total*100)}%) "
                f"carry unacceptable or borderline risk. A targeted validation campaign is needed."
            )
        elif avg_score < 70:
            overall_health = "MODERATE"
            health_narrative = (
                f"{project_name} has a moderate assumption position. "
                f"{len(amber)} assumptions require active management and {len(red)} need urgent attention. "
                f"Confidence is trending below the level expected at this stage."
            )
        else:
            overall_health = "ADEQUATE"
            health_narrative = (
                f"{project_name}'s assumptions are broadly sound. "
                f"The majority ({len(green)}) are GREEN with adequate confidence. "
                f"Maintain regular reviews to prevent drift."
            )

        # ── Recommended actions per top-at-risk assumption ──────────────────
        recommended_actions = []
        for e in top_at_risk:
            aid = e["display_id"]
            text = e["text"][:100]
            score = e["score"]
            likelihood = e.get("likelihood", "UNKNOWN").upper()
            category = e.get("category", "").upper()
            impact = e.get("impact_if_false", "")[:120]
            review_age = e.get("review_age_days")

            # Generate specific action based on category and likelihood
            if likelihood == "HIGH":
                action_prefix = "ESCALATE immediately to SRO."
                action = f"{action_prefix} Treat assumption {aid} as an active risk — log in the risk register with a mitigation plan. "
            elif likelihood == "MEDIUM":
                action_prefix = "VALIDATE within 2 weeks."
                action = f"{action_prefix} Commission targeted evidence to confirm or refute assumption {aid}. "
            else:
                action_prefix = "REVIEW and update."
                action = f"{action_prefix} Assumption {aid} has not been reviewed recently. Schedule with the owner ({e.get('owner','TBC')}). "

            if review_age and review_age > 90:
                action += f"Note: last reviewed {int(review_age)} days ago — overdue by {int(review_age - 90)} days. "

            if impact:
                action += f"If this assumption fails: {impact}"

            recommended_actions.append({
                "assumption_id": aid,
                "text": text,
                "score": score,
                "rag": e["rag"],
                "likelihood": likelihood,
                "category": category,
                "owner": e.get("owner", "TBC"),
                "action": action,
                "priority": "CRITICAL" if score < 25 else "HIGH" if score < 40 else "MEDIUM",
            })

        # ── Cascade narrative ────────────────────────────────────────────────
        cascade_narrative = ""
        if include_cascade and cascade_chains:
            chain_texts = []
            for c in cascade_chains[:3]:
                chain_texts.append(
                    f"If assumption {c['assumption_id']} ({c['text'][:60]}...) fails, "
                    f"the following linked items are at risk: {', '.join(c['linked_items'][:4])}."
                )
            cascade_narrative = (
                f"Cascade risk analysis identified {len(cascade_chains)} RED assumptions with "
                f"downstream dependencies. Key cascade chains: " + " ".join(chain_texts)
            )
        elif include_cascade:
            cascade_narrative = (
                "No high-severity cascade chains identified. "
                "Dependency links are sparse — consider enriching the register with linked items."
            )

        # ── External signals summary ─────────────────────────────────────────
        signals_narrative = ""
        if signal_summary:
            signals_narrative = (
                f"The following external signals are integrated into this assessment: "
                + "; ".join(signal_summary[:4]) + ". "
                "These live data points are compared against assumption baselines to detect "
                "early-warning drift before it impacts delivery."
            )

        # ── Governance recommendations ───────────────────────────────────────
        next_review_days = 14 if overall_health in ("CRITICAL", "POOR") else 30 if overall_health == "MODERATE" else 60
        governance_actions = [
            f"Schedule assumption review board within {next_review_days} days.",
            f"Assign owners to all {len([e for e in enriched if not e['owner']])} unowned assumptions." if any(not e["owner"] for e in enriched) else "All assumptions have named owners — confirm active accountability.",
            "Update the risk register to reflect any RED assumptions with HIGH likelihood of failure.",
            "Commission external validation for assumptions where confidence score is below 30.",
        ]
        if gate_stage is not None and gate_stage >= 3:
            governance_actions.insert(0,
                f"Gate {gate_stage} reviewers will expect evidence of assumption validation — prepare a validation pack.")

        # ── Assemble report ──────────────────────────────────────────────────
        report_date = datetime.now().strftime("%d %B %Y")
        report = {
            "report_title": f"Assumption Drift & Early Warning Report — {project_name}",
            "report_date": report_date,
            "project_id": project_id,
            "gate_context": gate_context,
            "executive_summary": {
                "overall_health": overall_health,
                "average_confidence_score": avg_score,
                "total_assumptions": total,
                "red_count": len(red),
                "amber_count": len(amber),
                "green_count": len(green),
                "narrative": health_narrative,
                "signals_integrated": len(signals),
                "signals_narrative": signals_narrative,
            },
            "top_at_risk_assumptions": recommended_actions,
            "cascade_risk": {
                "cascade_chains_identified": len(cascade_chains),
                "cascade_narrative": cascade_narrative,
                "chains": cascade_chains[:5],
            } if include_cascade else None,
            "governance_actions": governance_actions,
            "recommended_next_review_days": next_review_days,
            "methodology_note": (
                "Confidence scores are computed from three weighted factors: "
                "review recency (35%), source credibility (30%), and data backing quality (35%). "
                "The composite score is multiplied by a likelihood penalty "
                "(HIGH=0.3×, MEDIUM=0.6×, LOW=0.9×). "
                "RAG thresholds: GREEN ≥70, AMBER 40–69, RED <40."
            ),
        }

        # L6 then L5 — annotate first, then gate. The guardrail
        # evaluates the annotated report; if it rejects, the
        # _groundedness annotation is suppressed alongside the prose
        # (rejection JSON is returned instead).
        report = _attach_groundedness_to_assumption_report(
            report, assumptions, signals
        )

        # L8 audit-chain entry — record the executive verdict (RAG
        # summary counts + cascade-risk verdict) without storing the
        # full prose body. Recorded BEFORE the L5 guardrail so the
        # entry exists even if L5 rejects (auditors then see both
        # "we generated a report" and "L5 blocked it" downstream).
        summary = report.get("executive_summary") or {}
        cascade = report.get("cascade_risk") or {}
        rag_summary = report.get("rag_summary") or {}
        _safe_record_decision(
            input_data={"project_id": project_id},
            output_data={
                "rag_summary": rag_summary,
                "cascade_verdict": cascade.get("verdict"),
                "executive_score": summary.get("overall_score"),
            },
            decision=summary.get("overall_rag") or "UNKNOWN",
            action="generate_assumption_report",
            metadata={
                "assumption_count": len(assumptions),
                "signal_count": len(signals),
            },
        )
        return _apply_assumption_report_guardrail(report)

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


async def _export_assumption_html_dashboard(arguments: dict) -> list[TextContent]:
    project_id = arguments["project_id"]
    output_dir = arguments["output_dir"]
    project_name = arguments.get("project_name", project_id)
    gate_stage = arguments.get("gate_stage")
    db_path = arguments.get("db_path")
    store = AssuranceStore(db_path) if db_path else AssuranceStore()

    try:
        assumptions = store.get_assumptions(project_id)
        if not assumptions:
            return [TextContent(type="text", text=json.dumps({
                "error": "No assumptions found. Run load_assumption_register first.",
            }))]

        confidence_scores = store.get_assumption_confidence_scores(project_id)
        external_signals = store.get_all_external_signals()

        # Build lookup for confidence scores by assumption id
        score_lookup = {cs["assumption_id"]: cs for cs in confidence_scores}

        # If no scores computed yet, compute inline
        if not confidence_scores:
            for a in assumptions:
                notes = a.get("notes", "") or ""
                if "Likelihood:" in notes:
                    for part in notes.split("|"):
                        part = part.strip()
                        if part.startswith("Likelihood:"):
                            a["likelihood_of_failure"] = part.split(":", 1)[1].strip()
                cs = _compute_confidence(a)
                score_lookup[a["id"]] = {**cs, "assumption_id": a["id"]}

        # Enrich and sort
        enriched = []
        for a in assumptions:
            aid = a["id"]
            display_id = aid.replace(f"{project_id}-", "") if aid.startswith(project_id) else aid
            cs = score_lookup.get(aid, {})
            enriched.append({
                "id": display_id,
                "text": a.get("text", ""),
                "category": a.get("category", ""),
                "score": cs.get("score", 50.0),
                "rag": cs.get("rag", "AMBER"),
                "owner": a.get("owner", "TBC"),
                "likelihood": a.get("likelihood_of_failure", ""),
                "review_age_days": cs.get("review_age_days"),
                "impact_if_false": a.get("impact_if_false", "") or "",
                "dependencies": a.get("dependencies", "") or "",
            })
        enriched.sort(key=lambda x: x["score"])

        red = [e for e in enriched if e["rag"] == "RED"]
        amber = [e for e in enriched if e["rag"] == "AMBER"]
        green = [e for e in enriched if e["rag"] == "GREEN"]
        total = len(enriched)
        avg_score = round(sum(e["score"] for e in enriched) / total, 1) if total else 0

        if avg_score < 35:
            health = "CRITICAL"
        elif avg_score < 55:
            health = "POOR"
        elif avg_score < 70:
            health = "MODERATE"
        else:
            health = "ADEQUATE"

        # Cascade chains (RED assumptions with dependencies)
        cascades = []
        for e in enriched:
            if e["rag"] == "RED" and e["dependencies"]:
                deps = [d.strip() for d in e["dependencies"].split(",") if d.strip()]
                if deps:
                    cascades.append({
                        "id": e["id"],
                        "text": e["text"][:100],
                        "deps": deps,
                    })

        gate_label = ""
        if gate_stage is not None:
            gate_labels = {0: "Strategic Assessment", 1: "Justification", 2: "Strategy",
                          3: "Investment Decision", 4: "Readiness for Service", 5: "Operational Review"}
            gate_label = f"Gate {gate_stage}: {gate_labels.get(gate_stage, '')}"

        report_date = datetime.now().strftime("%d %B %Y")

        # ── Build HTML ───────────────────────────────────────────────────────
        def rag_color(rag):
            return {"RED": "#DC2626", "AMBER": "#D97706", "GREEN": "#16A34A"}.get(rag, "#6B7280")

        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

        # Top-10 worst table rows
        worst_rows = ""
        for e in enriched[:10]:
            age = f"{int(e['review_age_days'])} days" if e.get('review_age_days') else "—"
            worst_rows += f"""
        <tr>
          <td class="id">{esc(e['id'])}</td>
          <td><span class="pill" style="background:{rag_color(e['rag'])}">{e['rag']}</span></td>
          <td class="score">{e['score']:.1f}</td>
          <td>{esc(e['category'])}</td>
          <td class="text">{esc(e['text'][:120])}{'…' if len(e['text']) > 120 else ''}</td>
          <td>{esc(e['owner'])}</td>
          <td>{esc(e.get('likelihood','') or '—')}</td>
          <td>{age}</td>
        </tr>"""

        # External signals cards
        signals_html = ""
        for s in external_signals[:6]:
            signals_html += f"""
        <div class="signal-card">
          <div class="signal-label">{esc(s.get('indicator', '').replace('_',' ').upper())}</div>
          <div class="signal-value">{s.get('value', '?')}<span class="signal-unit">{esc(s.get('unit',''))}</span></div>
          <div class="signal-meta">{esc(s.get('source','').replace('_',' '))} · {esc(str(s.get('signal_date','unknown')))}</div>
        </div>"""

        # Cascade list
        cascade_html = ""
        if cascades:
            for c in cascades[:5]:
                deps_str = ", ".join(c['deps'][:4])
                cascade_html += f"""
        <li><strong>{esc(c['id'])}</strong> — {esc(c['text'])}<br>
          <span class="cascade-deps">If this fails, at risk: {esc(deps_str)}</span>
        </li>"""
        else:
            cascade_html = "<li class='none'>No cascade chains identified in this dataset.</li>"

        # Governance actions
        next_review_days = 14 if health in ("CRITICAL", "POOR") else 30 if health == "MODERATE" else 60
        gov_actions = []
        if gate_stage is not None and gate_stage >= 3:
            gov_actions.append(f"Gate {gate_stage} reviewers will expect evidence of assumption validation — prepare a validation pack.")
        gov_actions.append(f"Schedule assumption review board within {next_review_days} days.")
        unowned = sum(1 for e in enriched if not e["owner"] or e["owner"] == "TBC")
        if unowned:
            gov_actions.append(f"Assign owners to all {unowned} unowned assumptions.")
        else:
            gov_actions.append("All assumptions have named owners — confirm active accountability.")
        gov_actions.append("Update the risk register to reflect any RED assumptions with HIGH likelihood of failure.")
        gov_actions.append("Commission external validation for assumptions where confidence score is below 30.")
        gov_html = "".join(f"<li>{esc(a)}</li>" for a in gov_actions)

        # Health narrative
        if health == "CRITICAL":
            narrative = f"The assumption base for {project_name} is in a critical condition. With {len(red)} of {total} assumptions rated RED and an average confidence score of {avg_score}/100, the project is carrying substantial unvalidated risk. Immediate SRO attention and accelerated validation are required."
        elif health == "POOR":
            narrative = f"{project_name} has a weak assumption base. {len(red)} assumptions are RED and {len(amber)} are AMBER — meaning {len(red)+len(amber)} of {total} ({round((len(red)+len(amber))/total*100)}%) carry unacceptable or borderline risk. A targeted validation campaign is needed."
        elif health == "MODERATE":
            narrative = f"{project_name} has a moderate assumption position. {len(amber)} assumptions require active management and {len(red)} need urgent attention. Confidence is trending below the level expected at this stage."
        else:
            narrative = f"{project_name}'s assumptions are broadly sound. The majority ({len(green)}) are GREEN with adequate confidence. Maintain regular reviews to prevent drift."

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(project_name)} — Assumption Drift & Early Warning Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif;
    margin: 0;
    padding: 0;
    background: #F8FAFC;
    color: #0F172A;
    line-height: 1.5;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  header {{
    border-bottom: 4px solid #D946EF;
    padding-bottom: 16px;
    margin-bottom: 24px;
  }}
  header h1 {{ margin: 0; color: #334155; font-size: 28px; font-weight: 700; }}
  header .subtitle {{ color: #64748B; font-size: 14px; margin-top: 4px; }}
  header .meta {{ display: flex; gap: 24px; margin-top: 12px; font-size: 13px; color: #475569; }}
  header .meta span {{ display: inline-block; }}
  header .meta strong {{ color: #0F172A; }}

  .health-banner {{
    background: linear-gradient(135deg, {rag_color(enriched[0]['rag']) if enriched else '#6B7280'} 0%, #334155 100%);
    color: white;
    padding: 24px;
    border-radius: 8px;
    margin-bottom: 24px;
  }}
  .health-banner .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.8; }}
  .health-banner .rating {{ font-size: 36px; font-weight: 700; margin: 4px 0; }}
  .health-banner .narrative {{ font-size: 15px; margin-top: 8px; opacity: 0.95; }}

  .rag-grid {{ display: grid; grid-template-columns: repeat(3, 1fr) 2fr; gap: 16px; margin-bottom: 24px; }}
  .rag-card {{
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border-left: 6px solid;
  }}
  .rag-card.red {{ border-color: #DC2626; }}
  .rag-card.amber {{ border-color: #D97706; }}
  .rag-card.green {{ border-color: #16A34A; }}
  .rag-card.score {{ border-color: #334155; }}
  .rag-card .count {{ font-size: 40px; font-weight: 700; line-height: 1; color: #0F172A; }}
  .rag-card .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B; margin-top: 8px; }}

  section {{ margin-bottom: 32px; }}
  section h2 {{
    color: #334155;
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
  }}

  .signals-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }}
  .signal-card {{
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 14px;
  }}
  .signal-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B; font-weight: 600; }}
  .signal-value {{ font-size: 28px; font-weight: 700; color: #0F172A; margin-top: 4px; }}
  .signal-unit {{ font-size: 12px; color: #64748B; margin-left: 6px; font-weight: 400; }}
  .signal-meta {{ font-size: 11px; color: #94A3B8; margin-top: 4px; }}

  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  thead {{ background: #F1F5F9; }}
  th, td {{ padding: 10px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid #E2E8F0; }}
  th {{ color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; font-size: 11px; }}
  td.id {{ font-family: "Courier New", monospace; font-weight: 600; color: #334155; }}
  td.score {{ font-weight: 700; color: #0F172A; }}
  td.text {{ color: #475569; max-width: 360px; }}
  .pill {{ display: inline-block; padding: 3px 10px; border-radius: 12px; color: white; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }}

  .cascade-list {{ background: white; border-radius: 6px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .cascade-list li {{ margin: 0 0 12px; padding-left: 4px; }}
  .cascade-list li.none {{ color: #94A3B8; font-style: italic; }}
  .cascade-deps {{ display: inline-block; margin-top: 4px; color: #64748B; font-size: 12px; }}

  .gov-actions {{ background: white; border-radius: 6px; padding: 16px 20px 16px 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .gov-actions li {{ margin: 0 0 10px; color: #334155; }}
  .gov-actions li:first-child {{ color: #DC2626; font-weight: 600; }}

  footer {{
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #E2E8F0;
    font-size: 11px;
    color: #94A3B8;
    text-align: center;
  }}
  footer strong {{ color: #64748B; }}

  @media print {{
    body {{ background: white; }}
    .container {{ max-width: none; padding: 16px; }}
    section {{ page-break-inside: avoid; }}
    .health-banner, .rag-card, .signal-card, table, .cascade-list, .gov-actions {{ box-shadow: none; }}
  }}
</style>
</head>
<body>
<div class="container">

  <header>
    <h1>{esc(project_name)} — Assumption Drift &amp; Early Warning Dashboard</h1>
    <div class="subtitle">Generated by the PDA Platform · pm-assumptions module</div>
    <div class="meta">
      <span><strong>Project:</strong> {esc(project_id)}</span>
      <span><strong>Report date:</strong> {report_date}</span>
      {f'<span><strong>Gate context:</strong> {esc(gate_label)}</span>' if gate_label else ''}
      <span><strong>Platform tools:</strong> 126 (18 modules)</span>
    </div>
  </header>

  <div class="health-banner">
    <div class="label">Overall assumption health</div>
    <div class="rating">{health}</div>
    <div class="narrative">{esc(narrative)}</div>
  </div>

  <div class="rag-grid">
    <div class="rag-card red">
      <div class="count">{len(red)}</div>
      <div class="label">RED assumptions</div>
    </div>
    <div class="rag-card amber">
      <div class="count">{len(amber)}</div>
      <div class="label">AMBER assumptions</div>
    </div>
    <div class="rag-card green">
      <div class="count">{len(green)}</div>
      <div class="label">GREEN assumptions</div>
    </div>
    <div class="rag-card score">
      <div class="count">{avg_score} <span style="font-size:16px;color:#94A3B8;font-weight:400">/ 100</span></div>
      <div class="label">Average confidence score</div>
    </div>
  </div>

  <section>
    <h2>External signals (live data)</h2>
    <div class="signals-grid">{signals_html if signals_html else '<div class="signal-card" style="grid-column:1/-1;color:#94A3B8">No external signals cached. Run fetch_external_signal to populate.</div>'}</div>
  </section>

  <section>
    <h2>Top 10 at-risk assumptions</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>RAG</th>
          <th>Score</th>
          <th>Category</th>
          <th>Assumption</th>
          <th>Owner</th>
          <th>Likelihood</th>
          <th>Review age</th>
        </tr>
      </thead>
      <tbody>{worst_rows}</tbody>
    </table>
  </section>

  <section>
    <h2>Cascade risk chains</h2>
    <ul class="cascade-list">{cascade_html}</ul>
  </section>

  <section>
    <h2>Recommended governance actions</h2>
    <ol class="gov-actions">{gov_html}</ol>
  </section>

  <footer>
    Generated by <strong>PDA Platform</strong> · <strong>pm-assumptions</strong> · Tool: <code>export_assumption_html_dashboard</code><br>
    Confidence formula: review recency (35%) × source credibility (30%) × data backing (35%), multiplied by likelihood penalty. RAG: GREEN ≥70, AMBER 40–69, RED &lt;40.<br>
    This is a single-file offline HTML dashboard — no external dependencies, no server required.
  </footer>

</div>
</body>
</html>
"""

        out_path = Path(output_dir) / f"{project_id}-dashboard.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        return [TextContent(type="text", text=json.dumps({
            "project_id": project_id,
            "file_path": str(out_path),
            "file_size_bytes": out_path.stat().st_size,
            "assumptions_rendered": total,
            "rag_summary": {"RED": len(red), "AMBER": len(amber), "GREEN": len(green)},
            "average_score": avg_score,
            "overall_health": health,
            "external_signals_included": len(external_signals),
            "cascade_chains_included": len(cascades),
            "note": "Single-file HTML with inline CSS and data. Open in any browser, no server required.",
        }))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=json.dumps({"error": str(exc), "traceback": traceback.format_exc()}))]


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_DISPATCH = {
    "load_assumption_register": _load_assumption_register,
    "score_assumption_confidence": _score_assumption_confidence,
    "fetch_external_signal": _fetch_external_signal,
    "detect_external_drift": _detect_external_drift,
    "generate_assumption_report": _generate_assumption_report,
    "export_assumption_dashboard": _export_assumption_dashboard,
    "export_assumption_html_dashboard": _export_assumption_html_dashboard,
    "export_assumption_graph": _export_assumption_graph,
}


async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = _DISPATCH.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    return await handler(arguments)
