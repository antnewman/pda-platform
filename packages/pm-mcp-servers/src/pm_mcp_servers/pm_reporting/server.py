"""pm_reporting — IPA-format governance document generation.

Five tools:
  1. generate_gate_review_summary   — IPA Gate Review Summary with DCA rating and conditions
  2. generate_sro_dashboard         — One-page SRO dashboard (deterministic, no Claude)
  3. generate_board_exception_report — Board-format exception report (Claude-synthesised)
  4. generate_portfolio_summary     — Cross-project portfolio narrative (Claude-synthesised)
  5. generate_pir_template          — Post-Implementation Review template (Claude-synthesised)
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

server = Server("pm-reporting")

GATE_NAMES = {
    0: "Strategic Assessment",
    1: "Business Justification",
    2: "Delivery Strategy",
    3: "Investment Decision",
    4: "Readiness for Service",
    5: "Benefits Evaluation",
}

REPORTING_TOOLS: list[Tool] = [
    Tool(
        name="generate_gate_review_summary",
        description=(
            "Generate an IPA-format Gate Review Summary document for a project. "
            "Gathers risks, gate readiness history, benefits, financial data, assurance scores, "
            "and change requests from the store, then uses Claude to synthesise a structured "
            "markdown document with DCA rating, conditions, recommendations, and per-dimension "
            "RAG assessment. Suitable for direct submission to an IPA or departmental gate review. "
            "gate_number: 0 (Strategic Assessment) through 5 (Benefits Evaluation). "
            "Returns a markdown string ready for export."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project identifier.",
                },
                "gate_number": {
                    "type": "integer",
                    "description": "IPA gate number (0–5).",
                    "minimum": 0,
                    "maximum": 5,
                },
                "reviewer_name": {
                    "type": "string",
                    "description": "Name of the reviewing practitioner. Defaults to 'Independent Reviewer'.",
                },
                "include_recommendations": {
                    "type": "boolean",
                    "description": "Whether to include a Recommended Actions section. Defaults to true.",
                    "default": True,
                },
            },
            "required": ["project_id", "gate_number"],
        },
    ),
    Tool(
        name="generate_sro_dashboard",
        description=(
            "Generate a one-page SRO Dashboard for a project. "
            "Deterministic assembly of key delivery metrics — DCA rating, gate stage, EV metrics (SPI/CPI), "
            "financial performance, top risks, and benefits status — into a structured markdown table. "
            "No Claude required; returns immediately. "
            "Ideal for weekly or monthly SRO reporting packs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project identifier.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="generate_board_exception_report",
        description=(
            "Generate a Board-format Exception Report containing only items requiring escalation. "
            "Uses Claude to translate technical delivery data into board language: "
            "non-technical, decision-focused Situation / Implication / Decision Required structure. "
            "Includes a recommended board resolution. Suitable for submission to ARAC, Investment Committee, "
            "or departmental board. "
            "reporting_period: optional label such as 'Q1 2026/27'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project identifier.",
                },
                "reporting_period": {
                    "type": "string",
                    "description": "Reporting period label (e.g. 'Q1 2026/27'). Optional.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="generate_portfolio_summary",
        description=(
            "Generate a cross-project Portfolio Summary narrative for a portfolio committee. "
            "For each project: DCA rating, SPI, CPI, top risk, and benefits RAG. "
            "Uses Claude to identify common themes, systemic risks, and recommended interventions "
            "across the portfolio. Returns a structured markdown document. "
            "project_ids: list of project identifiers to include in the portfolio view."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of project identifiers to include.",
                    "minItems": 1,
                },
                "portfolio_name": {
                    "type": "string",
                    "description": "Name for the portfolio. Defaults to 'Portfolio'.",
                    "default": "Portfolio",
                },
            },
            "required": ["project_ids"],
        },
    ),
    Tool(
        name="generate_pir_template",
        description=(
            "Generate a Post-Implementation Review (PIR) template pre-populated with all available "
            "project data from the store. Includes: delivery metrics vs business case (schedule, cost, "
            "benefits), benefits realised vs planned, closed risks that materialised, lessons learned "
            "if pm-lessons data is available, and recommendations for future projects. "
            "Uses Claude to write narrative sections. Returns a complete markdown PIR template "
            "ready for review by the project team. "
            "closure_date: optional ISO date (e.g. '2026-03-31') for the PIR."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project identifier.",
                },
                "closure_date": {
                    "type": "string",
                    "description": "Project closure date as ISO date string (e.g. '2026-03-31'). Optional.",
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="export_sro_dashboard_data",
        description=(
            "Export SRO Dashboard data as a static JSON file for the Universal Dashboard Specification "
            "(UDS) Renderer. Gathers delivery metrics — DCA rating, gate stage, EV metrics (SPI/CPI), "
            "financial performance, top risks, and benefits status — assembles panel-level data, and "
            "writes it to a JSON file that the UDS Renderer can consume directly. "
            "Returns the output file path and a localhost URL to open the dashboard in the UDS Renderer. "
            "Requires the UDS Renderer to be running on http://localhost:5173. "
            "output_dir: path to a directory where the JSON data file will be written "
            "(e.g. path to uds-renderer/public/data)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project identifier.",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to write the panel data JSON file.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store. Defaults to ~/.pm_data_tools/store.db",
                },
            },
            "required": ["project_id", "output_dir"],
        },
    ),
]


# ── Data gathering helpers ─────────────────────────────────────────────────────

def _get_store():
    """Return an AssuranceStore instance."""
    from pm_data_tools.db.store import AssuranceStore
    return AssuranceStore()


def _gather_project_data(project_id: str) -> dict[str, Any]:
    """Gather all available data for a project from the store.

    Returns a dict with keys for each data type. Each value is either
    a list/dict of data or an error string if gathering failed.
    """
    data: dict[str, Any] = {"project_id": project_id}

    store = _get_store()

    # Risks
    try:
        data["risks"] = store.get_risks(project_id)
    except Exception as exc:
        data["risks"] = f"[unavailable: {exc}]"

    # Gate readiness history
    try:
        data["gate_readiness"] = store.get_gate_readiness_history(project_id)
    except Exception as exc:
        data["gate_readiness"] = f"[unavailable: {exc}]"

    # Benefits
    try:
        data["benefits"] = store.get_benefits(project_id)
    except Exception as exc:
        data["benefits"] = f"[unavailable: {exc}]"

    # Financial baselines
    try:
        data["financial_baselines"] = store.get_financial_baselines(project_id)
    except Exception as exc:
        data["financial_baselines"] = f"[unavailable: {exc}]"

    # Financial actuals
    try:
        data["financial_actuals"] = store.get_financial_actuals(project_id)
    except Exception as exc:
        data["financial_actuals"] = f"[unavailable: {exc}]"

    # Financial forecasts (EAC)
    try:
        data["financial_forecasts"] = store.get_financial_forecasts(project_id)
    except Exception as exc:
        data["financial_forecasts"] = f"[unavailable: {exc}]"

    # Assurance / NISTA confidence scores
    try:
        data["confidence_scores"] = store.get_confidence_scores(project_id)
    except Exception as exc:
        data["confidence_scores"] = f"[unavailable: {exc}]"

    # Change requests
    try:
        data["change_requests"] = store.get_change_requests(project_id)
    except Exception as exc:
        data["change_requests"] = f"[unavailable: {exc}]"

    # ARMM assessments
    try:
        data["armm_assessments"] = store.get_armm_assessments(project_id)
    except Exception as exc:
        data["armm_assessments"] = f"[unavailable: {exc}]"

    # Lessons learned (from pm-lessons module, stored in the lessons table)
    try:
        data["lessons"] = store.get_project_lessons(project_id)
    except Exception as exc:
        data["lessons"] = f"[unavailable: {exc}]"

    # Latest simulation run
    try:
        data["simulation"] = store.get_latest_simulation(project_id, "schedule")
    except Exception as exc:
        data["simulation"] = f"[unavailable: {exc}]"

    return data


def _has_any_data(project_data: dict[str, Any]) -> bool:
    """Return True if at least one data source returned non-empty results."""
    for key, val in project_data.items():
        if key == "project_id":
            continue
        if isinstance(val, list) and len(val) > 0:
            return True
        if isinstance(val, dict) and val:
            return True
    return False


def _get_anthropic_client():
    """Return an Anthropic client or None if key not set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


def _call_claude(client, prompt: str, max_tokens: int = 2000) -> str:
    """Call Claude and return the text response."""
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ── Tool handlers ──────────────────────────────────────────────────────────────

async def _generate_gate_review_summary(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    gate_number: int = int(arguments["gate_number"])
    reviewer_name: str = arguments.get("reviewer_name") or "Independent Reviewer"
    include_recommendations: bool = arguments.get("include_recommendations", True)

    client = _get_anthropic_client()
    if client is None:
        return [TextContent(type="text", text=json.dumps({
            "error": "ANTHROPIC_API_KEY environment variable is not set. "
                     "This tool requires the Anthropic API to generate the gate review summary."
        }))]

    project_data = _gather_project_data(project_id)

    if not _has_any_data(project_data):
        return [TextContent(type="text", text=json.dumps({
            "error": f"No data found for project '{project_id}'. "
                     "Load project data using pm-data, pm-risk, pm-brm, and pm-financial tools first."
        }))]

    today = date.today().isoformat()
    gate_name = GATE_NAMES.get(gate_number, f"Gate {gate_number}")

    data_summary = json.dumps(project_data, indent=2, default=str)

    recs_instruction = (
        "Include a '## Recommended Actions' section with a numbered list of recommended actions."
        if include_recommendations
        else "Do NOT include a Recommended Actions section."
    )

    prompt = f"""You are an experienced IPA (Infrastructure and Projects Authority) gate reviewer.
Using the project data below, generate a formal Gate {gate_number} Review Summary in IPA format.

Project ID: {project_id}
Gate: {gate_number} — {gate_name}
Date: {today}
Reviewer: {reviewer_name}

PROJECT DATA:
{data_summary}

Generate the following document structure exactly:

# Gate {gate_number} Review Summary — {project_id}
**Delivery Confidence Assessment:** [GREEN/AMBER-GREEN/AMBER/AMBER-RED/RED — select the most appropriate based on the evidence]
**Gate:** {gate_number} — {gate_name}  **Date:** {today}  **Reviewer:** {reviewer_name}

## Executive Summary
[2–3 paragraphs summarising the project's delivery position, key issues, and overall confidence]

## Strengths
- [bullet list of genuine project strengths based on the data]

## Areas Requiring Management Attention
- [bullet list of specific issues, gaps, or concerns]

## CONDITIONS
*The following conditions must be satisfied before the project may proceed:*
- [condition 1 — write specific, actionable conditions based on the data, or write "No conditions identified." if the project is in good shape]

{recs_instruction}

## Assessment by Dimension
| Dimension | RAG | Commentary |
|---|---|---|
| Strategic Context and Benefits | [🟢/🟡/🔴] | [one sentence commentary] |
| Leadership and Stakeholder Management | [🟢/🟡/🔴] | [one sentence commentary] |
| Risk Management | [🟢/🟡/🔴] | [one sentence commentary] |
| Governance and Assurance | [🟢/🟡/🔴] | [one sentence commentary] |
| Financials | [🟢/🟡/🔴] | [one sentence commentary] |
| Delivery Approach and Schedule | [🟢/🟡/🔴] | [one sentence commentary] |
| People and Capability | [🟢/🟡/🔴] | [one sentence commentary] |
| Commercial and Procurement | [🟢/🟡/🔴] | [one sentence commentary] |

---
*This summary was generated by the PDA Platform and requires review by a qualified assurance practitioner before submission.*

Be specific. Reference actual data values (risk scores, financial figures, benefit targets) where available.
Use IPA language — be direct, evidence-based, and avoid vague reassurances.
If data is missing for a dimension, note the gap rather than assuming performance is good."""

    try:
        document = _call_claude(client, prompt, max_tokens=3000)
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Claude API call failed: {exc}"}))]

    return [TextContent(type="text", text=document)]


async def _generate_sro_dashboard(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    today = date.today().isoformat()

    project_data = _gather_project_data(project_id)

    if not _has_any_data(project_data):
        return [TextContent(type="text", text=json.dumps({
            "error": f"No data found for project '{project_id}'. "
                     "Load project data using pm-data, pm-risk, pm-brm, and pm-financial tools first."
        }))]

    # ── Derive metrics ────────────────────────────────────────────────────────

    # DCA rating from latest gate readiness assessment
    gate_readiness = project_data.get("gate_readiness") or []
    if isinstance(gate_readiness, list) and gate_readiness:
        latest_gate = gate_readiness[-1]
        dca_rating = latest_gate.get("readiness", "UNKNOWN")
        gate_label = f"Gate {latest_gate.get('gate', '?')}"
    else:
        dca_rating = "No assessment"
        gate_label = "Not assessed"

    dca_icon = {"GREEN": "✅", "AMBER-GREEN": "🟡", "AMBER": "⚠️", "AMBER-RED": "⚠️", "RED": "🔴"}.get(dca_rating, "—")

    # Outstanding conditions (open recommendations)
    change_requests = project_data.get("change_requests") or []
    open_changes = [c for c in (change_requests if isinstance(change_requests, list) else [])
                    if c.get("status") in ("SUBMITTED", "UNDER_REVIEW")]
    outstanding_conditions = len(open_changes)

    # EV metrics from latest simulation
    simulation = project_data.get("simulation")
    spi_val: str = "N/A"
    cpi_val: str = "N/A"
    spi_icon: str = "—"
    cpi_icon: str = "—"
    if isinstance(simulation, dict) and simulation:
        p50 = simulation.get("p50_days")
        if p50:
            spi_val = f"P50={p50}d"
            spi_icon = "⚠️"

    # Financial data
    baselines = project_data.get("financial_baselines") or []
    forecasts = project_data.get("financial_forecasts") or []
    bac: float | None = None
    eac: float | None = None
    if isinstance(baselines, list) and baselines:
        bac = baselines[-1].get("total_budget")
    if isinstance(forecasts, list) and forecasts:
        eac = forecasts[-1].get("eac")

    if bac and eac:
        variance_pct = ((eac - bac) / bac * 100) if bac else 0
        eac_vs_bac = f"£{eac:,.0f} vs £{bac:,.0f}"
        fin_icon = "✅" if variance_pct <= 5 else ("⚠️" if variance_pct <= 20 else "🔴")
        fin_variance = f"{variance_pct:+.1f}%"
    else:
        eac_vs_bac = "No financial data"
        fin_icon = "—"
        fin_variance = "—"

    # Top risks
    risks = project_data.get("risks") or []
    top_risks = (sorted(
        [r for r in (risks if isinstance(risks, list) else []) if r.get("status") == "OPEN"],
        key=lambda r: r.get("risk_score", 0),
        reverse=True,
    ))[:5]

    # Benefits
    benefits = project_data.get("benefits") or []
    benefits_list = [b for b in (benefits if isinstance(benefits, list) else [])][:5]

    # ── Assemble dashboard ────────────────────────────────────────────────────

    lines = [
        f"# SRO Dashboard — {project_id}",
        f"*Generated: {today}*",
        "",
        "## Delivery Status",
        "| Metric | Value | Status |",
        "|---|---|---|",
        f"| DCA Rating | {dca_rating} | {dca_icon} |",
        f"| Current Gate | {gate_label} | — |",
        f"| Open Change Requests | {outstanding_conditions} | {'🔴' if outstanding_conditions > 3 else ('⚠️' if outstanding_conditions > 0 else '✅')} |",
        f"| Schedule (P50) | {spi_val} | {spi_icon} |",
        f"| EAC vs BAC | {eac_vs_bac} | {fin_icon} ({fin_variance}) |",
        "",
    ]

    if top_risks:
        lines += [
            "## Top Risks",
            "| Risk | Score | Owner | Status |",
            "|---|---|---|---|",
        ]
        for r in top_risks:
            mitigation_note = r.get("notes") or "No mitigation noted"
            owner = r.get("owner") or "Unassigned"
            score = r.get("risk_score", "?")
            score_icon = "🔴" if int(score) >= 15 else ("⚠️" if int(score) >= 9 else "🟡")
            lines.append(
                f"| {r.get('title', '?')} | {score} {score_icon} | {owner} | {r.get('status', '?')} |"
            )
        lines.append("")
    else:
        lines += ["## Top Risks", "*No open risks recorded.*", ""]

    if benefits_list:
        lines += [
            "## Benefits Status",
            "| Benefit | Target Value | Status |",
            "|---|---|---|",
        ]
        for b in benefits_list:
            target = b.get("target_value")
            target_str = f"£{target:,.0f}" if target else "TBC"
            lines.append(f"| {b.get('title', '?')} | {target_str} | {b.get('status', '?')} |")
        lines.append("")
    else:
        lines += ["## Benefits Status", "*No benefits recorded.*", ""]

    lines += ["## Key Actions Required"]
    actions = []
    if outstanding_conditions > 0:
        actions.append(f"Review and resolve {outstanding_conditions} outstanding change request(s).")
    high_risks = [r for r in top_risks if int(r.get("risk_score", 0)) >= 15]
    for r in high_risks[:3]:
        actions.append(f"Address critical risk: {r.get('title')} (score {r.get('risk_score')}).")
    if not actions:
        actions.append("No immediate escalation actions identified.")
    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. {action}")

    document = "\n".join(lines)
    return [TextContent(type="text", text=document)]


async def _generate_board_exception_report(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    reporting_period: str = arguments.get("reporting_period") or date.today().strftime("%B %Y")

    client = _get_anthropic_client()
    if client is None:
        return [TextContent(type="text", text=json.dumps({
            "error": "ANTHROPIC_API_KEY environment variable is not set. "
                     "This tool requires the Anthropic API to generate the board exception report."
        }))]

    project_data = _gather_project_data(project_id)

    if not _has_any_data(project_data):
        return [TextContent(type="text", text=json.dumps({
            "error": f"No data found for project '{project_id}'. "
                     "Load project data using pm-data, pm-risk, pm-brm, and pm-financial tools first."
        }))]

    today = date.today().isoformat()
    data_summary = json.dumps(project_data, indent=2, default=str)

    prompt = f"""You are a senior programme adviser preparing a board exception report.
The report must be written in board language: non-technical, decision-focused, and concise.
Only include items that require board awareness or a board decision. Do not describe routine activity.

Project ID: {project_id}
Reporting Period: {reporting_period}
Report Date: {today}

PROJECT DATA:
{data_summary}

Generate a board exception report with this structure:

# Board Exception Report — {project_id}
**Reporting Period:** {reporting_period}  **Date:** {today}

## Exception Items

For each significant exception (aim for 2–5 items maximum — only escalation-worthy items):

### Exception [N]: [Short title]
**Situation:** [What has happened or is happening — one paragraph, plain English, no jargon]
**Implication:** [What this means for delivery, cost, benefits, or public value — one paragraph]
**Decision Required:** [Specific decision the board needs to make, or explicit note if board awareness only]

## Recommended Board Resolution
[1–2 paragraphs with a clear recommended course of action for the board]

---
*This report was generated by the PDA Platform. All figures should be verified against the latest project data before submission.*

Rules:
- Write for a non-specialist board member
- Be specific about financial figures, dates, and risk scores where data exists
- If no exceptions warrant escalation, say so clearly and briefly
- Do not pad — a short accurate report is better than a long vague one"""

    try:
        document = _call_claude(client, prompt, max_tokens=2000)
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Claude API call failed: {exc}"}))]

    return [TextContent(type="text", text=document)]


async def _generate_portfolio_summary(arguments: dict[str, Any]) -> list[TextContent]:
    project_ids: list[str] = arguments["project_ids"]
    portfolio_name: str = arguments.get("portfolio_name") or "Portfolio"

    client = _get_anthropic_client()
    if client is None:
        return [TextContent(type="text", text=json.dumps({
            "error": "ANTHROPIC_API_KEY environment variable is not set. "
                     "This tool requires the Anthropic API to generate the portfolio summary."
        }))]

    today = date.today().isoformat()

    # Gather per-project summaries
    per_project: list[dict[str, Any]] = []
    for pid in project_ids:
        project_data = _gather_project_data(pid)

        # DCA
        gate_readiness = project_data.get("gate_readiness") or []
        if isinstance(gate_readiness, list) and gate_readiness:
            dca = gate_readiness[-1].get("readiness", "UNKNOWN")
        else:
            dca = "No assessment"

        # Top risk
        risks = project_data.get("risks") or []
        open_risks = sorted(
            [r for r in (risks if isinstance(risks, list) else []) if r.get("status") == "OPEN"],
            key=lambda r: r.get("risk_score", 0),
            reverse=True,
        )
        top_risk = open_risks[0] if open_risks else None

        # Financial
        baselines = project_data.get("financial_baselines") or []
        forecasts = project_data.get("financial_forecasts") or []
        bac = baselines[-1].get("total_budget") if isinstance(baselines, list) and baselines else None
        eac = forecasts[-1].get("eac") if isinstance(forecasts, list) and forecasts else None
        if bac and eac:
            cpi_approx = bac / eac if eac else 1.0
            cpi_str = f"{cpi_approx:.2f}"
        else:
            cpi_str = "N/A"

        # Benefits
        benefits = project_data.get("benefits") or []
        benefits_count = len(benefits) if isinstance(benefits, list) else 0

        # Latest simulation for SPI
        simulation = project_data.get("simulation")
        spi_str = "N/A"
        if isinstance(simulation, dict) and simulation and simulation.get("p50_days"):
            spi_str = f"P50={simulation['p50_days']}d"

        per_project.append({
            "project_id": pid,
            "dca_rating": dca,
            "cpi_approx": cpi_str,
            "spi_summary": spi_str,
            "top_risk": (f"{top_risk['title']} (score {top_risk['risk_score']})" if top_risk else "None"),
            "benefits_count": benefits_count,
        })

    project_table = json.dumps(per_project, indent=2)
    all_data = {pid: _gather_project_data(pid) for pid in project_ids}
    all_data_summary = json.dumps(all_data, indent=2, default=str)

    prompt = f"""You are a senior portfolio analyst preparing a summary for a portfolio committee.

Portfolio: {portfolio_name}
Date: {today}
Projects: {', '.join(project_ids)}

PER-PROJECT METRICS:
{project_table}

DETAILED DATA (all projects):
{all_data_summary}

Generate a portfolio summary with this structure:

# Portfolio Summary — {portfolio_name}
*Date: {today}*

## Portfolio Scorecard
| Project | DCA Rating | CPI | SPI | Top Risk | Benefits |
|---|---|---|---|---|---|
[One row per project — use the per-project metrics above]

## Portfolio Health Narrative
[2–3 paragraphs on overall portfolio health, delivery confidence distribution, and financial position]

## Common Themes and Systemic Risks
[Bullet list identifying risks or issues that appear across multiple projects — systemic patterns that a single-project view would miss]

## Recommended Portfolio Interventions
[Numbered list of specific portfolio-level actions the committee should consider — prioritised by impact]

---
*This summary was generated by the PDA Platform. Verify all metrics against source data before distribution.*

Be specific. If DCA ratings are mostly AMBER, say so. Identify systemic issues honestly."""

    try:
        document = _call_claude(client, prompt, max_tokens=2000)
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Claude API call failed: {exc}"}))]

    return [TextContent(type="text", text=document)]


async def _generate_pir_template(arguments: dict[str, Any]) -> list[TextContent]:
    project_id: str = arguments["project_id"]
    closure_date: str = arguments.get("closure_date") or date.today().isoformat()

    client = _get_anthropic_client()
    if client is None:
        return [TextContent(type="text", text=json.dumps({
            "error": "ANTHROPIC_API_KEY environment variable is not set. "
                     "This tool requires the Anthropic API to generate the PIR template."
        }))]

    project_data = _gather_project_data(project_id)

    # Determine if lessons data is available
    lessons = project_data.get("lessons") or []
    has_lessons = isinstance(lessons, list) and len(lessons) > 0

    # Identify closed/materialised risks
    risks = project_data.get("risks") or []
    closed_risks = [r for r in (risks if isinstance(risks, list) else []) if r.get("status") == "CLOSED"]

    # Benefits realised vs planned
    benefits = project_data.get("benefits") or []
    realised_benefits = [b for b in (benefits if isinstance(benefits, list) else [])
                         if b.get("status") in ("REALISED", "PARTIALLY_REALISED")]

    today = date.today().isoformat()
    data_summary = json.dumps(project_data, indent=2, default=str)

    prompt = f"""You are a project delivery expert writing a Post-Implementation Review (PIR) template.
Pre-populate all sections with the available data. Use [PLACEHOLDER] markers where human input is still needed.
The PIR will be reviewed by the project team and used to extract lessons for future projects.

Project ID: {project_id}
Closure Date: {closure_date}
PIR Prepared: {today}

PROJECT DATA:
{data_summary}

Closed Risks ({len(closed_risks)}): {json.dumps([r.get('title') for r in closed_risks])}
Lessons Available: {'Yes — ' + str(len(lessons)) + ' records' if has_lessons else 'No lessons data in store'}

Generate a complete PIR with this structure:

# Post-Implementation Review — {project_id}
**Closure Date:** {closure_date}  **PIR Date:** {today}  **Prepared by:** [PLACEHOLDER — name]  **Approved by:** [PLACEHOLDER — SRO name]

## 1. Project Overview
[2 paragraphs: what the project set out to do, key context, and delivery approach]

## 2. Delivery Performance vs Business Case

### Schedule
| Metric | Planned | Actual | Variance |
|---|---|---|---|
[Pre-populate from store data where available, otherwise [PLACEHOLDER]]

### Cost
| Metric | Budget (BAC) | Outturn (EAC) | Variance |
|---|---|---|---|
[Pre-populate from store data where available, otherwise [PLACEHOLDER]]

### Benefits Delivery
| Benefit | Target Value | Realised | Status |
|---|---|---|---|
[Pre-populate from benefits store — {len(benefits)} benefits recorded]

## 3. Risks That Materialised
[Summary of risks that were CLOSED — {len(closed_risks)} closed risks. Include which were mitigated successfully and which caused impact.]

## 4. What Went Well
[Bullet list of genuine successes, evidence-based from the data]

## 5. What Could Have Been Done Better
[Bullet list of specific improvement areas — honest and evidence-based]

## 6. Lessons Learned
{'[Pre-populated from ' + str(len(lessons)) + ' lessons records in store:]' if has_lessons else '[PLACEHOLDER — lessons not yet recorded in the store. Complete this section before sign-off.]'}
{chr(10).join(['- ' + str(l.get('title', '')) + ': ' + str(l.get('recommendation', l.get('description', '')))[:100] for l in (lessons[:10] if has_lessons else [])]) if has_lessons else ''}

## 7. Recommendations for Future Projects
[Numbered list of specific, actionable recommendations for future programme teams based on the experience of this project]

## 8. Outstanding Actions
| Action | Owner | Target Date |
|---|---|---|
| [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

## Sign-off
| Role | Name | Date | Signature |
|---|---|---|---|
| SRO | [PLACEHOLDER] | [PLACEHOLDER] | |
| Project Manager | [PLACEHOLDER] | [PLACEHOLDER] | |
| Benefits Owner | [PLACEHOLDER] | [PLACEHOLDER] | |

---
*This PIR template was generated by the PDA Platform and pre-populated with store data. All [PLACEHOLDER] fields require human completion before submission.*

Be specific. Reference actual figures from the store data. Write narrative sections in plain English.
Flag where data gaps exist rather than inventing numbers."""

    try:
        document = _call_claude(client, prompt, max_tokens=4000)
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Claude API call failed: {exc}"}))]

    return [TextContent(type="text", text=document)]


async def _export_sro_dashboard_data(arguments: dict[str, Any]) -> list[TextContent]:
    """Export SRO dashboard panel data as static JSON for the UDS Renderer."""
    import json as _json
    from pathlib import Path

    project_id: str = arguments["project_id"]
    output_dir: str = arguments["output_dir"]
    raw_db_path = arguments.get("db_path")

    try:
        from pm_data_tools.db.store import AssuranceStore
        store = AssuranceStore(db_path=Path(raw_db_path) if raw_db_path else None)

        project_data = _gather_project_data(project_id)

        # ── DCA rating ────────────────────────────────────────────────────────
        gate_readiness = project_data.get("gate_readiness") or []
        if isinstance(gate_readiness, list) and gate_readiness:
            latest_gate = gate_readiness[-1]
            dca_rating = str(latest_gate.get("readiness", "UNKNOWN"))
            gate_label = f"Gate {latest_gate.get('gate', '?')}"
        else:
            dca_rating = "No assessment"
            gate_label = "Not assessed"

        # ── Financial ─────────────────────────────────────────────────────────
        baselines = project_data.get("financial_baselines") or []
        forecasts = project_data.get("financial_forecasts") or []
        bac: float | None = baselines[-1].get("total_budget") if isinstance(baselines, list) and baselines else None
        eac: float | None = forecasts[-1].get("eac") if isinstance(forecasts, list) and forecasts else None
        if bac and eac:
            variance_pct = round((eac - bac) / bac * 100, 1)
            eac_label = f"£{eac:,.0f}"
            bac_label = f"£{bac:,.0f}"
        else:
            variance_pct = None
            eac_label = "N/A"
            bac_label = "N/A"

        # ── Schedule simulation ───────────────────────────────────────────────
        simulation = project_data.get("simulation")
        p50_days = simulation.get("p50_days") if isinstance(simulation, dict) else None
        p80_days = simulation.get("p80_days") if isinstance(simulation, dict) else None

        # ── Open change requests ──────────────────────────────────────────────
        change_requests = project_data.get("change_requests") or []
        open_changes = [c for c in (change_requests if isinstance(change_requests, list) else [])
                        if c.get("status") in ("SUBMITTED", "UNDER_REVIEW")]

        # ── Risks ─────────────────────────────────────────────────────────────
        risks = project_data.get("risks") or []
        top_risks = sorted(
            [r for r in (risks if isinstance(risks, list) else []) if r.get("status") == "OPEN"],
            key=lambda r: r.get("risk_score", 0),
            reverse=True,
        )[:5]

        # ── Benefits ──────────────────────────────────────────────────────────
        benefits = project_data.get("benefits") or []
        benefits_list = [b for b in (benefits if isinstance(benefits, list) else [])][:5]

        # ── Assemble panels ───────────────────────────────────────────────────
        panels: dict[str, Any] = {
            # KPI panels
            "dca_rating": {"value": dca_rating},
            "gate_status": {"value": gate_label},
            "open_changes": {"value": len(open_changes)},
            "schedule_p50": {"value": p50_days, "label": f"{p50_days}d" if p50_days else "N/A"},
            "schedule_p80": {"value": p80_days, "label": f"{p80_days}d" if p80_days else "N/A"},
            "financial_eac": {"value": eac_label},
            "financial_bac": {"value": bac_label},
            "financial_variance_pct": {"value": variance_pct},
            # Risk table
            "top_risks_table": {
                "rows": [
                    {
                        "title": r.get("title", ""),
                        "risk_score": r.get("risk_score", 0),
                        "owner": r.get("owner") or "Unassigned",
                        "status": r.get("status", "OPEN"),
                        "category": r.get("category", ""),
                    }
                    for r in top_risks
                ]
            },
            # Benefits table
            "benefits_table": {
                "rows": [
                    {
                        "title": b.get("title", ""),
                        "target_value": b.get("target_value"),
                        "status": b.get("status", ""),
                        "owner": b.get("owner") or "Unassigned",
                    }
                    for b in benefits_list
                ]
            },
        }

        # ── Write to file ─────────────────────────────────────────────────────
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{project_id}-sro-data.json"
        file_path.write_text(_json.dumps(panels, indent=2, default=str))

        output: dict[str, Any] = {
            "file_path": str(file_path),
            "panel_count": len(panels),
            "project_id": project_id,
            "url": f"http://localhost:5173/?dashboard=sro-dashboard.uds.yaml&project_id={project_id}&data_mode=static",
        }
        return [TextContent(type="text", text=_json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        import traceback
        return [TextContent(type="text", text=f"Error: {exc}\n{traceback.format_exc()}")]


# ── MCP handlers ───────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return REPORTING_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handlers = {
        "generate_gate_review_summary": _generate_gate_review_summary,
        "generate_sro_dashboard": _generate_sro_dashboard,
        "generate_board_exception_report": _generate_board_exception_report,
        "generate_portfolio_summary": _generate_portfolio_summary,
        "generate_pir_template": _generate_pir_template,
        "export_sro_dashboard_data": _export_sro_dashboard_data,
    }
    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    return await handler(arguments)


def main() -> None:
    import asyncio
    from mcp.server.stdio import stdio_server

    async def _run() -> None:
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
