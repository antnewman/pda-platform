"""PM-Synthesis MCP server — AI-powered executive briefing tools.

Tools:
  1. summarise_project_health — Gather multi-source assurance data and call the
     Anthropic Claude API to produce a plain-English executive briefing tailored
     to the specified audience (SRO, PMO, or BOARD).
  2. compare_project_health  — Gather data for 2–5 projects and call the
     Anthropic Claude API to produce a comparative briefing highlighting the
     healthiest and highest-risk projects.

Both tools operate within a UK government project assurance context and use
IPA/HM Treasury terminology throughout (SRO, gate review, DCA, IPA, DWP, etc.).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

SYNTHESIS_TOOLS: list[Tool] = [
    Tool(
        name="summarise_project_health",
        description=(
            "Gather assurance data from all available sources (compliance scores, "
            "open actions, assumption drift, ARMM maturity, gate readiness, benefits "
            "health) and produce a plain-English executive briefing via the Anthropic "
            "Claude API. Tone and length are tailored to the specified audience: "
            "SRO (4-6 decision-focused bullets), PMO (prose + action list), or "
            "BOARD (2-3 sentences, RAG status + headline finding). "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "audience": {
                    "type": "string",
                    "enum": ["SRO", "PMO", "BOARD"],
                    "description": (
                        "Target audience controlling tone and length. "
                        "SRO: 4-6 decision-focused bullets. "
                        "PMO: prose paragraph plus action list. "
                        "BOARD: 2-3 sentences, RAG status and headline finding. "
                        "Defaults to SRO."
                    ),
                    "default": "SRO",
                },
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "compliance",
                            "actions",
                            "assumptions",
                            "armm",
                            "gate_readiness",
                            "benefits",
                        ],
                    },
                    "description": (
                        "Which data sections to include. "
                        "Defaults to all available sections."
                    ),
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="compare_project_health",
        description=(
            "Gather assurance data for 2–5 projects and produce a comparative "
            "briefing via the Anthropic Claude API identifying the healthiest "
            "project, the highest-risk project, and any common issues across the "
            "portfolio. Returns both a Claude-generated comparative paragraph and "
            "a structured comparison table. "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 5,
                    "description": "List of 2–5 project identifiers to compare.",
                },
                "db_path": {
                    "type": "string",
                    "description": (
                        "Optional path to the SQLite store. "
                        "Defaults to ~/.pm_data_tools/store.db"
                    ),
                },
            },
            "required": ["project_ids"],
        },
    ),
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ALL_SECTIONS = [
    "compliance",
    "actions",
    "assumptions",
    "armm",
    "gate_readiness",
    "benefits",
]

_MAX_TOKENS: dict[str, int] = {
    "BOARD": 500,
    "SRO": 800,
    "PMO": 1000,
}

_SYSTEM_PROMPT = """\
You are an expert UK government project assurance analyst working within the
Infrastructure and Projects Authority (IPA) framework. You write plain-English
briefings for senior decision-makers using IPA/HM Treasury terminology:
SRO (Senior Responsible Owner), DCA (Delivery Confidence Assessment), gate review
(IPA gates 0–5), OBC (Outline Business Case), FBC (Full Business Case), ARMM
(Assurance and Risk Management Maturity), RAG status (Red/Amber/Green),
and HM Treasury Green Book benefit classification.

You always:
- Use UK English spelling (programme, organisation, realisation, behaviour).
- Write with authority and precision; avoid hedging or vague language.
- Flag items that require senior decision or immediate action.
- Present RAG statuses where appropriate.
- Never invent data; base every finding on the structured context provided.
- Do not include any preamble such as "Here is the briefing" — start directly.
"""

_AUDIENCE_INSTRUCTIONS: dict[str, str] = {
    "SRO": (
        "Write exactly 4 to 6 bullet points. Each bullet must be decision-focused "
        "and flag any item requiring SRO action. Lead each bullet with a bold "
        "keyword (e.g. **Compliance**, **Actions**, **Gate Readiness**). "
        "Be direct and concise — the SRO has limited time."
    ),
    "PMO": (
        "Write one clear prose paragraph summarising overall project health, "
        "followed by a numbered action list of specific items the PMO team "
        "should address. The prose should be technical but accessible. "
        "The action list should prioritise the most time-sensitive items first."
    ),
    "BOARD": (
        "Write 2 to 3 sentences only. Open with the overall RAG/DCA status, "
        "state one headline finding (positive or risk), and close with a single "
        "recommended board-level decision or note. "
        "Do not include bullet points or lists."
    ),
}


def _get_store(arguments: dict[str, Any]) -> Any:
    """Return a process-cached AssuranceStore (audit finding P2.F03)."""
    from pm_data_tools.db.store import get_store

    raw_db_path = arguments.get("db_path")
    db_path = Path(raw_db_path) if raw_db_path else None
    return get_store(db_path)


def _gather_project_data(
    store: Any,
    project_id: str,
    sections: list[str],
) -> tuple[dict[str, Any], list[str]]:
    """Gather assurance data for a single project from the store.

    Returns a tuple of (context_dict, missing_sections) where missing_sections
    lists section names that returned no records.
    """
    ctx: dict[str, Any] = {"project_id": project_id}
    missing: list[str] = []

    if "compliance" in sections:
        scores = store.get_confidence_scores(project_id)
        if scores:
            latest = scores[-1]
            # Compute a simple trend: compare last two scores if available.
            trend = "stable"
            if len(scores) >= 2:
                delta = latest["score"] - scores[-2]["score"]
                if delta > 1:
                    trend = "improving"
                elif delta < -1:
                    trend = "deteriorating"
            ctx["compliance"] = {
                "latest_score": latest["score"],
                "trend": trend,
                "timestamp": latest["timestamp"],
                "dimension_scores": latest.get("dimension_scores", {}),
            }
        else:
            missing.append("compliance")

    if "actions" in sections:
        actions = store.get_recommendations(project_id)
        if actions:
            open_actions = [a for a in actions if a.get("status") == "OPEN"]
            recurring = [
                a for a in open_actions if a.get("recurrence_of") is not None
            ]
            ctx["actions"] = {
                "total": len(actions),
                "open": len(open_actions),
                "recurring_open": len(recurring),
            }
        else:
            missing.append("actions")

    if "assumptions" in sections:
        assumptions = store.get_assumptions(project_id)
        if assumptions:
            # Gather drift severity from assumption_validations for each assumption.
            severity_counts: dict[str, int] = {
                "NONE": 0,
                "MINOR": 0,
                "MODERATE": 0,
                "SIGNIFICANT": 0,
                "CRITICAL": 0,
            }
            for assumption in assumptions:
                validations = store.get_assumption_validations(
                    assumption_id=assumption["id"]
                )
                if validations:
                    latest_val = validations[-1]
                    sev = latest_val.get("severity", "NONE")
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                    else:
                        severity_counts["NONE"] += 1
                else:
                    severity_counts["NONE"] += 1

            ctx["assumptions"] = {
                "total": len(assumptions),
                "drift_by_severity": severity_counts,
            }
        else:
            missing.append("assumptions")

    if "armm" in sections:
        armm_rows = store.get_armm_assessments(project_id)
        if armm_rows:
            latest_armm = armm_rows[-1]
            ctx["armm"] = {
                "overall_level": latest_armm["overall_level"],
                "overall_score_pct": latest_armm["overall_score_pct"],
                "assessed_at": latest_armm["assessed_at"],
                "criteria_met": latest_armm["criteria_met"],
                "criteria_total": latest_armm["criteria_total"],
            }
        else:
            missing.append("armm")

    if "gate_readiness" in sections:
        gate_rows = store.get_gate_readiness_history(project_id)
        if gate_rows:
            latest_gate = gate_rows[-1]
            ctx["gate_readiness"] = {
                "gate": latest_gate["gate"],
                "readiness": latest_gate["readiness"],
                "composite_score": latest_gate["composite_score"],
                "assessed_at": latest_gate["assessed_at"],
            }
        else:
            missing.append("gate_readiness")

    if "benefits" in sections:
        benefits = store.get_benefits(project_id)
        if benefits:
            by_status: dict[str, int] = {}
            for b in benefits:
                s = b.get("status", "UNKNOWN")
                by_status[s] = by_status.get(s, 0) + 1
            ctx["benefits"] = {
                "total": len(benefits),
                "by_status": by_status,
            }
        else:
            missing.append("benefits")

    return ctx, missing


def _build_user_prompt(ctx: dict[str, Any], audience: str) -> str:
    """Build the user prompt for the Claude API call."""
    lines: list[str] = [
        f"Project: {ctx['project_id']}",
        f"Audience: {audience}",
        "",
        _AUDIENCE_INSTRUCTIONS[audience],
        "",
        "--- Assurance Data ---",
    ]

    compliance = ctx.get("compliance")
    if compliance:
        lines.append(
            f"Compliance score: {compliance['latest_score']:.1f}/100 "
            f"(trend: {compliance['trend']}, as at {compliance['timestamp']})."
        )
        dim = compliance.get("dimension_scores")
        if dim:
            dim_parts = ", ".join(
                f"{k}: {v:.1f}" for k, v in sorted(dim.items())
            )
            lines.append(f"  Dimension scores: {dim_parts}.")

    actions = ctx.get("actions")
    if actions:
        lines.append(
            f"Actions: {actions['open']} open of {actions['total']} total; "
            f"{actions['recurring_open']} recurring open action(s)."
        )

    assumptions = ctx.get("assumptions")
    if assumptions:
        sev = assumptions["drift_by_severity"]
        lines.append(
            f"Assumptions: {assumptions['total']} registered. "
            f"Drift by severity — "
            f"Critical: {sev.get('CRITICAL', 0)}, "
            f"Significant: {sev.get('SIGNIFICANT', 0)}, "
            f"Moderate: {sev.get('MODERATE', 0)}, "
            f"Minor: {sev.get('MINOR', 0)}, "
            f"None: {sev.get('NONE', 0)}."
        )

    armm = ctx.get("armm")
    if armm:
        lines.append(
            f"ARMM maturity: Level {armm['overall_level']} "
            f"({armm['overall_score_pct']:.1f}%, "
            f"{armm['criteria_met']}/{armm['criteria_total']} criteria met, "
            f"assessed {armm['assessed_at']})."
        )

    gate_readiness = ctx.get("gate_readiness")
    if gate_readiness:
        lines.append(
            f"Gate readiness: Gate {gate_readiness['gate']}, "
            f"readiness {gate_readiness['readiness']}, "
            f"composite score {gate_readiness['composite_score']:.1f} "
            f"(assessed {gate_readiness['assessed_at']})."
        )

    benefits = ctx.get("benefits")
    if benefits:
        status_parts = ", ".join(
            f"{k}: {v}" for k, v in sorted(benefits["by_status"].items())
        )
        lines.append(
            f"Benefits: {benefits['total']} registered ({status_parts})."
        )

    lines.append("")
    lines.append(
        "Write the briefing now, following the audience instructions above exactly."
    )
    return "\n".join(lines)


def _call_claude(
    user_prompt: str,
    max_tokens: int,
    api_key: str,
) -> str:
    """Call the Anthropic Claude API synchronously and return the response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _summarise_project_health(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Gather multi-source data and produce an AI executive briefing."""
    try:
        project_id = arguments["project_id"]
        audience = arguments.get("audience", "SRO")
        sections = arguments.get("sections") or _ALL_SECTIONS

        # Validate audience
        if audience not in _MAX_TOKENS:
            return [
                TextContent(
                    type="text",
                    text=f"Error: audience must be one of SRO, PMO, BOARD — got '{audience}'.",
                )
            ]

        store = _get_store(arguments)
        ctx, missing = _gather_project_data(store, project_id, sections)

        # Check whether the project has any data at all.
        data_keys = [k for k in ctx if k != "project_id"]
        if not data_keys:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No assurance data found for project '{project_id}'. "
                        "Please run 'create_project_from_profile' or "
                        "'run_assurance_workflow' to populate data before "
                        "requesting a synthesis briefing."
                    ),
                )
            ]

        # Build confidence note for missing sections.
        confidence_note = ""
        if missing:
            confidence_note = (
                f"[Note: No data available for the following sections: "
                f"{', '.join(missing)}. The briefing is based on available data only.]\n\n"
            )

        # Get API key and call Claude.
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raw_output = {
                "project_id": project_id,
                "audience": audience,
                "error": "ANTHROPIC_API_KEY environment variable not set.",
                "structured_data": ctx,
            }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(raw_output, indent=2, default=str),
                )
            ]

        user_prompt = _build_user_prompt(ctx, audience)
        max_tokens = _MAX_TOKENS[audience]

        try:
            briefing_text = _call_claude(user_prompt, max_tokens, api_key)
        except Exception as api_err:  # anthropic.APIError and subclasses
            raw_output = {
                "project_id": project_id,
                "audience": audience,
                "error": f"Anthropic API call failed: {api_err}",
                "structured_data": ctx,
            }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(raw_output, indent=2, default=str),
                )
            ]

        full_text = f"{confidence_note}{briefing_text}"
        return [TextContent(type="text", text=full_text)]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def _compare_project_health(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Gather data for multiple projects and produce a comparative briefing."""
    try:
        project_ids: list[str] = arguments["project_ids"]

        if not (2 <= len(project_ids) <= 5):
            return [
                TextContent(
                    type="text",
                    text=(
                        "Error: compare_project_health requires between 2 and 5 "
                        f"project IDs — {len(project_ids)} provided."
                    ),
                )
            ]

        store = _get_store(arguments)

        # Gather data for each project across all sections.
        project_data: dict[str, dict[str, Any]] = {}
        for pid in project_ids:
            ctx, _ = _gather_project_data(store, pid, _ALL_SECTIONS)
            project_data[pid] = ctx

        # Build comparison table.
        comparison: list[dict[str, Any]] = []
        for pid in project_ids:
            ctx = project_data[pid]
            row: dict[str, Any] = {"project_id": pid}

            compliance = ctx.get("compliance")
            row["compliance_score"] = (
                compliance["latest_score"] if compliance else None
            )
            row["compliance_trend"] = (
                compliance["trend"] if compliance else None
            )

            actions = ctx.get("actions")
            row["open_actions"] = actions["open"] if actions else None
            row["recurring_actions"] = (
                actions["recurring_open"] if actions else None
            )

            armm = ctx.get("armm")
            row["armm_level"] = armm["overall_level"] if armm else None
            row["armm_score_pct"] = armm["overall_score_pct"] if armm else None

            gate = ctx.get("gate_readiness")
            row["gate"] = gate["gate"] if gate else None
            row["gate_readiness"] = gate["readiness"] if gate else None
            row["gate_score"] = gate["composite_score"] if gate else None

            benefits = ctx.get("benefits")
            row["benefits_total"] = benefits["total"] if benefits else None

            comparison.append(row)

        # Build prompt for Claude comparative briefing.
        comparison_lines: list[str] = [
            "You are comparing the following projects on UK government assurance data.",
            "",
            "Write a 3 to 5 sentence comparative briefing identifying:",
            "  1. Which project is currently healthiest and why.",
            "  2. Which project carries the most risk and what the primary risk is.",
            "  3. Any common issues appearing across multiple projects.",
            "",
            "Use UK English and IPA terminology. Do not include preamble.",
            "",
            "--- Project Comparison Data ---",
        ]

        for row in comparison:
            pid = row["project_id"]
            parts: list[str] = [f"Project {pid}:"]
            if row["compliance_score"] is not None:
                parts.append(
                    f"compliance {row['compliance_score']:.1f}/100 "
                    f"({row['compliance_trend']})"
                )
            if row["open_actions"] is not None:
                parts.append(
                    f"{row['open_actions']} open action(s) "
                    f"({row['recurring_actions']} recurring)"
                )
            if row["armm_level"] is not None:
                parts.append(
                    f"ARMM Level {row['armm_level']} "
                    f"({row['armm_score_pct']:.1f}%)"
                )
            if row["gate_readiness"] is not None:
                parts.append(
                    f"Gate {row['gate']} readiness {row['gate_readiness']} "
                    f"(score {row['gate_score']:.1f})"
                )
            if row["benefits_total"] is not None:
                parts.append(f"{row['benefits_total']} benefit(s) registered")
            comparison_lines.append("; ".join(parts) + ".")

        comparison_lines.append("")
        comparison_lines.append("Write the comparative briefing now.")

        user_prompt = "\n".join(comparison_lines)

        # Get API key and call Claude.
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        comparative_text: str | None = None

        if not api_key:
            comparative_text = (
                "[ANTHROPIC_API_KEY not set — comparative narrative unavailable.]"
            )
        else:
            try:
                comparative_text = _call_claude(
                    user_prompt=user_prompt,
                    max_tokens=600,
                    api_key=api_key,
                )
            except Exception as api_err:
                comparative_text = (
                    f"[Anthropic API call failed: {api_err} — "
                    "structured comparison data below.]"
                )

        output = {
            "comparative_briefing": comparative_text,
            "comparison_table": comparison,
        }
        return [TextContent(type="text", text=json.dumps(output, indent=2, default=str))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]
