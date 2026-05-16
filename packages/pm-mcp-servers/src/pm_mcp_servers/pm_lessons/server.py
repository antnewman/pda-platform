"""PM Lessons MCP Server.

AI-powered extraction of lessons learned from gate review reports and PIRs,
and a searchable cross-project lessons store.

Five tools:
  1. extract_lessons          — AI extraction from gate review / PIR text
  2. get_project_lessons      — retrieve stored lessons for a project
  3. search_lessons           — keyword search across all projects' lessons
  4. get_systemic_patterns    — AI pattern analysis across the full lessons corpus
  5. generate_lessons_section — AI-written lessons section for PIR / gate review
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from pm_data_tools.db.store import AssuranceStore
from pm_mcp_servers._groundedness import compute_groundedness
from pm_mcp_servers._guardrails import (
    Severity,
    Verdict,
    build_forbidden_phrase_rule,
    evaluate,
)
from pm_mcp_servers._quality import derive_quality_from_groundedness

server = Server("pm-lessons")


# ─────────────────────────────────────────────────────────────────────────
# Layer 5 — Output-guardrail policy for AI-written lessons sections
# ─────────────────────────────────────────────────────────────────────────
# A lessons learned section in a PIR or gate review carries forward
# guidance to future projects, so a forbidden phrase (overclaim,
# template leak) survives well beyond the current report. The policy
# blocks both failure modes.
_LESSONS_SECTION_POLICY = [
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
            "INSERT LESSON HERE",
            "[placeholder]",
        ],
        severity=Severity.BLOCK,
    ),
]


# ─────────────────────────────────────────────────────────────────────────
# Layer 6 — Groundedness footer for the lessons section
# ─────────────────────────────────────────────────────────────────────────
# The lessons section's "answer" is the markdown document. Its
# "sources" are the stored lesson rows (the raw data the section
# claims to summarise). We append a visible groundedness footer +
# HTML-comment JSON block — same shape as B10's pm-reporting footer.


def _build_lessons_sources(lessons: list[dict]) -> list[dict[str, object]]:
    """One source per lesson row, plus a combined-corpus source.

    Per-lesson sources let the per_source_citation_scores identify
    which specific lesson supports which fragment of the section.
    The corpus source is the union, used as the high-level reference.
    """
    sources: list[dict[str, object]] = []
    if not lessons:
        return sources
    sources.append(
        {
            "id": "lessons_corpus",
            "content": json.dumps(lessons, default=str),
        }
    )
    for lesson in lessons:
        lid = lesson.get("id") or "lesson"
        sources.append(
            {
                "id": f"lesson_{lid}",
                "content": json.dumps(lesson, default=str),
            }
        )
    return sources


def _attach_groundedness_to_lessons_section(
    document: str,
    lessons: list[dict],
) -> str:
    """Append a groundedness footer to the lessons-section markdown."""
    sources = _build_lessons_sources(lessons)
    if not document.strip():
        return document
    if not sources:
        return (
            document
            + "\n\n---\n*Groundedness: not computed — no lessons in "
            "the store to ground against.*\n"
        )
    result = compute_groundedness(
        document, sources, query="generate_lessons_section"
    )
    rd = result.to_dict()
    quality = derive_quality_from_groundedness(rd)
    # Both groundedness and quality live in the same HTML-comment
    # payload for parser convenience.
    combined = dict(rd)
    combined["_quality"] = quality
    terms = rd.get("ungrounded_terms", []) or []
    terms_preview = ", ".join(terms[:8])
    if len(terms) > 8:
        terms_preview += f", … (+{len(terms) - 8} more)"
    if not terms_preview:
        terms_preview = "(none)"
    human_line = (
        f"*Groundedness: {rd['overall_score']:.2f} ({rd['verdict']}). "
        f"Ungrounded terms: {terms_preview}*"
    )
    machine_block = "<!-- _groundedness: " + json.dumps(combined, default=str) + " -->"
    return f"{document}\n\n---\n{human_line}\n\n{machine_block}\n"


def _apply_lessons_section_guardrail(document: str) -> list[TextContent]:
    """Apply the L5 deterministic guardrail to a lessons-section markdown
    document.

    APPROVED: pass through unchanged as markdown.
    FLAGGED: prepend a guardrail-notice blockquote, keep the document.
    REJECTED: replace the document with structured error JSON so a
        downstream PIR/gate-review consumer cannot render forbidden
        prose.
    """
    result = evaluate({"document": document}, _LESSONS_SECTION_POLICY)
    if result.verdict == Verdict.REJECTED:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "guardrail_rejected",
                        "verdict": result.verdict.value,
                        "message": (
                            "Generated lessons section contained one or "
                            "more phrases forbidden by the L5 deterministic "
                            "policy. Inspect `triggered` for the failing "
                            "rules; the original markdown has been "
                            "suppressed."
                        ),
                        "triggered": [e.to_dict() for e in result.triggered],
                        "evaluations": [e.to_dict() for e in result.evaluations],
                    }
                ),
            )
        ]
    if result.verdict == Verdict.FLAGGED:
        notice_lines = [
            "> ⚠️ **L5 guardrail flagged this lessons section.** Reviewer attention required.",
            ">",
        ]
        for triggered in result.triggered:
            notice_lines.append(
                f"> - {triggered.rule_name}: {triggered.message}"
            )
        document = "\n".join(notice_lines) + "\n\n" + document
    return [TextContent(type="text", text=document)]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

_EXTRACT_SYSTEM_PROMPT = (
    "You are a UK government project delivery assurance expert specialising in "
    "lessons learned analysis. Extract structured lessons from the provided "
    "document text. Return ONLY a valid JSON array — no prose, no markdown fences. "
    "Each element must have these exact keys:\n"
    "  title         (string, ≤10 words)\n"
    "  category      (one of: GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE)\n"
    "  phase         (one of: INITIATION, PLANNING, DELIVERY, CLOSURE, ANY)\n"
    "  root_cause    (string, 1–2 sentences describing the underlying cause)\n"
    "  recommendation (string, 1–2 sentences, actionable, what to do differently next time)\n"
    "  severity      (one of: HIGH, MEDIUM, LOW)\n"
    "  source_excerpt (verbatim phrase from the text, ≤50 words)\n"
    "Extract only concrete, specific lessons. Omit vague platitudes. "
    "If no lessons are present in the text return an empty array []."
)

_PATTERNS_SYSTEM_PROMPT = (
    "You are a UK government portfolio assurance analyst. You will be given a "
    "JSON array of lessons learned from multiple government projects. Identify "
    "patterns that recur across multiple projects — systemic issues rather than "
    "one-off problems. Return ONLY a valid JSON array of pattern objects — no "
    "prose, no markdown fences. Each pattern object must have:\n"
    "  pattern              (string, concise name for the systemic issue)\n"
    "  category             (one of: GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE)\n"
    "  occurrences          (integer, number of lessons that exemplify this pattern)\n"
    "  projects_affected    (array of project_id strings)\n"
    "  evidence             (array of lesson title strings that exemplify this pattern)\n"
    "  recommendation       (string, systemic portfolio-level action to address this)\n"
    "Order by occurrences descending. Only include patterns seen in 2+ lessons."
)

_PIR_FORMAT_PROMPT = (
    "Write a structured 'Lessons Learned' section for a Post-Implementation Review (PIR). "
    "Group lessons by category (GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE). "
    "For each category: summarise the key root causes, then list prioritised recommendations. "
    "Use professional UK government project delivery language. Return markdown."
)

_GATE_FORMAT_PROMPT = (
    "Write a concise 'Lessons Learned' section for a gate review report. "
    "Use bullet points. Focus on risks and actions for future phases. "
    "Keep it tight — reviewers need to scan it quickly. Return markdown."
)

_BRIEF_FORMAT_PROMPT = (
    "Write a 3–5 key lessons summary suitable for an executive summary. "
    "One short paragraph per lesson. Plain, direct language. Return markdown."
)

_FORMAT_PROMPTS = {
    "pir": _PIR_FORMAT_PROMPT,
    "gate_review": _GATE_FORMAT_PROMPT,
    "brief": _BRIEF_FORMAT_PROMPT,
}


def _get_store(arguments: dict[str, Any]) -> AssuranceStore:
    db_path_str = arguments.get("db_path")
    if db_path_str:
        return AssuranceStore(db_path=Path(db_path_str))
    return AssuranceStore()


def _call_claude(system: str, user: str, max_tokens: int, api_key: str) -> str:
    """Call the Anthropic Claude API synchronously and return the response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

LESSONS_TOOLS: list[Tool] = [
    Tool(
        name="extract_lessons",
        description=(
            "Extract structured lessons learned from a gate review report or PIR using AI. "
            "Parses the supplied text, identifies concrete lessons, and stores them in the "
            "lessons corpus for the specified project. Each lesson is classified by category "
            "(GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE), severity (HIGH/MEDIUM/LOW), "
            "lifecycle phase, root cause, and actionable recommendation. "
            "Returns the extracted lessons and a count. "
            "document_type: GATE_REVIEW, PIR, LESSONS_WORKSHOP, OTHER. "
            "gate: GATE_0–GATE_5, PAR (optional — annotates lessons with the gate stage). "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Unique project identifier (e.g. PROJ-001).",
                },
                "text": {
                    "type": "string",
                    "description": "Full text of the gate review report or PIR to extract lessons from.",
                },
                "document_type": {
                    "type": "string",
                    "enum": ["GATE_REVIEW", "PIR", "LESSONS_WORKSHOP", "OTHER"],
                    "description": "Type of source document.",
                },
                "gate": {
                    "type": "string",
                    "enum": ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "PAR"],
                    "description": "Optional IPA gate stage. Annotates all extracted lessons with this gate.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store. Defaults to ~/.pm_data_tools/store.db",
                },
            },
            "required": ["project_id", "text", "document_type"],
        },
    ),
    Tool(
        name="get_project_lessons",
        description=(
            "Retrieve all stored lessons for a project from the lessons corpus. "
            "Optionally filter by category (GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE) "
            "and/or gate stage. Returns lessons with their severity, root cause, recommendation, "
            "and source document metadata."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier to retrieve lessons for.",
                },
                "category": {
                    "type": "string",
                    "enum": ["GOVERNANCE", "DELIVERY", "COMMERCIAL", "TECHNICAL", "PEOPLE"],
                    "description": "Optional category filter.",
                },
                "gate": {
                    "type": "string",
                    "description": "Optional gate stage filter (e.g. GATE_2, PAR).",
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
        name="search_project_lessons",
        description=(
            "Search across ALL lessons in the structured lessons store — not just one project. "
            "Useful for portfolio managers querying institutional memory: "
            "'What do we know about supplier dependency failures at Gate 3?' "
            "Uses keyword matching on title, root_cause, and recommendation fields. "
            "Returns matching lessons with their project_id so you know which "
            "project each lesson came from. "
            "Optionally filter by category and/or minimum severity. "
            "Note: this searches the pm-lessons structured store (gate review / PIR extractions). "
            "To search the OPAL-7 lessons_learned corpus, use search_lessons from pm-assure."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword search query.",
                },
                "category": {
                    "type": "string",
                    "enum": ["GOVERNANCE", "DELIVERY", "COMMERCIAL", "TECHNICAL", "PEOPLE"],
                    "description": "Optional category filter applied after search.",
                },
                "min_severity": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"],
                    "description": "Optional minimum severity filter. HIGH returns only HIGH; MEDIUM returns MEDIUM and HIGH; LOW returns all.",
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
        name="get_systemic_patterns",
        description=(
            "Load all lessons from the store and use AI to identify patterns that recur "
            "across multiple projects — surfacing systemic issues in the portfolio rather "
            "than one-off project problems. Returns ranked patterns with the projects and "
            "lesson evidence that support each finding. "
            "Use this for portfolio-level retrospectives and continuous improvement planning. "
            "Requires at least 5 lessons in the store. "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "min_occurrences": {
                    "type": "integer",
                    "description": "Minimum number of lessons a pattern must appear in to be reported (default 2).",
                    "default": 2,
                },
                "category": {
                    "type": "string",
                    "enum": ["GOVERNANCE", "DELIVERY", "COMMERCIAL", "TECHNICAL", "PEOPLE"],
                    "description": "Optional category filter — analyse only lessons in this category.",
                },
                "db_path": {
                    "type": "string",
                    "description": "Optional path to the SQLite store.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="generate_lessons_section",
        description=(
            "Retrieve stored lessons for a project and use AI to write a formatted "
            "lessons learned section suitable for inclusion in a PIR, gate review report, "
            "or executive brief. Returns markdown. "
            "format options:\n"
            "  pir         — narrative grouped by category, root causes summarised, "
            "recommendations prioritised\n"
            "  gate_review — concise bullets focused on risks to future phases\n"
            "  brief       — 3–5 key lessons for an executive summary\n"
            "If no lessons are stored for the project, returns a template with guidance. "
            "Requires ANTHROPIC_API_KEY environment variable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
                "max_lessons": {
                    "type": "integer",
                    "description": "Maximum number of lessons to include (default 10).",
                    "default": 10,
                },
                "format": {
                    "type": "string",
                    "enum": ["pir", "gate_review", "brief"],
                    "description": "Output format. Default: pir.",
                    "default": "pir",
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


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _extract_lessons(arguments: dict[str, Any]) -> list[TextContent]:
    """Extract structured lessons from document text using Claude."""
    project_id = arguments["project_id"]
    text = arguments["text"]
    document_type = arguments["document_type"]
    gate = arguments.get("gate")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "ANTHROPIC_API_KEY environment variable not set.",
                        "project_id": project_id,
                        "document_type": document_type,
                    }
                ),
            )
        ]

    user_prompt = (
        f"Document type: {document_type}\n"
        + (f"Gate stage: {gate}\n" if gate else "")
        + f"\n---\n{text}\n---\n\n"
        "Extract all lessons learned from the above document as a JSON array."
    )

    try:
        raw = _call_claude(_EXTRACT_SYSTEM_PROMPT, user_prompt, 4096, api_key)
    except Exception as exc:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Anthropic API call failed: {exc}",
                        "project_id": project_id,
                    }
                ),
            )
        ]

    # Parse Claude's JSON response.
    try:
        lessons_raw: list[dict] = json.loads(raw)
        if not isinstance(lessons_raw, list):
            lessons_raw = []
    except json.JSONDecodeError:
        # Attempt to extract JSON array from surrounding text.
        import re
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                lessons_raw = json.loads(match.group())
            except json.JSONDecodeError:
                lessons_raw = []
        else:
            lessons_raw = []

    store = _get_store(arguments)
    stored_lessons: list[dict] = []
    for n, lesson in enumerate(lessons_raw, start=1):
        lesson_id = f"{project_id}-L{n:03d}"
        record = {
            "id": lesson_id,
            "project_id": project_id,
            "document_type": document_type,
            "gate": gate,
            "phase": lesson.get("phase"),
            "category": lesson.get("category", "DELIVERY"),
            "title": lesson.get("title", ""),
            "root_cause": lesson.get("root_cause"),
            "recommendation": lesson.get("recommendation", ""),
            "severity": lesson.get("severity", "MEDIUM"),
            "source_excerpt": lesson.get("source_excerpt"),
        }
        store.upsert_project_lesson(record)
        stored_lessons.append(record)

    result = {
        "project_id": project_id,
        "document_type": document_type,
        "gate": gate,
        "lessons_extracted": len(stored_lessons),
        "lessons": stored_lessons,
        "model": "claude-3-5-haiku-20241022",
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _get_project_lessons(arguments: dict[str, Any]) -> list[TextContent]:
    """Retrieve stored lessons for a project."""
    project_id = arguments["project_id"]
    category = arguments.get("category")
    gate = arguments.get("gate")

    store = _get_store(arguments)
    lessons = store.get_project_lessons(project_id, category=category, gate=gate)

    result = {
        "project_id": project_id,
        "filters": {"category": category, "gate": gate},
        "count": len(lessons),
        "lessons": lessons,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


async def _search_lessons(arguments: dict[str, Any]) -> list[TextContent]:
    """Keyword search across all lessons in the store."""
    query = arguments["query"]
    category = arguments.get("category")
    min_severity = arguments.get("min_severity")

    store = _get_store(arguments)
    matches = store.search_lessons(query)

    # Apply Python-side filters.
    if category:
        matches = [m for m in matches if m.get("category") == category]

    if min_severity:
        threshold = _SEVERITY_ORDER.get(min_severity, 0)
        matches = [m for m in matches if _SEVERITY_ORDER.get(m.get("severity", "LOW"), 0) >= threshold]

    result = {
        "query": query,
        "filters": {"category": category, "min_severity": min_severity},
        "count": len(matches),
        "lessons": matches,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


async def _get_systemic_patterns(arguments: dict[str, Any]) -> list[TextContent]:
    """Use AI to identify recurring patterns across all project lessons."""
    min_occurrences = arguments.get("min_occurrences", 2)
    category = arguments.get("category")

    store = _get_store(arguments)
    all_lessons = store.get_all_lessons(category=category)

    if len(all_lessons) < 5:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "insufficient_data",
                        "message": (
                            f"Only {len(all_lessons)} lesson(s) exist in the store. "
                            "At least 5 are required to identify systemic patterns. "
                            "Use extract_lessons to populate the store from gate review "
                            "reports and PIRs before running this analysis."
                        ),
                        "total_lessons": len(all_lessons),
                    }
                ),
            )
        ]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "ANTHROPIC_API_KEY environment variable not set.",
                        "total_lessons_available": len(all_lessons),
                    }
                ),
            )
        ]

    # Build a compact representation for the prompt.
    lessons_summary = [
        {
            "id": l["id"],
            "project_id": l["project_id"],
            "category": l["category"],
            "title": l["title"],
            "root_cause": l.get("root_cause", ""),
            "recommendation": l["recommendation"],
            "severity": l["severity"],
        }
        for l in all_lessons
    ]

    user_prompt = (
        f"Analyse the following {len(all_lessons)} lessons from UK government projects "
        f"and identify systemic patterns that occur across multiple projects. "
        f"Return only patterns with at least {min_occurrences} occurrences.\n\n"
        + json.dumps(lessons_summary, indent=2)
    )

    try:
        raw = _call_claude(_PATTERNS_SYSTEM_PROMPT, user_prompt, 4096, api_key)
    except Exception as exc:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": f"Anthropic API call failed: {exc}"}),
            )
        ]

    try:
        patterns: list[dict] = json.loads(raw)
        if not isinstance(patterns, list):
            patterns = []
    except json.JSONDecodeError:
        import re
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                patterns = json.loads(match.group())
            except json.JSONDecodeError:
                patterns = []
        else:
            patterns = []

    # Filter by min_occurrences (Claude should do this, but enforce here too).
    patterns = [p for p in patterns if p.get("occurrences", 0) >= min_occurrences]
    patterns.sort(key=lambda p: p.get("occurrences", 0), reverse=True)

    result = {
        "total_lessons_analysed": len(all_lessons),
        "filters": {"category": category, "min_occurrences": min_occurrences},
        "patterns_found": len(patterns),
        "patterns": patterns,
        "model": "claude-3-5-haiku-20241022",
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _generate_lessons_section(arguments: dict[str, Any]) -> list[TextContent]:
    """Use AI to write a formatted lessons learned section."""
    project_id = arguments["project_id"]
    max_lessons = arguments.get("max_lessons", 10)
    fmt = arguments.get("format", "pir")

    store = _get_store(arguments)
    lessons = store.get_project_lessons(project_id)

    if not lessons:
        template = (
            f"# Lessons Learned — {project_id}\n\n"
            "_No lessons have been recorded for this project yet._\n\n"
            "## How to populate this section\n\n"
            "Use the `extract_lessons` tool to extract structured lessons from:\n"
            "- Gate review reports\n"
            "- Post-Implementation Reviews (PIRs)\n"
            "- Lessons workshops\n\n"
            "Once lessons are stored, re-run `generate_lessons_section` to produce "
            "a formatted section ready for inclusion in your report.\n"
        )
        template = _attach_groundedness_to_lessons_section(template, lessons)
        return _apply_lessons_section_guardrail(template)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Return a structured fallback without AI narrative.
        fallback_lines = [f"# Lessons Learned — {project_id}\n"]
        for lesson in lessons[:max_lessons]:
            fallback_lines.append(
                f"## {lesson.get('title', 'Untitled')}\n"
                f"**Category:** {lesson.get('category')}  "
                f"**Severity:** {lesson.get('severity')}\n\n"
                f"**Root cause:** {lesson.get('root_cause', 'Not recorded')}\n\n"
                f"**Recommendation:** {lesson.get('recommendation')}\n"
            )
        fallback_document = "\n".join(fallback_lines)
        fallback_document = _attach_groundedness_to_lessons_section(
            fallback_document, lessons
        )
        return _apply_lessons_section_guardrail(fallback_document)

    # Trim to max_lessons — prioritise by severity.
    severity_key = lambda l: _SEVERITY_ORDER.get(l.get("severity", "LOW"), 0)
    lessons_sorted = sorted(lessons, key=severity_key, reverse=True)
    lessons_for_prompt = lessons_sorted[:max_lessons]

    format_instruction = _FORMAT_PROMPTS.get(fmt, _PIR_FORMAT_PROMPT)

    user_prompt = (
        f"Project: {project_id}\n\n"
        f"Format instruction: {format_instruction}\n\n"
        "Lessons to write up:\n"
        + json.dumps(lessons_for_prompt, indent=2, default=str)
    )

    system = (
        "You are a UK government project delivery assurance expert. "
        "Write a professional lessons learned section for inclusion in a formal report. "
        "Use plain, direct language. Avoid jargon. Return only markdown."
    )

    try:
        narrative = _call_claude(system, user_prompt, 2048, api_key)
    except Exception as exc:
        return [
            TextContent(
                type="text",
                text=f"Error: Anthropic API call failed: {exc}",
            )
        ]

    narrative = _attach_groundedness_to_lessons_section(narrative, lessons)
    return _apply_lessons_section_guardrail(narrative)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return LESSONS_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    handlers = {
        "extract_lessons": _extract_lessons,
        "get_project_lessons": _get_project_lessons,
        "search_project_lessons": _search_lessons,
        "get_systemic_patterns": _get_systemic_patterns,
        "generate_lessons_section": _generate_lessons_section,
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
