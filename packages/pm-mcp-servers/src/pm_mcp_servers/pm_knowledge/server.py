"""pm_knowledge — pre-loaded UK government project delivery knowledge base.

Eight tools:
  1. list_knowledge_categories   — discover what's available
  2. get_benchmark_data          — cost/schedule/DCA benchmarks by project type
  3. get_failure_patterns        — common failure modes with indicators and mitigations
  4. get_ipa_guidance            — IPA/HMT/Cabinet Office guidance references
  5. search_knowledge_base       — full-text search across all knowledge
  6. run_reference_class_check   — compare an estimate against the IPA benchmark distribution
  7. get_benchmark_percentile    — position a metric value in the benchmark distribution
  8. generate_premortem_questions — generate structured pre-mortem challenge questions for a gate review
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from .knowledge_base import (
    BENCHMARK_DATA,
    FAILURE_PATTERNS,
    GUIDANCE_REFERENCES,
    KNOWLEDGE_CATEGORIES,
    PREMORTEM_QUESTIONS,
    RISK_FLAG_QUESTIONS,
)

server = Server("pm-knowledge")

KNOWLEDGE_TOOLS: list[Tool] = [
    Tool(
        name="list_knowledge_categories",
        description=(
            "List all categories of pre-loaded knowledge available in the PDA Platform knowledge base. "
            "Returns benchmark data types (cost overrun, schedule slip, DCA distributions by project type), "
            "failure pattern domains and gate stages, and IPA/HMT guidance topics. "
            "Use this to discover what is available before calling other knowledge tools."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="get_benchmark_data",
        description=(
            "Retrieve statistical benchmark data for a specific project type and metric. "
            "Sources: IPA Annual Reports 2019-2024, NAO reports, GMPP data. "
            "Project types: IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE, HEALTH_AND_SOCIAL_CARE, CROSS_GOVERNMENT. "
            "Metrics: cost_overrun (mean/median/P80 %), schedule_slip (mean/median/P80 months, % late), "
            "dca_distribution (% at each DCA rating), common_overrun_drivers (list), "
            "optimism_bias_reference (HMT Green Book uplift ranges — CROSS_GOVERNMENT only)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_type": {
                    "type": "string",
                    "enum": ["IT_AND_DIGITAL", "INFRASTRUCTURE", "DEFENCE", "HEALTH_AND_SOCIAL_CARE", "CROSS_GOVERNMENT"],
                    "description": "Project type to retrieve benchmarks for.",
                },
                "metric": {
                    "type": "string",
                    "enum": ["cost_overrun", "schedule_slip", "dca_distribution", "common_overrun_drivers", "optimism_bias_reference", "all"],
                    "description": "Metric to retrieve. Use 'all' for the complete benchmark profile.",
                },
            },
            "required": ["project_type", "metric"],
        },
    ),
    Tool(
        name="get_failure_patterns",
        description=(
            "Retrieve common failure patterns identified by IPA and NAO research. "
            "Each pattern includes: description, early warning indicators, mitigation strategies, "
            "and IPA/NAO source references. "
            "Filter by domain (ALL, IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE, HEALTH_AND_SOCIAL_CARE) "
            "and/or gate stage (GATE_0 through GATE_5). "
            "Use this to cross-reference observed project indicators against known failure modes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ["ALL", "IT_AND_DIGITAL", "INFRASTRUCTURE", "DEFENCE", "HEALTH_AND_SOCIAL_CARE"],
                    "description": "Filter by project domain. 'ALL' returns patterns applicable to all domains.",
                },
                "gate": {
                    "type": "string",
                    "enum": ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "ANY"],
                    "description": "Filter by gate stage relevance. 'ANY' returns all patterns.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="get_ipa_guidance",
        description=(
            "Retrieve IPA, HM Treasury, or Cabinet Office guidance references on a specific topic. "
            "Topics: optimism_bias, green_book, cabinet_office_controls, ipa_annual_report, "
            "gmpp_reporting, benefits_management, schedule_management, project_delivery_functional_standard. "
            "Returns: summary, key thresholds/principles, and source URL. "
            "Use to cite authoritative guidance when making recommendations or assessing compliance."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [
                        "optimism_bias",
                        "green_book",
                        "cabinet_office_controls",
                        "ipa_annual_report",
                        "gmpp_reporting",
                        "benefits_management",
                        "schedule_management",
                        "project_delivery_functional_standard",
                        "all",
                    ],
                    "description": "Guidance topic to retrieve. Use 'all' for a full index.",
                },
            },
            "required": ["topic"],
        },
    ),
    Tool(
        name="search_knowledge_base",
        description=(
            "Full-text search across all knowledge in the PDA Platform knowledge base: "
            "benchmark data, failure patterns, and IPA/HMT guidance. "
            "Returns ranked results with the most relevant entries first. "
            "Use this when you are not sure which specific tool to call, or when you want "
            "to find all knowledge relevant to a topic (e.g. 'supplier risk', 'benefits owner', 'schedule float')."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Can be a keyword, phrase, or question.",
                },
                "category": {
                    "type": "string",
                    "enum": ["benchmark_data", "failure_patterns", "ipa_guidance", "all"],
                    "description": "Restrict search to a specific category. Default: 'all'.",
                    "default": "all",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="run_reference_class_check",
        description=(
            "Compare a submitted cost or schedule estimate against the IPA benchmark distribution "
            "for comparable completed government projects. Returns the approximate percentile the estimate "
            "sits at, an optimism bias risk flag if below P50, the benchmark distribution statistics, "
            "and a recommended adjusted value. "
            "Use at business case review points to detect systematic underestimation before it becomes a delivery problem. "
            "project_type: IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE, HEALTH_AND_SOCIAL_CARE, CROSS_GOVERNMENT. "
            "estimate_type: cost_overrun (submit as % above baseline) or schedule_slip (submit as months)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_type": {
                    "type": "string",
                    "enum": ["IT_AND_DIGITAL", "INFRASTRUCTURE", "DEFENCE", "HEALTH_AND_SOCIAL_CARE", "CROSS_GOVERNMENT"],
                    "description": "Type of project — used to select the appropriate benchmark cohort.",
                },
                "estimate_type": {
                    "type": "string",
                    "enum": ["cost_overrun", "schedule_slip"],
                    "description": "What is being estimated: cost_overrun (% above approved baseline) or schedule_slip (months beyond planned completion).",
                },
                "submitted_value": {
                    "type": "number",
                    "description": "The estimate being checked. For cost_overrun: percentage (e.g. 10 means 10% overrun). For schedule_slip: months (e.g. 3 means 3 months late).",
                },
            },
            "required": ["project_type", "estimate_type", "submitted_value"],
        },
    ),
    Tool(
        name="get_benchmark_percentile",
        description=(
            "Given a current performance metric value, return where it sits in the IPA benchmark distribution "
            "for comparable projects. Provides immediate context for performance numbers that otherwise "
            "lack a reference point. "
            "Example: 'Our CPI is 0.87 — is that normal for infrastructure projects at this stage?' "
            "project_type: IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE, HEALTH_AND_SOCIAL_CARE, CROSS_GOVERNMENT. "
            "metric: cost_overrun (%), schedule_slip (months), or dca_green_rate (%)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_type": {
                    "type": "string",
                    "enum": ["IT_AND_DIGITAL", "INFRASTRUCTURE", "DEFENCE", "HEALTH_AND_SOCIAL_CARE", "CROSS_GOVERNMENT"],
                },
                "metric": {
                    "type": "string",
                    "enum": ["cost_overrun", "schedule_slip", "dca_green_rate"],
                    "description": "The metric to benchmark against.",
                },
                "value": {
                    "type": "number",
                    "description": "The current value to position in the distribution.",
                },
            },
            "required": ["project_type", "metric", "value"],
        },
    ),
    Tool(
        name="generate_premortem_questions",
        description=(
            "Generate a set of structured pre-mortem challenge questions for a gate review, "
            "tailored to the IPA gate being reviewed and optional risk flags. "
            "Pre-mortem analysis — imagining the project has failed and asking what caused it — "
            "is an evidence-based technique for counteracting optimism bias and groupthink in "
            "governance forums. "
            "Returns 5-10 targeted questions drawn from a library keyed to gate stage and known risk patterns. "
            "gate: GATE_0 through GATE_5 or ANY. "
            "risk_flags: optional list from [optimism_bias, benefits_unowned, schedule_no_float, "
            "supplier_dependency, stale_risks, sro_capacity]."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "gate": {
                    "type": "string",
                    "enum": ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "ANY"],
                    "description": "IPA gate being reviewed.",
                },
                "risk_flags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["optimism_bias", "benefits_unowned", "schedule_no_float", "supplier_dependency", "stale_risks", "sro_capacity"],
                    },
                    "description": "Optional risk flags to add targeted questions for specific known risk patterns.",
                },
                "max_questions": {
                    "type": "integer",
                    "description": "Maximum number of questions to return (default 8).",
                    "default": 8,
                },
            },
            "required": ["gate"],
        },
    ),
]


# ── Handlers ──────────────────────────────────────────────────────────────────

async def _list_knowledge_categories(_arguments: dict[str, Any]) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(KNOWLEDGE_CATEGORIES, indent=2))]


async def _get_benchmark_data(arguments: dict[str, Any]) -> list[TextContent]:
    project_type = arguments["project_type"]
    metric = arguments["metric"]

    data = BENCHMARK_DATA.get(project_type)
    if not data:
        return [TextContent(type="text", text=json.dumps({"error": f"No benchmark data for project type: {project_type}"}))]

    if metric == "all":
        result = {"project_type": project_type, "benchmarks": data}
    else:
        metric_data = data.get(metric)
        if metric_data is None:
            available = list(data.keys())
            return [TextContent(type="text", text=json.dumps({
                "error": f"Metric '{metric}' not available for {project_type}",
                "available_metrics": available,
            }))]
        result = {"project_type": project_type, "metric": metric, "data": metric_data}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _get_failure_patterns(arguments: dict[str, Any]) -> list[TextContent]:
    domain = arguments.get("domain", "ALL")
    gate = arguments.get("gate", "ANY")

    patterns = FAILURE_PATTERNS

    if domain != "ALL":
        patterns = [p for p in patterns if domain in p["domains"] or "ALL" in p["domains"]]

    if gate != "ANY":
        patterns = [p for p in patterns if gate in p["gates"]]

    result = {
        "filters": {"domain": domain, "gate": gate},
        "count": len(patterns),
        "patterns": patterns,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _get_ipa_guidance(arguments: dict[str, Any]) -> list[TextContent]:
    topic = arguments["topic"]

    if topic == "all":
        index = [{"id": g["id"], "topic": g["topic"], "title": g["title"], "publisher": g["publisher"], "year": g["year"]} for g in GUIDANCE_REFERENCES]
        result = {"count": len(index), "guidance_index": index}
    else:
        matches = [g for g in GUIDANCE_REFERENCES if g["topic"] == topic]
        if not matches:
            available = [g["topic"] for g in GUIDANCE_REFERENCES]
            return [TextContent(type="text", text=json.dumps({"error": f"No guidance found for topic: {topic}", "available_topics": available}))]
        result = {"count": len(matches), "guidance": matches}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _search_knowledge_base(arguments: dict[str, Any]) -> list[TextContent]:
    query = arguments["query"].lower()
    category = arguments.get("category", "all")
    results: list[dict] = []

    def score(text: str) -> int:
        words = query.split()
        return sum(1 for w in words if w in text.lower())

    if category in ("all", "failure_patterns"):
        for p in FAILURE_PATTERNS:
            searchable = " ".join([
                p["name"], p["description"],
                " ".join(p["indicators"]),
                p["mitigation"],
                " ".join(p["domains"]),
            ])
            s = score(searchable)
            if s > 0:
                results.append({"category": "failure_pattern", "score": s, "id": p["id"], "name": p["name"], "description": p["description"][:200] + "...", "indicators_count": len(p["indicators"])})

    if category in ("all", "ipa_guidance"):
        for g in GUIDANCE_REFERENCES:
            searchable = " ".join([g["topic"], g["title"], g["summary"]])
            s = score(searchable)
            if s > 0:
                results.append({"category": "ipa_guidance", "score": s, "id": g["id"], "topic": g["topic"], "title": g["title"], "summary": g["summary"][:200] + "..."})

    if category in ("all", "benchmark_data"):
        for ptype, metrics in BENCHMARK_DATA.items():
            for mname, mdata in metrics.items():
                searchable = ptype + " " + mname + " " + str(mdata)
                s = score(searchable)
                if s > 0:
                    results.append({"category": "benchmark_data", "score": s, "project_type": ptype, "metric": mname, "preview": str(mdata)[:150]})

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:10]

    return [TextContent(type="text", text=json.dumps({"query": arguments["query"], "category": category, "count": len(results), "results": results}, indent=2))]


async def _run_reference_class_check(arguments: dict[str, Any]) -> list[TextContent]:
    project_type = arguments["project_type"]
    estimate_type = arguments["estimate_type"]
    submitted_value = arguments["submitted_value"]

    data = BENCHMARK_DATA.get(project_type, {}).get(estimate_type)
    if not data:
        return [TextContent(type="text", text=json.dumps({"error": f"No benchmark data for {project_type}/{estimate_type}"}))]

    mean = data.get("mean_percent") or data.get("mean_months", 0)
    median = data.get("median_percent") or data.get("median_months", 0)
    p80 = data.get("p80_percent") or data.get("p80_months", 0)

    # Approximate percentile using simple linear interpolation between known points
    # Points: P0≈0, P50=median, P80=p80, P100=p80*2 (rough approximation)
    if submitted_value <= 0:
        approx_percentile = 5
    elif submitted_value <= median:
        approx_percentile = int(50 * submitted_value / median) if median > 0 else 50
    elif submitted_value <= p80:
        approx_percentile = int(50 + 30 * (submitted_value - median) / (p80 - median)) if p80 > median else 65
    else:
        approx_percentile = min(99, int(80 + 19 * (submitted_value - p80) / p80)) if p80 > 0 else 85

    optimism_bias_risk = submitted_value < median
    recommended_minimum = median
    recommended_p80 = p80

    unit = "%" if estimate_type == "cost_overrun" else " months"

    interpretation = (
        f"The submitted estimate of {submitted_value}{unit} sits at approximately the "
        f"{approx_percentile}th percentile of the IPA benchmark distribution for "
        f"{project_type.replace('_', ' ').title()} projects."
    )
    if optimism_bias_risk:
        interpretation += (
            f" This is BELOW the median outcome ({median}{unit}), which means more than half of "
            f"comparable completed projects experienced a worse outcome than this estimate assumes. "
            f"This is a strong indicator of optimism bias and should be challenged."
        )
    elif submitted_value <= p80:
        interpretation += (
            f" This is within the normal range but below the P80 outcome ({p80}{unit}). "
            f"For budget-setting purposes, HM Treasury guidance recommends using P80."
        )
    else:
        interpretation += (
            f" This is above the P80 outcome for comparable projects, suggesting a conservative "
            f"estimate or that this project has specific characteristics that warrant higher provisions."
        )

    result = {
        "project_type": project_type,
        "estimate_type": estimate_type,
        "submitted_value": submitted_value,
        "approximate_percentile": approx_percentile,
        "optimism_bias_risk": optimism_bias_risk,
        "benchmark_distribution": {
            "median": median,
            "p80": p80,
            "mean": mean,
            "source": data.get("source", "IPA Annual Report"),
            "sample_size": data.get("sample_size", "Not specified"),
        },
        "recommendations": {
            "minimum_provision": f"{recommended_minimum}{unit}",
            "p80_provision": f"{recommended_p80}{unit}",
            "guidance": "HM Treasury Green Book requires optimism bias uplifts to be applied to raw estimates. Budget setting should use P80, not P50.",
        },
        "interpretation": interpretation,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _get_benchmark_percentile(arguments: dict[str, Any]) -> list[TextContent]:
    project_type = arguments["project_type"]
    metric = arguments["metric"]
    value = arguments["value"]

    if metric == "dca_green_rate":
        dist = BENCHMARK_DATA.get(project_type, {}).get("dca_distribution", {})
        benchmark_value = dist.get("green", 9)
        result = {
            "project_type": project_type,
            "metric": metric,
            "submitted_value": value,
            "benchmark_green_rate": benchmark_value,
            "interpretation": (
                f"The IPA benchmark Green rate for {project_type.replace('_', ' ').title()} projects "
                f"is {benchmark_value}%. "
                + ("This project exceeds the benchmark." if value > benchmark_value
                   else "This project is at or below the benchmark Green rate.")
            ),
            "source": BENCHMARK_DATA.get(project_type, {}).get("dca_distribution", {}).get("source", "IPA Annual Report 2023"),
        }
    else:
        data = BENCHMARK_DATA.get(project_type, {}).get(metric, {})
        if not data:
            return [TextContent(type="text", text=json.dumps({"error": f"No data for {project_type}/{metric}"}))]

        mean = data.get("mean_percent") or data.get("mean_months", 0)
        median = data.get("median_percent") or data.get("median_months", 0)
        p80 = data.get("p80_percent") or data.get("p80_months", 0)

        if value <= median:
            position = "below the median (better than 50% of comparable projects)"
        elif value <= p80:
            position = "between the median and P80 (worse than 50% but better than 80% of comparable projects)"
        else:
            position = "above P80 (worse than 80% of comparable projects)"

        result = {
            "project_type": project_type,
            "metric": metric,
            "submitted_value": value,
            "benchmark": {"median": median, "p80": p80, "mean": mean, "source": data.get("source")},
            "position": position,
            "interpretation": f"A value of {value} for {metric} on a {project_type.replace('_', ' ').title()} project is {position}.",
        }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _generate_premortem_questions(arguments: dict[str, Any]) -> list[TextContent]:
    gate = arguments.get("gate", "ANY")
    risk_flags = arguments.get("risk_flags", [])
    max_questions = arguments.get("max_questions", 8)

    questions = []

    # Gate-specific questions
    gate_qs = PREMORTEM_QUESTIONS.get(gate, [])
    questions.extend([{"source": f"gate_{gate.lower()}", **q} for q in gate_qs])

    # Universal questions (always include a subset)
    universal = PREMORTEM_QUESTIONS.get("ANY", [])
    questions.extend([{"source": "universal", **q} for q in universal[:3]])

    # Risk flag targeted questions
    flag_questions = []
    for flag in risk_flags:
        for q_text in RISK_FLAG_QUESTIONS.get(flag, []):
            flag_questions.append({
                "source": f"risk_flag_{flag}",
                "question": q_text,
                "targets": [flag],
                "failure_mode": flag.replace("_", " ").title(),
            })
    questions.extend(flag_questions)

    # Deduplicate and limit
    seen = set()
    unique_questions = []
    for q in questions:
        if q["question"] not in seen:
            seen.add(q["question"])
            unique_questions.append(q)

    unique_questions = unique_questions[:max_questions]

    result = {
        "gate": gate,
        "risk_flags": risk_flags,
        "question_count": len(unique_questions),
        "questions": unique_questions,
        "usage_note": (
            "These questions are designed to be used in a gate review forum to surface risks "
            "that optimism bias and groupthink might otherwise suppress. Present each question "
            "to the programme team and require a specific, evidence-based answer — not a reassurance."
        ),
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ── MCP handlers ──────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return KNOWLEDGE_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handlers = {
        "list_knowledge_categories": _list_knowledge_categories,
        "get_benchmark_data": _get_benchmark_data,
        "get_failure_patterns": _get_failure_patterns,
        "get_ipa_guidance": _get_ipa_guidance,
        "search_knowledge_base": _search_knowledge_base,
        "run_reference_class_check": _run_reference_class_check,
        "get_benchmark_percentile": _get_benchmark_percentile,
        "generate_premortem_questions": _generate_premortem_questions,
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
