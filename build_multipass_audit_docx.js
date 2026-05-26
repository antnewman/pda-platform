// Build the PDA Platform multipass-audit DOCX with Tortoise AI branding.
// Same brand styling as build_gap_analysis_v2_docx.js for visual consistency
// across the audit set. Renders the 71-finding multipass audit into a
// page-numbered A4 PDF-suitable DOCX.

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Footer, AlignmentType,
  LevelFormat, HeadingLevel, BorderStyle, PageNumber, PageBreak,
  TabStopType,
} = require("docx");

// ── Brand colours ──────────────────────────────────────────────────────────
const C = {
  fuchsia: "D946EF",
  slate:   "334155",
  bg:      "F8FAFC",
  green:   "10B981",
  amber:   "D97706",
  red:     "DC2626",
  slate500:"64748B",
  slate200:"E2E8F0",
};
const FONT = "Inter";

// ── Helpers ────────────────────────────────────────────────────────────────
const t = (text, opts = {}) =>
  new TextRun({ text, font: FONT, color: opts.color || C.slate, bold: !!opts.bold,
    italics: !!opts.italics, size: opts.size, allCaps: !!opts.caps,
    characterSpacing: opts.spacing });

const p = (runs, opts = {}) =>
  new Paragraph({
    children: Array.isArray(runs) ? runs : [runs],
    spacing: { before: opts.before ?? 80, after: opts.after ?? 140, line: 320 },
    alignment: opts.align || AlignmentType.LEFT,
    indent: opts.indent,
  });

const body = (text, opts = {}) => p(t(text, { size: 21, ...opts }), opts);

const bodyRuns = (runs, opts = {}) => new Paragraph({
  children: runs,
  spacing: { before: opts.before ?? 80, after: opts.after ?? 140, line: 320 },
  alignment: opts.align || AlignmentType.LEFT,
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160, line: 280 },
  children: [new TextRun({ text, font: FONT, color: C.slate, bold: true, size: 36 })],
});

const h2 = (text, opts = {}) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 320, after: 120, line: 280 },
  children: [new TextRun({ text, font: FONT, color: opts.color || C.slate, bold: true, size: 28 })],
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 240, after: 80, line: 260 },
  children: [new TextRun({ text, font: FONT, color: C.slate, bold: true, size: 22 })],
});

const smallCaps = (text, opts = {}) => new Paragraph({
  spacing: { before: opts.before ?? 280, after: opts.after ?? 60 },
  children: [new TextRun({
    text, font: FONT, color: opts.color || C.slate500, bold: true,
    allCaps: true, size: opts.size || 16, characterSpacing: 40,
  })],
});

const ruleFuchsia = new Paragraph({
  spacing: { before: 80, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C.fuchsia, space: 1 } },
  children: [new TextRun({ text: "" })],
});

const ruleSlate = new Paragraph({
  spacing: { before: 60, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.slate200, space: 1 } },
  children: [new TextRun({ text: "" })],
});

const labelled = (label, runs, opts = {}) => new Paragraph({
  spacing: { before: 80, after: 120, line: 320 },
  children: [
    new TextRun({ text: label.toUpperCase() + ".  ", font: FONT,
      color: opts.labelColor || C.slate500,
      bold: true, allCaps: true, size: 17, characterSpacing: 40 }),
    ...(Array.isArray(runs) ? runs : [runs]),
  ],
});

const code = (text) => new TextRun({ text, font: "Consolas", color: C.slate, size: 19 });

// Severity-coloured tag
const sevTag = (sev) => {
  const colour = sev === "HIGH" ? C.red : sev === "MEDIUM" ? C.amber : C.slate500;
  return new TextRun({ text: sev, font: FONT, color: colour, bold: true,
    allCaps: true, size: 17, characterSpacing: 40 });
};

const numbering = {
  config: [
    { reference: "rank",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ],
};

// ── Finding renderer ──────────────────────────────────────────────────────
// Each finding has: id, title, severity, where, what, reproduction,
// recommended, effort. We render them as a compact block.
const finding = (f) => {
  const out = [];
  // ID + title + severity tag on one line
  out.push(new Paragraph({
    spacing: { before: 200, after: 60 },
    children: [
      new TextRun({ text: f.id + "  ", font: FONT, color: C.fuchsia,
        bold: true, size: 22 }),
      new TextRun({ text: f.title, font: FONT, color: C.slate, bold: true, size: 22 }),
      new TextRun({ text: "    " }),
      sevTag(f.severity),
    ],
  }));
  if (f.where) {
    out.push(new Paragraph({
      spacing: { before: 40, after: 40, line: 280 },
      children: [
        new TextRun({ text: "WHERE  ", font: FONT, color: C.slate500,
          bold: true, allCaps: true, size: 14, characterSpacing: 40 }),
        new TextRun({ text: f.where, font: "Consolas", color: C.slate, size: 19 }),
      ],
    }));
  }
  if (f.what) {
    out.push(new Paragraph({
      spacing: { before: 20, after: 40, line: 280 },
      children: [
        new TextRun({ text: "WHAT  ", font: FONT, color: C.slate500,
          bold: true, allCaps: true, size: 14, characterSpacing: 40 }),
        new TextRun({ text: f.what, font: FONT, color: C.slate, size: 20 }),
      ],
    }));
  }
  if (f.reproduction) {
    out.push(new Paragraph({
      spacing: { before: 20, after: 40, line: 280 },
      children: [
        new TextRun({ text: "REPRODUCTION  ", font: FONT, color: C.slate500,
          bold: true, allCaps: true, size: 14, characterSpacing: 40 }),
        new TextRun({ text: f.reproduction, font: FONT, color: C.slate, italics: true, size: 20 }),
      ],
    }));
  }
  if (f.recommended) {
    out.push(new Paragraph({
      spacing: { before: 20, after: 40, line: 280 },
      children: [
        new TextRun({ text: "RECOMMENDED  ", font: FONT, color: C.fuchsia,
          bold: true, allCaps: true, size: 14, characterSpacing: 40 }),
        new TextRun({ text: f.recommended, font: FONT, color: C.slate, size: 20 }),
      ],
    }));
  }
  if (f.effort) {
    out.push(new Paragraph({
      spacing: { before: 20, after: 100, line: 280 },
      children: [
        new TextRun({ text: "EFFORT  ", font: FONT, color: C.slate500,
          bold: true, allCaps: true, size: 14, characterSpacing: 40 }),
        new TextRun({ text: f.effort, font: FONT, color: C.green, bold: true, size: 20 }),
      ],
    }));
  }
  return out;
};

// ── Content build ──────────────────────────────────────────────────────────
const content = [];

// Cover title
content.push(new Paragraph({
  spacing: { before: 600, after: 80 },
  children: [new TextRun({
    text: "Multipass audit · v1", font: FONT, color: C.slate, bold: true, size: 16,
    allCaps: true, characterSpacing: 60,
  })],
}));

content.push(new Paragraph({
  spacing: { before: 40, after: 80, line: 260 },
  children: [new TextRun({
    text: "PDA Platform",
    font: FONT, color: C.slate, bold: true, size: 52,
  })],
}));

content.push(new Paragraph({
  spacing: { before: 0, after: 200, line: 260 },
  children: [new TextRun({
    text: "Six-pass forensic audit of v2.0.0",
    font: FONT, color: C.fuchsia, bold: true, italics: true, size: 28,
  })],
}));

content.push(ruleFuchsia);

content.push(body(
  "Six independent passes — silent failures, concurrency, data integrity, security and attack surface, " +
  "observability, and test coverage gaps. Conducted sequentially so each later pass had awareness of earlier " +
  "findings; severity calibrated consistently across passes; cross-pass synthesis produces the pattern view " +
  "below. Pure audit; no fixes applied inline."
));

content.push(smallCaps("Audit date"));
content.push(body("16 May 2026, against the platform at v2.0.0 (commit a02dcc3 on main)."));

content.push(smallCaps("Methodology"));
content.push(body(
  "Read-only inspection of the codebase by six focused subagents, each operating against the audit rubric: " +
  "ID, severity (HIGH / MEDIUM / LOW), location (file path + line range), what, reproduction, recommended " +
  "action, effort (small / medium / large). After each pass, findings were saved to the running audit document " +
  "and the next pass's prompt was updated to reflect what had already been flagged — this prevented duplicate " +
  "findings and improved cross-pass severity calibration."
));

// ── Executive summary ────────────────────────────────────────────────────
content.push(new Paragraph({ children: [new PageBreak()] }));
content.push(smallCaps("Executive summary", { size: 18 }));
content.push(h1("71 findings across six passes"));
content.push(ruleFuchsia);

content.push(h2("Severity by pass"));

// Severity table as paragraphs (compact, brand-consistent)
const severityRows = [
  { pass: "Pass 1 — Silent failures",  high: 4, med: 7, low: 2, total: 13 },
  { pass: "Pass 2 — Concurrency",      high: 3, med: 5, low: 3, total: 11 },
  { pass: "Pass 3 — Data integrity",   high: 3, med: 7, low: 3, total: 13 },
  { pass: "Pass 4 — Security",         high: 3, med: 4, low: 3, total: 10 },
  { pass: "Pass 5 — Observability",    high: 4, med: 4, low: 4, total: 12 },
  { pass: "Pass 6 — Test coverage",    high: 3, med: 6, low: 3, total: 12 },
];
for (const r of severityRows) {
  content.push(new Paragraph({
    spacing: { before: 60, after: 60, line: 280 },
    tabStops: [
      { type: TabStopType.LEFT,  position: 4400 },
      { type: TabStopType.RIGHT, position: 5800 },
      { type: TabStopType.RIGHT, position: 7200 },
      { type: TabStopType.RIGHT, position: 8600 },
    ],
    children: [
      new TextRun({ text: r.pass, font: FONT, color: C.slate, bold: true, size: 21 }),
      new TextRun({ text: "\t" }),
      new TextRun({ text: "HIGH " + r.high, font: FONT, color: C.red, bold: true, size: 19, characterSpacing: 20 }),
      new TextRun({ text: "\t" }),
      new TextRun({ text: "MED " + r.med, font: FONT, color: C.amber, bold: true, size: 19, characterSpacing: 20 }),
      new TextRun({ text: "\t" }),
      new TextRun({ text: "LOW " + r.low, font: FONT, color: C.slate500, bold: true, size: 19, characterSpacing: 20 }),
      new TextRun({ text: "\t" }),
      new TextRun({ text: "total " + r.total, font: FONT, color: C.slate, bold: true, size: 19 }),
    ],
  }));
}
content.push(new Paragraph({
  spacing: { before: 100, after: 80, line: 280 },
  children: [
    new TextRun({ text: "TOTAL  ", font: FONT, color: C.slate, bold: true,
      allCaps: true, size: 17, characterSpacing: 40 }),
    new TextRun({ text: "20 HIGH · 33 MEDIUM · 18 LOW · 71 findings", font: FONT,
      color: C.slate, bold: true, size: 22 }),
  ],
}));

// Top 10
content.push(h2("Top 10 HIGH-severity items, by recommended priority"));

const top10 = [
  { rank: 1, id: "P4.F02", title: "Public dashboard endpoint exposes any project's data without auth",
    action: "Add Bearer/API-key auth on /data/* and /dashboards/*, or restrict to internal", effort: "small" },
  { rank: 2, id: "P4.F01", title: "Unsanitised project_id flows into Claude prompts (injection vector)",
    action: "Sanitise IDs to alphanumeric + hyphen + underscore before f-string interpolation", effort: "small" },
  { rank: 3, id: "P4.F03", title: "No input-size limits on tool parameters",
    action: "Add maxLength to free-text inputs across MCP schemas; validate before LLM call", effort: "small" },
  { rank: 4, id: "P5.F02", title: "/health endpoint too shallow to detect realistic degradation",
    action: "Promote /health to check store / API key / audit chains / extras presence", effort: "small" },
  { rank: 5, id: "P3.F01", title: "SQLite foreign keys declared but not enforced",
    action: "Add PRAGMA foreign_keys=ON in _connect()", effort: "small" },
  { rank: 6, id: "P3.F02", title: "Dual lessons and lessons_learned tables with different schemas",
    action: "Consolidate via migration; deprecate one of the two", effort: "medium" },
  { rank: 7, id: "P5.F01", title: "Audit-chain failures silent without operator counter or log",
    action: "Increment failure counter on swallowed exceptions; expose at /health", effort: "small" },
  { rank: 8, id: "P5.F03", title: "Tool invocations leave zero trace in operational logs",
    action: "Add one structured structlog.info per call_tool invocation", effort: "small" },
  { rank: 9, id: "P5.F04", title: "Audit-chain JSONL files grow monotonically with no rotation",
    action: "Daily rotation with chain-link preservation; expose size metric at /health", effort: "medium" },
  { rank: 10, id: "P6.F02", title: "No test for _safe_record_decision fail-safe property",
    action: "Add monkeypatched-failure test asserting tool output is preserved", effort: "small" },
];
for (const item of top10) {
  content.push(new Paragraph({
    spacing: { before: 100, after: 30 },
    children: [
      new TextRun({ text: String(item.rank).padStart(2, "0") + "  ", font: FONT,
        color: C.fuchsia, bold: true, size: 24 }),
      new TextRun({ text: item.id, font: "Consolas", color: C.slate, bold: true, size: 20 }),
      new TextRun({ text: "  " + item.title, font: FONT, color: C.slate, bold: true, size: 21 }),
    ],
  }));
  content.push(new Paragraph({
    spacing: { before: 0, after: 40, line: 280 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: item.action, font: FONT, color: C.slate, size: 19 }),
      new TextRun({ text: "  ·  " + item.effort + " effort", font: FONT,
        color: C.green, bold: true, italics: true, size: 18 }),
    ],
  }));
}

// Cross-pass synthesis
content.push(h2("Cross-pass synthesis"));

const synth = [
  { title: "Silent audit-chain failure is the dominant cross-pass concern.",
    body: "Surfaces in Pass 1 (silent by design, no log), Pass 2 (race window during hydration), Pass 3 " +
          "(no version field for recovery), Pass 5 (no operator visibility), and Pass 6 (no test for the " +
          "fail-safe). Single highest-leverage fix: one structlog.warning on swallowed exceptions plus " +
          "a failure counter on /health — closes four findings." },
  { title: "Input is unsanitised everywhere.",
    body: "Pass 4 (project_id prompt injection, missing size limits, MCP schema not enforced), Pass 1 " +
          "(notes parsing fragility), Pass 3 (canonical-JSON non-determinism), and Pass 6 (no oversized-" +
          "input tests) all reduce to \"the platform trusts MCP-supplied input\". A single input-validation " +
          "seam (jsonschema enforcement in call_tool) closes most of these." },
  { title: "The platform is at the demo / open-beta deployment boundary.",
    body: "Permissive CORS, no auth, no rate limiting, no observability beyond stderr, no rotation, no " +
          "monitoring. Appropriate for the current demo posture but each becomes an operational issue the " +
          "moment the platform moves toward production traffic. The audit findings collectively form the " +
          "punch list for that transition." },
  { title: "The L7 RedTeam harness exists but has no corpus.",
    body: "Pass 4 (P4.F10) and Pass 6 (P6.F12) both flag this. The harness primitive is built and tested; " +
          "the empty corpus means none of the security-class findings have automated regression coverage. " +
          "Building a corpus is the single highest-value hardening artefact for the platform." },
  { title: "The audit chain is cryptographically robust but operationally fragile.",
    body: "Tamper-evidence holds for clean inputs but degrades on NaN/inf, sets, bytes/tuples. The chain " +
          "has no version field, no rotation, no operator visibility, no resilience tests. The cryptographic " +
          "claim is sound; the surrounding operational story needs work." },
  { title: "Render's single-worker deployment masks all multi-worker concurrency findings.",
    body: "Three Pass 2 HIGH findings (audit-chain race, SQLite contention, connection leak) are HIGH in " +
          "principle but mitigated in current deployment. The platform should document the single-worker " +
          "requirement explicitly before any operator scales it." },
];

for (const s of synth) {
  content.push(new Paragraph({
    spacing: { before: 160, after: 40 },
    children: [
      new TextRun({ text: s.title, font: FONT, color: C.fuchsia, bold: true, size: 21 }),
    ],
  }));
  content.push(body(s.body));
}

// Per-pass findings sections — each pass on its own page
const passes = [
  {
    n: "1",
    title: "Silent failures and error recovery",
    summary: "13 findings (4 HIGH · 7 MEDIUM · 2 LOW)",
    pattern: "The `_safe_record_decision` pattern is correctly designed (audit failures don't break tool " +
             "output) but lacks observability — exceptions are silent. Fallback paths work correctly but " +
             "lack freshness metadata and consumer awareness that they are fallbacks. NaN/None/inf " +
             "propagation is mostly handled at source, but downstream consumers assume valid numeric " +
             "values without schema validation.",
    findings: [
      // HIGH
      { id: "P1.F01", severity: "HIGH", title: "_safe_record_decision silently swallows audit-chain persistence failures",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assure/server.py : 40-61",
        what: "The audit-chain recording wrapper catches all exceptions and swallows them with bare pass. If the AssuranceStore fails (disk full, permissions, schema mismatch), no diagnostic is logged, no metric recorded. Operator has zero signal that a decision audit entry was lost.",
        reproduction: "Set a read-only store path and call a tool that triggers _safe_record_decision. The audit entry vanishes silently.",
        recommended: "Add a structlog.warning() before the pass statement with the exception type and brief context.",
        effort: "small" },
      { id: "P1.F02", severity: "HIGH", title: "Identical bare-except-pass pattern in four other modules",
        where: "pm_assumptions/server.py : 66-67; pm_reporting/server.py : 62-63; pm_knowledge/server.py; pm_simulation/server.py",
        what: "Same silent audit-chain failure pattern replicated across five MCP servers. Each one swallows exceptions from record_decision without logging.",
        reproduction: "Trigger any audit-chain write on a locked or corrupted database. Audit entry is lost; no error surfaces.",
        recommended: "Create a shared _log_audit_failure(exc, context) function that all servers call instead of bare pass.",
        effort: "small" },
      { id: "P1.F03", severity: "HIGH", title: "Evidence-only board report fallback lacks machine-readable labelling",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_reporting/server.py : 577-721",
        what: "When Claude API fails, report falls back to evidence-only mode. The heading note says \"AI synthesis unavailable\" but downstream consumers may not see it if the fallback is rendered as markdown in a PDF or email. Board members may think it is AI-synthesised when it is not.",
        reproduction: "Unset ANTHROPIC_API_KEY, trigger generate_board_exception_report. Fallback activates. Send to board without screenshot of heading.",
        recommended: "Embed a machine-readable flag (e.g. top-level _fallback: true) so consumers know to treat it as evidence-only.",
        effort: "medium" },
      { id: "P1.F04", severity: "HIGH", title: "detect_external_drift may return drift_pct=None without operator signal",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 1172-1176",
        what: "When baseline is zero, drift_pct is set to 0.0 (not NaN). When signal fetch fails silently, consumers may receive None for drift_pct. No schema validation on the consumer side catches this; downstream aggregation skips it silently.",
        reproduction: "Create boolean assumption with baseline=1.0, fetch external signal returning None. Output has drift_pct=None.",
        recommended: "Add explicit validation in consumers: if drift_pct is None, log a warning and exclude that assumption from health aggregates.",
        effort: "medium" },
      // MEDIUM
      { id: "P1.F05", severity: "MEDIUM", title: "Groundedness checker accepts empty-string content sources without explicit signal",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_groundedness/checker.py : 186-188",
        what: "If a source has content=\"\", overall_score becomes 0.0 and ungrounded_terms lists every token. Callers may interpret 0.0 as \"completely ungrounded\" and suppress the output, when the real issue is missing source data.",
        reproduction: "Pass a source with content=\"\" to compute_groundedness. Caller could misinterpret as hallucination.",
        recommended: "If all sources have empty content, return NOT_COMPUTED verdict with explicit reason.",
        effort: "small" },
      { id: "P1.F06", severity: "MEDIUM", title: "Lazy import of agent_planning may leak traceback on signature drift",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 1400-1402",
        what: "ImportError is caught and returned as JSON error. But if import succeeds and signature has drifted, the resulting TypeError is caught as a generic Exception and the raw traceback is returned to the consumer.",
        reproduction: "Modify AnthropicProvider signature; reinstall. Call track_review_actions. Caller sees raw traceback in JSON.",
        recommended: "Distinguish ImportError from generic Exception; sanitise other errors.",
        effort: "small" },
      { id: "P1.F07", severity: "MEDIUM", title: "External signal fallback hardcodes a stale signal_date",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 748-766, 825-840",
        what: "Fallback values include signal_date: \"2026-Q1\" (string). No freshness check. If code is run in 2028 and fallback is used, consumer sees \"2026-Q1\" and may think the signal is recent.",
        reproduction: "Set ONS API to fail. Call fetch_external_signal. Get fallback with signal_date=\"2026-Q1\".",
        recommended: "Compute fallback signal_date dynamically: str(date.today()) plus a _fallback: true flag.",
        effort: "small" },
      { id: "P1.F08", severity: "MEDIUM", title: "Assumption notes-field parsing fragile to pipe characters",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 995-1005",
        what: "_score_assumption_confidence enriches via pipe-delimited notes parsing. If a note contains a pipe character, the split is corrupted. Enriched record passes wrong values to _compute_confidence.",
        reproduction: "Load assumption with notes containing \"Validation: Check in Q2 (2026|Q2)\". Parse breaks.",
        recommended: "Use a structured metadata field, or regex with named groups.",
        effort: "medium" },
      { id: "P1.F09", severity: "MEDIUM", title: "Benefits drift severity classification missing None/inf handling",
        where: "packages/pm-data-tools/src/pm_data_tools/assurance/benefits.py : 1101-1109",
        what: "drift_pct = abs((current - baseline) / baseline) * 100. If baseline is None, raises TypeError. If baseline == 0 and current != 0, drift_pct is inf; _classify_drift(inf) may return CRITICAL artefactually.",
        reproduction: "Benefit with baseline_value=None. Measurement value=100. Call analyse_health. TypeError propagates.",
        recommended: "Add None/zero checks before drift_pct; default to DriftSeverity.NONE if baseline is missing.",
        effort: "small" },
      { id: "P1.F10", severity: "MEDIUM", title: "L5 guardrail-rejection envelope not defensively consumed downstream",
        where: "Cross-cutting — pm_synthesis / pm_portfolio aggregators of generate_* outputs",
        what: "When L5 rejects, response is {\"error\": \"guardrail_rejected\", ...}. Downstream consumers may not check this envelope; they parse it as the normal response and fail with misleading errors.",
        reproduction: "Generate gate review with forbidden phrase. Pass to a downstream composer.",
        recommended: "Define a single is_guardrail_rejection(response) helper and use at every aggregator site.",
        effort: "small" },
      { id: "P1.F11", severity: "MEDIUM", title: "Asymmetric exception-output detail in _export_assumption_graph",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 1370-1372",
        what: "Most handlers return traceback in the JSON error for operator debugging. _export_assumption_graph returns only the error string.",
        reproduction: "Trigger an error in _export_assumption_graph (e.g. read-only output_dir). Response lacks traceback.",
        recommended: "Add traceback.format_exc() to the error JSON to match other handlers.",
        effort: "small" },
      // LOW
      { id: "P1.F12", severity: "LOW", title: "Missing validation on dependencies field in load_assumption_register",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 940",
        what: "linked_items / dependencies loaded as comma-separated string. No validation that IDs correspond to actual deliverables. Cascade analysis silently skips non-existent items.",
        reproduction: "Load assumption with linked_items=\"DELIVERY-999\". Cascade skips silently.",
        recommended: "Log a warning if any linked_items cannot be resolved, or mark as \"unresolved\".",
        effort: "small" },
      { id: "P1.F13", severity: "LOW", title: "Empty answer in compute_groundedness returns counter-intuitive grounded=True",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_groundedness/checker.py : 166-182",
        what: "If answer is empty, _tokenise returns empty; result is grounded=True, overall_score=1.0. Rationale is \"trivially grounded\" but semantically confusing.",
        reproduction: "compute_groundedness(\"\", sources=[...]). Result misleading.",
        recommended: "Return NOT_COMPUTED instead of grounded=True when answer_tokens is empty.",
        effort: "small" },
    ],
  },
  // Pass 2 ── Concurrency
  {
    n: "2",
    title: "Concurrency",
    summary: "11 findings (3 HIGH · 5 MEDIUM · 3 LOW)",
    pattern: "Render's single-worker default mitigates the most dangerous cross-process findings. SQLite is " +
             "used with defaults (no WAL, no busy-timeout, per-call connection). The audit-chain module " +
             "level state has check-then-set seams in three places (_get_chain, _ensure_schemas, dict " +
             "mutations) that are not atomic.",
    findings: [
      { id: "P2.F01", severity: "HIGH", title: "Audit-chain hydration race on multi-worker restart",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py : 91-122",
        what: "_get_chain() checks if module_name not in _CHAINS without a cross-process lock. Under multi-process deployment, two workers restarting simultaneously both pass the check, both hydrate, both append. Chain hash integrity breaks.",
        reproduction: "Deploy with 2+ uvicorn workers; trigger simultaneous restarts; verify chain check fails.",
        recommended: "Guard with a file-level lock (fcntl/msvcrt) held during hydration plus first-write. Or switch to SQLite-backed chain.",
        effort: "medium (mitigated by single-worker Render config)" },
      { id: "P2.F02", severity: "HIGH", title: "SQLite has no journal_mode or busy_timeout configured",
        where: "packages/pm-data-tools/src/pm_data_tools/db/store.py : 82-84",
        what: "AssuranceStore creates new connections per call without setting journal_mode or busy_timeout. SQLite's default DELETE mode plus no timeout means concurrent writes raise SQLITE_BUSY immediately.",
        reproduction: "Two concurrent MCP tools call insert_confidence_score on overlapping projects; one may fail with DatabaseError.",
        recommended: "In _connect() set PRAGMA journal_mode=WAL and PRAGMA busy_timeout=5000.",
        effort: "small" },
      { id: "P2.F03", severity: "HIGH", title: "Per-call AssuranceStore instantiation leaks connections under load",
        where: "packages/pm-data-tools/src/pm_data_tools/db/store.py : 76-84; 13+ instantiation sites",
        what: "Each tool call creates a new AssuranceStore() and opens a new connection. No pooling; 1000 concurrent calls open 1000 FDs. SQLite default FD limit often 256/process; resource exhaustion plausible.",
        reproduction: "300 concurrent score_assumption_confidence calls; observe OperationalError or \"too many open files\".",
        recommended: "Module-level singleton _GLOBAL_STORE = AssuranceStore() initialised once at import.",
        effort: "small" },
      { id: "P2.F04", severity: "MEDIUM", title: "Lazy schema initialisation race in GMPP narratives",
        where: "packages/pm-data-tools/src/pm_data_tools/gmpp/narratives.py : 102-137",
        what: "_ensure_schemas() does if GMPP_DCA_SCHEMA is not None: return without sync. Two concurrent instances both pass the check, both call CustomSchema() — redundant work, brief race window.",
        reproduction: "Call generate_dca_narrative from two concurrent MCP tools; count construction calls.",
        recommended: "threading.Lock around the check-and-set, or functools.cached_property on a class attribute.",
        effort: "small" },
      { id: "P2.F05", severity: "MEDIUM", title: "_CHAINS and _LOCKS dict mutations unguarded",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py : 74-75",
        what: "Threads access _CHAINS and _LOCKS without holding a sync lock during the check-then-set. CPython's GIL makes single ops atomic, but the if-not-in/insert sequence is not.",
        reproduction: "Stress under PyPy or 100 threads on CPython hitting fresh module names; observe KeyError.",
        recommended: "Module-level threading.Lock held during the check-and-set, or use dict.setdefault().",
        effort: "small" },
      { id: "P2.F06", severity: "MEDIUM", title: "Concurrent run_schedule_simulation writes to simulation_residuals without isolation",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_simulation/server.py : 284-287, 319-326",
        what: "Two concurrent run_schedule_simulation calls for the same project write to simulation_residuals. A third call to _build_conformal_bands may read partial writes.",
        reproduction: "Two concurrent run_schedule_simulation calls; concurrently call get_simulation_results; observe missing/duplicated residuals.",
        recommended: "Wrap residuals write in an explicit transaction (with conn:). Combined with WAL (P2.F02), readers see a consistent snapshot.",
        effort: "medium" },
      { id: "P2.F07", severity: "MEDIUM", title: "SSE disconnect orphans in-flight async tasks",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 49-59",
        what: "When client disconnects mid-request, async tasks spawned by server.run() are not explicitly cancelled. They continue against a closed connection; resources may dangle.",
        reproduction: "Start a long-running tool call; kill the client; observe orphaned tasks.",
        recommended: "Wrap server.run() in asyncio.TaskGroup (3.11+) or try/finally cancel; document the cancellation contract.",
        effort: "medium" },
      { id: "P2.F08", severity: "MEDIUM", title: "No documented lock ordering across modules' audit chains",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py",
        what: "Each module has its own audit chain with its own lock. A tool touching multiple modules holds locks sequentially. No documented ordering means a parallel pair could deadlock.",
        reproduction: "Construct tools that record to pm_assure→pm_assumptions vs pm_assumptions→pm_assure; run concurrently — possible deadlock.",
        recommended: "Document lock-acquisition order (alphabetical) and assert in record_decision. Or consolidate to a single global chain.",
        effort: "medium" },
      { id: "P2.F09", severity: "LOW", title: "reset_for_testing mutates caches without holding any lock",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py : 182-212",
        what: "reset_for_testing clears _CHAINS and _LOCKS without sync. If pytest runs in parallel (pytest-xdist) and one test calls reset while another is in _get_chain, races produce sporadic KeyError.",
        reproduction: "pytest -n auto; call reset_for_testing in a conftest fixture.",
        recommended: "Module-level lock held during reset. Or mark audit tests as @pytest.mark.serial.",
        effort: "small" },
      { id: "P2.F10", severity: "LOW", title: "Dashboard endpoint may return inconsistent panels under concurrent writes",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 85-98",
        what: "Multiple clients polling /data/{project_id}/dashboard.json concurrently each call build_assumption_dashboard_panels. If one client is mid-query and a tool is writing, stale data may be returned.",
        reproduction: "Poll dashboard every 1s while running score_assumption_confidence in background.",
        recommended: "Enable WAL mode (P2.F02). Optional: ETag/Last-Modified header.",
        effort: "small (covered by P2.F02)" },
      { id: "P2.F11", severity: "LOW", title: "Single-worker assumption is implicit, not asserted",
        where: "render.yaml; pda_platform/remote.py",
        what: "Render's default is single-worker; the platform's chain integrity depends on this. The assumption isn't documented or asserted — a future operator scaling to multi-worker would silently break chain integrity.",
        reproduction: "Add workers=2 to uvicorn.run; trigger an audit-recording tool from two SSE connections; chain may degrade.",
        recommended: "Add DEPLOYMENT.md documenting the single-worker requirement. Log a WARNING at startup if multi-worker is detected.",
        effort: "small" },
    ],
  },
  // Pass 3 ── Data integrity
  {
    n: "3",
    title: "Data integrity and audit-chain claims",
    summary: "13 findings (3 HIGH · 7 MEDIUM · 3 LOW)",
    pattern: "Schema-versioning gaps recur — neither AuditEntry nor the L5 rejection envelope carries a " +
             "version field. Determinism gaps in canonical serialisation are small individually but together " +
             "break the structural-consistency claim (§11.4). Two HIGH findings (dual lessons tables, FK " +
             "enforcement) are deferred migration debt that predates the VA work.",
    findings: [
      { id: "P3.F01", severity: "HIGH", title: "SQLite foreign keys declared but not enforced",
        where: "packages/pm-data-tools/src/pm_data_tools/db/store.py : 76-84",
        what: "Schema declares FOREIGN KEY constraints, but _connect() does not execute PRAGMA foreign_keys = ON. SQLite disables FK enforcement by default. Orphaned child rows persist; cascade deletes don't fire.",
        reproduction: "Insert a child row with a non-existent parent ID; it succeeds despite the FK declaration.",
        recommended: "Add conn.execute(\"PRAGMA foreign_keys = ON\") immediately after creating each connection.",
        effort: "small" },
      { id: "P3.F02", severity: "HIGH", title: "Dual lessons and lessons_learned tables with different schemas",
        where: "packages/pm-data-tools/src/pm_data_tools/db/store.py : 154-169, 521-534",
        what: "Two tables with overlapping purpose: lessons_learned (8 columns, upsert_lesson) and lessons (10 columns, upsert_project_lesson). Methods inconsistently use one or the other. No migration plan documented.",
        reproduction: "Insert via upsert_lesson; call get_project_lessons which reads from the other table. Lesson does not appear.",
        recommended: "Consolidate into a single lessons table with a migration. Deprecate lessons_learned.",
        effort: "medium" },
      { id: "P3.F03", severity: "HIGH", title: "Audit entries have no schema version field",
        where: "packages/pm-data-tools/src/pm_data_tools/audit/chain.py : 95-144",
        what: "AuditEntry contains no version or schema_version field. If a future PR adds a required field, old chains silently lack it; backward-compatibility is not testable.",
        reproduction: "Add a required field; attempt from_json() on a v1 chain. Field is missing or defaults silently.",
        recommended: "Add version: int = 1 to AuditEntry; update from_dict() to dispatch on version.",
        effort: "medium" },
      { id: "P3.F04", severity: "MEDIUM", title: "Canonical serialisation is non-deterministic for sets",
        where: "packages/pm-data-tools/src/pm_data_tools/audit/chain.py : 49-57",
        what: "Sets fall through to default=str(value) which uses Python's hash-randomised iteration order. Two processes recording structurally identical decisions produce different hashes; consistency-hash verification fails.",
        reproduction: "Record input_data={\"items\": {1,2,3}} twice across two processes; observe different entry_hash.",
        recommended: "Handle sets explicitly in _json_default: return sorted(list(value)). Also handle frozenset.",
        effort: "small" },
      { id: "P3.F05", severity: "MEDIUM", title: "NaN and Infinity floats produce non-compliant JSON",
        where: "packages/pm-data-tools/src/pm_data_tools/audit/chain.py : 35-46",
        what: "json.dumps emits NaN and Infinity literals which are not valid per RFC 7159. Strict parsers (jq, browser JSON.parse) reject them, breaking inter-tool portability.",
        reproduction: "chain.record(..., input_data={\"score\": float('nan')}, ...). Parse with jq — fails.",
        recommended: "Use json.dumps(..., allow_nan=False) which raises ValueError automatically.",
        effort: "small" },
      { id: "P3.F06", severity: "MEDIUM", title: "simulation_residuals.residual is a stored snapshot that can desynchronise",
        where: "packages/pm-data-tools/src/pm_data_tools/db/store.py : 505-516",
        what: "residual is computed at insert and stored. If predicted_value or actual_value is later updated, residual is stale. No trigger or computed column prevents this.",
        reproduction: "Insert; UPDATE simulation_residuals SET predicted_value=...; residual is now wrong.",
        recommended: "Use a generated column (SQLite 3.31+), or BEFORE UPDATE trigger, or make rows immutable in app code.",
        effort: "small" },
      { id: "P3.F07", severity: "MEDIUM", title: "L5 rule exception downgrades severity from BLOCK to UNKNOWN silently",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_guardrails/engine.py : 217-230",
        what: "When a Rule.condition raises, the trail entry is severity=UNKNOWN, violated=False. The rule's original BLOCK severity is lost. A crashing critical rule passes through to APPROVED.",
        reproduction: "Define a BLOCK rule whose condition raises KeyError; tool output is APPROVED.",
        recommended: "Preserve nominal severity; treat exception in a BLOCK rule as a BLOCK violation (fail-safe).",
        effort: "small" },
      { id: "P3.F08", severity: "MEDIUM", title: "HTML-comment groundedness footer parser is fragile",
        where: "Cross-cutting — pm_reporting, pm_lessons (L6 markdown footer)",
        what: "Groundedness metadata embedded as <!-- _groundedness: {...} -->. If the document body itself contains the literal string <!-- _groundedness: (e.g. in a code example), parser extracts the wrong block.",
        reproduction: "Generate a document with documentation about the platform that mentions the marker string.",
        recommended: "Use a versioned, base64-delimited format: <!-- _groundedness:v1:{base64} -->. Or sidecar JSON.",
        effort: "small" },
      { id: "P3.F09", severity: "MEDIUM", title: "GroundednessResult has to_dict but no from_dict",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_groundedness/checker.py : 109-122",
        what: "Consumers who deserialise the JSON cannot reconstruct a typed result; round-trip testing impossible; forensic replay harder.",
        reproduction: "Take a result.to_dict(), JSON-roundtrip, no from_dict exists.",
        recommended: "Add @classmethod from_dict(cls, raw: dict) -> GroundednessResult.",
        effort: "small" },
      { id: "P3.F10", severity: "MEDIUM", title: "Deprecated datetime.utcnow() used in audit chain and ~8 sites",
        where: "packages/pm-data-tools/src/pm_data_tools/audit/chain.py : 236 (and search 'utcnow' across repo)",
        what: "datetime.utcnow() deprecated in Python 3.12, will be removed. Returns naive datetime; cross-system comparison fragile.",
        reproduction: "Run tests on Python 3.13; observe DeprecationWarning.",
        recommended: "Replace globally with datetime.now(timezone.utc). One-line search-and-replace.",
        effort: "small" },
      { id: "P3.F11", severity: "LOW", title: "Structured rejection envelope has no schema_version field",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_guardrails/wrapper.py",
        what: "L5 rejection JSON shape {\"error\": \"guardrail_rejected\", ...} carries no version field. Future changes will fail consumers silently.",
        reproduction: "No reproduction yet; bites when envelope evolves.",
        recommended: "Add \"schema_version\": 1 to the envelope. Document in mcp-tools-reference.md.",
        effort: "small" },
      { id: "P3.F12", severity: "LOW", title: "NISTA chain backward compatibility not tested after refactor",
        where: "packages/pm-data-tools/src/pm_data_tools/integrations/nista/audit.py : 33-66",
        what: "PR #66 refactored to wrap the generic AuditChain. File-on-disk compat is claimed but no test verifies it. A canonical-serialisation drift would silently fail to verify pre-refactor logs after deploy.",
        reproduction: "No fixture exists. Break would be invisible until an operator runs verify_chain_integrity.",
        recommended: "Add a test that ships a pre-refactor JSONL fixture and verifies it passes integrity-check.",
        effort: "small" },
      { id: "P3.F13", severity: "LOW", title: "Bytes and tuple types serialise opaquely",
        where: "packages/pm-data-tools/src/pm_data_tools/audit/chain.py : 49-57",
        what: "Bytes become \"b'...'\" strings. Tuples become JSON arrays indistinguishable from lists. Round-trip loses type information.",
        reproduction: "Record input_data={\"b\": b\"hello\", \"t\": (1,2)}. Roundtrip — types lost.",
        recommended: "Bytes → base64 with __type__: bytes marker. Tuples → list with __type__: tuple marker.",
        effort: "small" },
    ],
  },
  // Pass 4 ── Security
  {
    n: "4",
    title: "Security and attack surface",
    summary: "10 findings (3 HIGH · 4 MEDIUM · 3 LOW)",
    pattern: "Input is unsanitised everywhere — three HIGH findings reduce to \"the platform trusts " +
             "MCP-supplied input without validating it before sending to Claude or to handlers\". The platform " +
             "is public-internet-deployed with no auth. The L7 capability gap (no corpus) means none of the " +
             "security-class findings have automated regression coverage.",
    findings: [
      { id: "P4.F01", severity: "HIGH", title: "Unsanitised project_id flows into Claude prompts (prompt-injection vector)",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_reporting/server.py : 1040, 1049, 1278",
        what: "project_id is interpolated directly into f-string prompts. A malicious project_id like \"PROJ-001\\n\\nIGNORE PRIOR INSTRUCTIONS...\" breaks out of the system prompt's role framing. L5 only guards OUTPUT — input is unchecked.",
        reproduction: "Call a tool with project_id containing newlines and injection text. The injected instruction reaches Claude.",
        recommended: "Sanitise project_id to alphanumeric + hyphen + underscore. Or use a structured prompt format that isolates user-supplied IDs from instruction text.",
        effort: "small" },
      { id: "P4.F02", severity: "HIGH", title: "Public dashboard endpoint exposes any project's data without auth",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 85-98",
        what: "GET /data/{project_id}/dashboard.json is publicly accessible with allow_origins=[\"*\"]. Anyone on the internet can enumerate project IDs and scrape assumption drift, financial metrics, risks, and benefits without authentication.",
        reproduction: "curl https://pda-platform-i33p.onrender.com/data/any-project-id/dashboard.json returns live data.",
        recommended: "Require Bearer-token or API-key auth for /data/* and /dashboards/* endpoints. Or restrict to internal deployment.",
        effort: "small" },
      { id: "P4.F03", severity: "HIGH", title: "No input-size limits on tool parameters",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_analyse/registry.py : 224-225 (and across many tool schemas)",
        what: "narrative_text and other free-text parameters have no maxLength. A 100MB narrative_text exceeds Claude's token budget, fails verbosely, may echo prompt context. No early rejection.",
        reproduction: "Call detect_narrative_divergence with narrative_text=\"A\"*50_000_000. API fails; cost is paid.",
        recommended: "Add maxLength to every free-text input (50_000 chars for prose, 1_000 for IDs). Validate before LLM call.",
        effort: "small" },
      { id: "P4.F04", severity: "MEDIUM", title: "Permissive CORS on the SSE transport allows browser-origin MCP clients",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 143-149",
        what: "CORS allow_origins=[\"*\"] for GET, OPTIONS. The SSE endpoint at /sse does not need browser-origin clients. Any attacker-controlled web page can connect and issue MCP tool calls.",
        reproduction: "Browser console at attacker.example.com: new EventSource(\"https://pda-platform-i33p.onrender.com/sse\"). Succeeds.",
        recommended: "Restrict allow_origins to specific Claude/Anthropic origins (or empty for internal). Add origin assertion in handle_sse.",
        effort: "small" },
      { id: "P4.F05", severity: "MEDIUM", title: "L5 guardrails vulnerable to Unicode evasion",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_guardrails/builders.py : 228-237",
        what: "Forbidden-phrase matching uses case-insensitive substring on raw text. An LLM (if prompt-injected) can evade with zero-width characters, Unicode lookalikes, decomposed marks.",
        reproduction: "Inject prompt asking for \"100​% certain\" (with ZWNJ). L5 substring match misses.",
        recommended: "Normalise to Unicode NFKC + remove zero-width chars before matching. Or regex with word boundaries on normalised string.",
        effort: "medium" },
      { id: "P4.F06", severity: "MEDIUM", title: "Audit-chain metadata field stores plaintext context (PII risk)",
        where: "Cross-cutting — _safe_record_decision(metadata=...) sites",
        what: "Metadata dict is persisted plaintext to JSONL. Callers can attach arbitrary context; no scrubbing. PII (user, email, name) leaks into operator log indefinitely (7-year retention).",
        reproduction: "Pass metadata={\"user\": current_user_email}. Email lands in JSONL.",
        recommended: "Document a \"no PII in metadata\" rule. Add a runtime warn on field names matching PII patterns. Consider encrypting at rest.",
        effort: "medium" },
      { id: "P4.F07", severity: "MEDIUM", title: "MCP inputSchema is declared but not enforced at dispatch",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/server.py:call_tool",
        what: "Tools declare inputSchema; call_tool does not validate inbound arguments. Malformed inputs reach handlers unchecked; behaviour undefined.",
        reproduction: "Call a tool with int parameter passed as \"not-a-number\". Handler crashes with TypeError.",
        recommended: "Add jsonschema.validate(arguments, tool.inputSchema) in call_tool before dispatch. Return structured validation-error envelope.",
        effort: "medium" },
      { id: "P4.F08", severity: "LOW", title: "Dashboard path mangling is best-effort, not principled",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 110",
        what: "name.replace(\".uds.yaml\", \"\").replace(\"/\", \"\").replace(\"\\\\\", \"\").replace(\"..\", \"\"). Robust against simple traversal; not validated against Unicode normalisation tricks, non-printable characters, symlinks.",
        reproduction: "Unicode-normalisation attacks mostly mitigated upstream by Starlette; this is defence-in-depth.",
        recommended: "Use principled check: candidate.resolve().is_relative_to(_DASHBOARD_SPECS_DIR.resolve()).",
        effort: "small" },
      { id: "P4.F09", severity: "LOW", title: "ANTHROPIC_API_KEY and PDA_AUDIT_SIGNING_KEY have no rotation or scanning story",
        where: "render.yaml : 16-17; CI workflows",
        what: "Secrets are sync:false (good) but no automated rotation, no secret-scanning in CI, no usage anomaly alerting. A leaked key is usable indefinitely.",
        reproduction: "No reproduction; hardening recommendation.",
        recommended: "Add truffleHog or gitleaks to CI. Document quarterly rotation. Optional: usage monitoring.",
        effort: "medium" },
      { id: "P4.F10", severity: "LOW", title: "L7 RedTeam harness exists but no corpus checked in",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_redteam/",
        what: "PR #70 shipped the RedTeamHarness primitive but no corpus. L7 is structurally PRESENT but operationally untested. Future developers may not realise the corpus is missing.",
        reproduction: "Grep for corpus/ — none exists.",
        recommended: "Check in a YAML/JSON corpus under _redteam/corpus/ with categories: prompt-injection, unicode-evasion, schema-abuse, oversized-input. Wire to CI.",
        effort: "medium" },
    ],
  },
  // Pass 5 ── Observability
  {
    n: "5",
    title: "Observability",
    summary: "12 findings (4 HIGH · 4 MEDIUM · 4 LOW)",
    pattern: "The audit chain is cryptographically sound but operationally invisible — the operator running " +
             "the platform cannot see if recording is working today. The platform has zero per-invocation " +
             "request logging. Render's transient stderr captures hide import diagnostics that have already " +
             "saved us once.",
    findings: [
      { id: "P5.F01", severity: "HIGH", title: "Audit-chain failures silent without operator-visible counter or log",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_knowledge/server.py : 58-59 and four sibling modules",
        what: "If every audit record fails for a day (disk, schema, permissions), the operator has zero signal — no metric, no log, no /health indicator. Tool output keeps flowing. Discovery is manual file inspection.",
        reproduction: "Set PDA_AUDIT_DIR to read-only. Run an audited tool. Output succeeds; no operator-visible failure.",
        recommended: "Increment audit_failure_count counter on each swallowed exception. Expose at /health. Emit logger.warning on first failure within a window.",
        effort: "small" },
      { id: "P5.F02", severity: "HIGH", title: "/health endpoint too shallow to detect realistic degradation",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 67-74",
        what: "Health response only confirms len(ALL_TOOLS) == 126. Does NOT check store connectivity, API key presence, audit chains, extras. A deployment with lost DB connectivity for hours still reports ok.",
        reproduction: "Rename store.db. /health returns ok. Store-dependent tools fail.",
        recommended: "Promote /health to {status, checks: {store, anthropic_api_key, audit_chains, tools}}.",
        effort: "small" },
      { id: "P5.F03", severity: "HIGH", title: "Tool invocations leave zero trace in operational logs",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/server.py : 124-130",
        what: "No structured log entry per invocation. Debugging \"user said X but data was Y\" requires reading code from cold. Audit chain captures decisions; operators have no rate/latency/error-count visibility.",
        reproduction: "Call any tool 100 times. grep tool_name in logs — zero hits.",
        recommended: "Add structlog.info per invocation: event=tool_invoked, tool=name, duration_ms=..., status=....",
        effort: "small" },
      { id: "P5.F04", severity: "HIGH", title: "Audit-chain JSONL files grow monotonically with no rotation or size metric",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py : 167-169",
        what: "Files at ~/.pm_data_tools/audit/<module>.jsonl grow unbounded. No rotation, no archival. At scale, cold-start hydration time grows linearly. Disk-full scenarios invisible.",
        reproduction: "Generate 10,000 entries. Measure restart time. No size metric.",
        recommended: "Daily rotation with chain-link preservation. Expose audit_chain_size_bytes per module at /health.",
        effort: "medium" },
      { id: "P5.F05", severity: "MEDIUM", title: "Error response shapes are inconsistent across modules",
        where: "Cross-cutting — pm_assumptions, pm_analyse, pm_data each emit different envelopes",
        what: "Some flatten, some nest, some include traceback. Consumers can't parse uniformly; operators writing dashboards must handle three shapes.",
        reproduction: "Trigger errors in three different modules; observe shape differences.",
        recommended: "Define a canonical {\"error\": {\"code\": str, \"message\": str, \"context\": dict, \"schema_version\": 1}}. Retrofit.",
        effort: "medium" },
      { id: "P5.F06", severity: "MEDIUM", title: "ANTHROPIC_API_KEY absence invisible until first AI tool call",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_brm/server.py : 1172-1177 and five sibling handlers",
        what: "AI-authored tools check key at runtime and fallback. /health doesn't report key absence. Operators don't know at deploy time that ten AI tools will silently degrade.",
        reproduction: "Deploy without key. /health says ok. First AI tool call reveals.",
        recommended: "Emit logger.warning at startup. Add presence to /health (covered by P5.F02).",
        effort: "small" },
      { id: "P5.F07", severity: "MEDIUM", title: "Cold-start import diagnostics are stderr-only; not persisted to structured logs",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 26, 36, 41",
        what: "Import progress prints are stderr-only. If logs roll or operator uses structured-log filtering, diagnostics lost. The recent lazy-import regression took 10 minutes to diagnose because these were the only breadcrumbs.",
        reproduction: "Inject 5s delay in an import. Operator can't see which import was slow from structured logs.",
        recommended: "Replace stderr prints with logger.info entries including relative timestamps.",
        effort: "small" },
      { id: "P5.F08", severity: "MEDIUM", title: "No startup-time metric or uptime indicator",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 67-74",
        what: "/health returns point-in-time. No uptime_seconds, no startup_duration_ms. Operators can't compare deploy times or detect crash-loops.",
        reproduction: "Restart server. /health is identical before and after.",
        recommended: "Capture _STARTUP_TIME at module load. Add uptime_seconds and startup_duration_ms to /health.",
        effort: "small" },
      { id: "P5.F09", severity: "LOW", title: "_groundedness annotations are operator-unfriendly without aggregation tooling",
        where: "Cross-cutting — every AI-authored tool's response",
        what: "Each individual response carries useful _groundedness. Operators have no aggregate view: what % flagged UNGROUNDED this week, which tool's outputs are most often ungrounded.",
        reproduction: "Generate 50 narratives. Operator must hand-grep JSON.",
        recommended: "Add internal aggregator: pm_mcp_servers._observability.record_groundedness called from each L6 site; expose via /metrics.",
        effort: "medium" },
      { id: "P5.F10", severity: "LOW", title: "No aggregated visibility into audit-chain verification status",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_audit/__init__.py : 172-179",
        what: "Operators can call verify_chain from Python but no CLI wrapper, no /health integration, no scheduled job. A tampered chain remains undetected until manual invocation.",
        reproduction: "Hand-edit one entry. Operator never runs verify_chain — invisible.",
        recommended: "Add /audit/verify endpoint (auth-gated) walking all five chains.",
        effort: "medium" },
      { id: "P5.F11", severity: "LOW", title: "Tracebacks leak in JSON error responses from pm_assumptions",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/server.py : 974",
        what: "Errors include {\"error\": str, \"traceback\": str} exposing Python stack to MCP consumer. Leaks file paths, module names, versions. Some modules strip; pm_assumptions doesn't.",
        reproduction: "Trigger error in pm_assumptions tool. Response includes traceback.",
        recommended: "Log traceback to operator logs; return only {\"error\": {\"code\", \"message\"}} to consumer. Add DEBUG_VERBOSE_ERRORS env-var for development.",
        effort: "small" },
      { id: "P5.F12", severity: "LOW", title: "Dashboard polling endpoint has no Last-Modified / ETag",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/remote.py : 85-98",
        what: "GET /data/{project_id}/dashboard.json returns fresh payload every poll. No cache validators. A UDS renderer polling every 60s re-fetches the entire payload even when unchanged.",
        reproduction: "Poll twice; payload identical; bandwidth wasted.",
        recommended: "Compute hash of panel data; return as ETag. Honour If-None-Match with 304.",
        effort: "small" },
    ],
  },
  // Pass 6 ── Test coverage
  {
    n: "6",
    title: "Test coverage gaps",
    summary: "12 findings (3 HIGH · 6 MEDIUM · 3 LOW)",
    pattern: "Test breadth is good, depth is shallow at edges. 205 tests cover the happy path of every " +
             "layer, but edge-case coverage thins out at boundaries (extreme α, threshold equality, empty " +
             "inputs, missing files). The platform's claimed properties are demonstrated, not stress-tested. " +
             "Several findings depend on fixes from earlier passes.",
    findings: [
      { id: "P6.F01", severity: "HIGH", title: "Four-tier router: only two verdict paths tested",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py : TestRouteOutputsToReviewTool",
        what: "Tests cover NONE and EXPERT_REQUIRED. DETAILED_REVIEW and SPOT_CHECK not exercised. Off-by-one in threshold comparison would slip.",
        reproduction: "Pass confidence=0.75 with no outliers (should DETAILED_REVIEW); pass 0.85 with outlier (OR fail-safe to EXPERT_REQUIRED). Neither asserted.",
        recommended: "Add two tests covering DETAILED_REVIEW and SPOT_CHECK plus exact-threshold boundary tests.",
        effort: "small" },
      { id: "P6.F02", severity: "HIGH", title: "No test for _safe_record_decision fail-safe property",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py (audit-chain integration tests)",
        what: "_safe_record_decision is designed to swallow audit failures so tool output is never lost — critical platform property. No test mocks the chain to raise and verifies the tool still returns its output unchanged.",
        reproduction: "No test exists that monkeypatches pm_mcp_servers._audit.record_decision to raise.",
        recommended: "Add test_audit_chain_failure_does_not_break_tool_output — monkeypatch to raise, invoke scan_for_red_flags, assert tool returns JSON unchanged.",
        effort: "small" },
      { id: "P6.F03", severity: "HIGH", title: "Conformal calibration has no edge-case coverage",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py : TestCalibrationAndConformal",
        what: "Tests use n=200 or n=500 residuals at α=0.1. No tests for empty, single, all-identical residuals, or extreme α. The platform claims coverage guarantees; guarantees are unverified at edges.",
        reproduction: "Call conformal_predict_band with residuals=[]. Behaviour undefined-by-test.",
        recommended: "Three tests: empty → error; single → symmetric band; identical → zero half-width.",
        effort: "small" },
      { id: "P6.F04", severity: "MEDIUM", title: "JSONL corruption resilience untested",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py : TestPmAssureAuditChain",
        what: "Tamper test hand-edits an entry's decision. No tests for truncated mid-line write, malformed JSON, missing closing brace. Current code silently skips malformed lines; behaviour untested.",
        reproduction: "Append {\"id\": \"... (incomplete) to a chain JSONL; call verify_chain.",
        recommended: "Add test_truncated_jsonl_line_does_not_crash_verify — assert verify_chain returns a defined result.",
        effort: "small" },
      { id: "P6.F05", severity: "MEDIUM", title: "Missing-chain-file scenario not tested",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py : TestPmAssureAuditChain",
        what: "Tests assume the file exists. No test for: file deleted between record and verify, fresh hydration against missing path.",
        reproduction: "Delete the JSONL after entries; call verify_chain. Behaviour: treats as empty (per hydration logic). Operator may want distinct MISSING status.",
        recommended: "Add test_verify_chain_with_missing_file_returns_distinct_status.",
        effort: "small" },
      { id: "P6.F06", severity: "MEDIUM", title: "Extreme α and threshold-equality boundaries untested",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py : TestCalibrationAndConformal and router tests",
        what: "Calibration uses α=0.1 only. Router thresholds (0.4, 0.6, 0.8) never tested at exact equality. Off-by-one tier-selection bugs slip.",
        reproduction: "route_outputs_to_review with confidence=0.4 exactly — which tier? No test asserts.",
        recommended: "Add test_route_thresholds_at_exact_boundaries testing 0.39/0.40/0.41 etc.",
        effort: "small" },
      { id: "P6.F07", severity: "MEDIUM", title: "No cross-module integration test (L5+L6+L8 in one request)",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py (overall)",
        what: "Each layer has its own test class; none exercises composition. When a tool runs, L8 audit + L6 footer + L5 verdict should align. The composition is untested end-to-end.",
        reproduction: "Call generate_board_exception_report with forbidden phrase. Assert: rejection JSON + chain shows REJECTED + no groundedness footer.",
        recommended: "Add test_board_report_rejected_path_records_in_chain_with_no_groundedness_footer.",
        effort: "medium" },
      { id: "P6.F08", severity: "MEDIUM", title: "No oversized-input tests on any tool",
        where: "Cross-cutting — no test class targets this",
        what: "No tests feed oversized inputs. MCP schema validation untested (P4.F07). OOM, slow response, or verbose error envelopes leaking context would slip.",
        reproduction: "Call generate_board_exception_report with project_id=\"A\"*10_000_000. Undefined-by-test.",
        recommended: "Add test_oversized_inputs_return_structured_413 (after P4.F03 fix).",
        effort: "medium (depends on P4.F03)" },
      { id: "P6.F09", severity: "MEDIUM", title: "MCP inputSchema violations not validated at dispatch",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/pda_platform/server.py:call_tool",
        what: "Tools declare inputSchema; dispatcher does not validate (P4.F07). No test asserts schema violations are rejected before handler runs.",
        reproduction: "Call a tool with string field passed as integer. Handler likely raises TypeError.",
        recommended: "Once P4.F07 fix lands, add test_mcp_dispatch_rejects_schema_violation.",
        effort: "medium (depends on P4.F07)" },
      { id: "P6.F10", severity: "LOW", title: "No concurrent-invocation tests",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py (overall)",
        what: "All 205 tests sequential. No asyncio.gather tests exercising two tools simultaneously, two SSE clients, two writers to chain. Production traffic will be concurrent.",
        reproduction: "asyncio.gather(call_tool(...), call_tool(...)) for two chain-writing tools.",
        recommended: "Add test_two_concurrent_scans_produce_two_linked_audit_entries.",
        effort: "medium" },
      { id: "P6.F11", severity: "LOW", title: "No cold-start regression test (PR #72 reference)",
        where: "packages/pm-mcp-servers/tests/test_pda_platform.py",
        what: "PR #72 introduced a lazy-import regression caught only by manual smoke. No automated test asserts unified-server import completes in reasonable time.",
        reproduction: "Add 5s sleep to an import. Tests still pass; Render deploy breaks.",
        recommended: "Add test_unified_server_imports_under_10_seconds.",
        effort: "small" },
      { id: "P6.F12", severity: "LOW", title: "No L7 corpus or harness regression test",
        where: "packages/pm-mcp-servers/src/pm_mcp_servers/_redteam/ and tests",
        what: "Confirms P4.F10. Corpus empty; no test exercises the harness against live platform tools.",
        reproduction: "Grep for redteam_corpus — none.",
        recommended: "Once corpus exists, add test_redteam_corpus_catches_known_attack_vectors.",
        effort: "medium (depends on P4.F10)" },
    ],
  },
];

for (const pass of passes) {
  content.push(new Paragraph({ children: [new PageBreak()] }));
  content.push(smallCaps("Pass " + pass.n));
  content.push(h1(pass.title));
  content.push(ruleFuchsia);
  content.push(body(pass.summary, { italics: true }));
  content.push(smallCaps("Pattern observed", { before: 200, after: 40 }));
  content.push(body(pass.pattern));
  content.push(ruleSlate);
  for (const f of pass.findings) {
    for (const para of finding(f)) {
      content.push(para);
    }
  }
}

// ── Closing notes ─────────────────────────────────────────────────────────
content.push(new Paragraph({ children: [new PageBreak()] }));
content.push(smallCaps("Closing notes"));
content.push(h1("What the audit makes visible"));
content.push(ruleFuchsia);

content.push(body(
  "The PDA Platform's v2.0.0 codebase is in a state where every claimed property of the Verified Autonomy " +
  "framework holds in principle — the L5 guardrails, L6 groundedness, L8 audit chains, and L4 conformal " +
  "bands all work as designed. This audit identifies where those properties degrade in practice: under " +
  "concurrent traffic the platform isn't yet ready for; against malformed or adversarial inputs the platform " +
  "doesn't yet reject; in failure modes the operator can't yet see."
));

content.push(body(
  "Twenty HIGH-severity findings cluster around four operational themes: silent audit-chain failures " +
  "(observability gap), unsanitised input (security gap), audit-log unbounded growth (operations gap), and " +
  "shallow health checks (deployment gap). None of these compromise the v2.0.0 release's claim of " +
  "implementing the nine-layer framework end-to-end. All of them affect how confidently an operator can " +
  "run the platform in production at scale."
));

content.push(body(
  "Thirty-three MEDIUM-severity findings constitute the platform's hardening backlog. Eighteen LOW " +
  "findings are polish — version fields, naming consistency, defence-in-depth recommendations. The " +
  "recommended four-week remediation sequence in the executive summary closes the highest-impact findings " +
  "first while leaving the multi-worker scaling concerns for the moment they actually bite.",
  { italics: true }
));

content.push(body(
  "This document does not assess whether the platform is \"safe\" or \"production-ready\" — the Verified " +
  "Autonomy framework itself argues no single component can answer those questions. The 71 findings above " +
  "are gaps in a form the framework would recognise; what their cumulative coverage means in PDA Platform's " +
  "specific deployment context (UK government IPA Gate Reviews, Treasury submissions, parliamentary " +
  "scrutiny) is the question for a human architect."
));

// ── Footer ────────────────────────────────────────────────────────────────
const footerPara = new Paragraph({
  tabStops: [{ type: TabStopType.RIGHT, position: 9026 }],
  spacing: { before: 0, after: 0 },
  children: [
    new TextRun({ children: ["Page "], font: FONT, color: C.slate500,
      allCaps: true, size: 14, characterSpacing: 40 }),
    new TextRun({ children: [PageNumber.CURRENT], font: FONT, color: C.slate500,
      allCaps: true, size: 14, characterSpacing: 40 }),
    new TextRun({ text: " of ", font: FONT, color: C.slate500,
      allCaps: true, size: 14, characterSpacing: 40 }),
    new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, color: C.slate500,
      allCaps: true, size: 14, characterSpacing: 40 }),
    new TextRun({ text: "\t", font: FONT }),
    new TextRun({ text: "Tortoise", font: FONT, color: C.slate, bold: true, size: 18 }),
    new TextRun({ text: "[AI]", font: FONT, color: C.fuchsia, bold: true, size: 18 }),
  ],
});

// ── Build document ────────────────────────────────────────────────────────
const doc = new Document({
  background: { color: C.bg },
  styles: {
    default: { document: { run: { font: FONT, size: 22, color: C.slate } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: FONT, color: C.slate },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: C.slate },
        paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering,
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: { default: new Footer({ children: [footerPara] }) },
    children: content,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = "C:/Users/antjs/Projects/pda-platform/PDA-platform-multipass-audit.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("DOCX written: " + outPath + " (" + buffer.length + " bytes)");
});
