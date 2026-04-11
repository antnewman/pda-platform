# Lessons Learned — A Guide for Project Delivery Professionals

This guide explains the lessons learned capabilities available in the PDA Platform. No technical background is needed.

---

## What this module does

Government projects fail for a finite set of reasons. Optimism bias in the business case. Supplier dependencies that were never stress-tested. Governance structures that looked right on paper but collapsed under pressure. Capability gaps that were flagged in Gate 2 and still unresolved at Gate 4.

The IPA's own research, published annually in the Government Major Projects Portfolio report, confirms that the same failure modes recur across programmes, departments, and decades. Lessons are learned in individual post-implementation reviews, then lost. The next programme team starts from scratch.

The `pm-lessons` module is designed to break that cycle. It uses AI to extract structured lessons from gate review reports, PIRs, and lessons workshops — capturing the root cause, not just the symptom — and stores them in a searchable, cross-project corpus. Portfolio managers and assurance reviewers can then query that corpus to surface patterns that transcend any single project. Future project teams can search it before they repeat the mistake.

---

## When to use it

- When you receive a gate review report or PIR and want to capture the lessons systematically rather than filing the document.
- When preparing a formal Lessons Learned section for a PIR or gate review report and need it written to IPA standard.
- When briefing a new SRO or project manager who is taking on an established programme — search for what the organisation already knows about programmes of this type.
- When conducting a portfolio retrospective and need to identify systemic issues affecting multiple projects, not just programme-by-programme summaries.
- When a gate reviewer asks "what lessons from comparable programmes are relevant here?" — search the corpus before the review, not after.
- When an incoming Gate 3 or Gate 4 review panel asks "what were the conditions from the previous gate?" — the lessons store provides evidence of whether prior conditions were resolved or recurred.

---

## The five tools

### 1. `extract_lessons` — AI extraction from gate review text

This is the starting point. Pass in the text of a gate review report, PIR, or lessons workshop write-up, and the tool uses Claude to extract structured lessons automatically.

Each lesson is classified with:

| Field | Options | What it captures |
|-------|---------|-----------------|
| `category` | GOVERNANCE, DELIVERY, COMMERCIAL, TECHNICAL, PEOPLE | Which domain the lesson belongs to |
| `phase` | INITIATION, PLANNING, DELIVERY, CLOSURE, ANY | When in the lifecycle this lesson is most relevant |
| `severity` | HIGH, MEDIUM, LOW | How significant the lesson is for future programmes |
| `root_cause` | Free text | The underlying reason, not the surface symptom |
| `recommendation` | Free text | What to do differently — specific and actionable |
| `source_excerpt` | Verbatim quote ≤50 words | The exact passage in the document that supports this lesson |

The tool stores all extracted lessons in the AssuranceStore, associated with the project identifier and optionally with a gate stage annotation (GATE_0 through GATE_5, or PAR).

**Worked example**

A Gate 3 review report for a digital transformation programme contains this passage:

> "The programme entered Gate 3 without a confirmed commercial model for the data processing element. The review team found that this had been flagged as a risk at Gate 2 but the commercial team's capacity constraints meant it had not been resolved. The lack of a confirmed model creates material uncertainty over the EAC."

Calling `extract_lessons` on this text might produce:

```json
{
  "title": "Commercial model not resolved between gates",
  "category": "COMMERCIAL",
  "phase": "DELIVERY",
  "severity": "HIGH",
  "root_cause": "Capacity constraints in the commercial team prevented resolution of a known risk between Gate 2 and Gate 3, despite the risk being formally flagged.",
  "recommendation": "Assign named commercial resource accountability for resolving gate conditions before the next review, with formal SRO sign-off at the midpoint between gates.",
  "source_excerpt": "The programme entered Gate 3 without a confirmed commercial model... flagged as a risk at Gate 2 but the commercial team's capacity constraints meant it had not been resolved."
}
```

**When to annotate with a gate:**

If you know the document relates to a specific gate (e.g., a Gate 3 review report), set `gate: "GATE_3"`. This annotates all extracted lessons with that gate stage, enabling future searches filtered by gate. This is particularly valuable for building up a corpus of what typically goes wrong at each stage of the IPA lifecycle.

---

### 2. `get_project_lessons` — retrieve lessons for a project

Retrieves all stored lessons for a named project, with optional filters:

- `category` — narrow to one domain (e.g., only COMMERCIAL lessons)
- `gate` — narrow to lessons from a specific gate stage

Use this when reviewing a specific programme's lesson history, or when preparing a lessons section for a PIR and you want the full structured set before writing.

---

### 3. `search_project_lessons` — cross-project keyword search

Searches across **all** lessons in the store — not just one project. Use this to query the organisation's institutional memory.

**Useful search patterns:**

- `"supplier dependency"` — find all recorded lessons about supplier risk across the portfolio
- `"governance"` category filter + `"GATE_3"` — what governance lessons recur at Gate 3?
- `min_severity: "HIGH"` — surface only the most significant lessons matching your query
- `"benefits realisation"` — what has the organisation already learned about benefits delivery?

The tool returns each matching lesson with its `project_id`, so you can trace which programme it came from.

**Worked example**

Before a Gate 2 review on a new infrastructure programme, a portfolio manager runs:

```
search_project_lessons
  query: "procurement timeline"
  category: COMMERCIAL
  min_severity: HIGH
```

The response surfaces three HIGH-severity COMMERCIAL lessons from two previous programmes, all pointing to the same root cause: procurement timelines were set at Gate 1 without accounting for departmental approvals, compressing the Gate 2 to Gate 3 transition. The new programme's SRO uses this to challenge the commercial lead's timeline assumptions two months before the review.

---

### 4. `get_systemic_patterns` — AI pattern analysis across the corpus

This tool loads all lessons in the store and uses Claude to identify patterns that recur across multiple projects — systemic issues rather than programme-specific problems.

**Requirements:** At least 5 lessons must be in the store before this tool will run. The tool is designed for portfolio-level retrospectives, not single-project analysis.

**What it returns:**

Each pattern includes:
- The pattern name and category
- The number of lessons that exemplify it
- The project IDs where it appears
- Evidence (lesson titles) supporting the pattern
- A portfolio-level recommendation for systemic action

**Worked example output:**

```json
{
  "pattern": "Business case optimism on supplier capability",
  "category": "COMMERCIAL",
  "occurrences": 7,
  "projects_affected": ["PROJ-001", "PROJ-003", "PROJ-007"],
  "evidence": [
    "Supplier delivery capacity not independently verified at Gate 2",
    "Primavera schedule accepted from supplier without sense-check",
    "No contractual mechanism for schedule visibility beyond milestone dates"
  ],
  "recommendation": "Require independent schedule assurance from a quantity surveyor or technical adviser on all programmes with a primary delivery supplier before Gate 3."
}
```

When to use this: at portfolio board retrospectives, at the start of a spending review cycle when looking for systemic improvement opportunities, or when the IPA asks what the department has learned across its programme portfolio.

---

### 5. `generate_lessons_section` — AI-written section for PIRs and gate reviews

Retrieves stored lessons for a project and uses Claude to write a formatted lessons learned section suitable for direct inclusion in a formal document.

Three formats are available:

| Format | When to use | What it produces |
|--------|------------|-----------------|
| `pir` | Post-Implementation Review | Narrative grouped by category, root causes summarised, recommendations prioritised |
| `gate_review` | Gate review report | Concise bullets focused on risks to future phases; written for reviewers who scan quickly |
| `brief` | Executive summary | 3–5 key lessons, one short paragraph each, plain English |

**If no lessons are stored** for the project, the tool returns a template with guidance on how to populate the store using `extract_lessons` before running this tool.

---

## Common workflows

### Workflow A: Process a gate review report

1. Receive the gate review report as text.
2. Call `extract_lessons` with `document_type: "GATE_REVIEW"` and the appropriate `gate` annotation.
3. Call `get_project_lessons` to review what was extracted and verify it is complete.
4. Call `generate_lessons_section` with `format: "gate_review"` to produce a lessons section for the next review's opening pack.

### Workflow B: Prepare a PIR

1. Ensure lessons have been extracted from all relevant gate review reports during the programme lifecycle (Workflow A above).
2. Call `generate_lessons_section` with `format: "pir"`.
3. The tool retrieves all stored lessons, prioritises by severity, and produces a narrative grouped by category — ready to paste into the PIR.

### Workflow C: Pre-review portfolio query

1. Before a Gate 3 review on a new programme, call `search_project_lessons` with keywords relevant to the programme type (e.g., `"digital transformation"`, `"commercial model"`, `"contractor dependency"`).
2. Filter by `min_severity: "HIGH"` to focus on the most significant precedents.
3. Share the results with the review panel as context.

### Workflow D: Portfolio retrospective

1. Ensure lessons from at least 5 programmes have been extracted and stored.
2. Call `get_systemic_patterns` with no filters for a full cross-portfolio analysis.
3. If the portfolio is large, run once per category (GOVERNANCE, COMMERCIAL, TECHNICAL, PEOPLE, DELIVERY) to get focused output.
4. Use the ranked patterns to build a departmental lessons register and action plan.

---

## Limitations

- **AI extraction quality depends on document quality.** Gate review reports that are vague or heavily redacted will produce vague lessons. The tool extracts what the document contains — it does not fill in gaps.
- **Lessons must be extracted before they can be searched.** The store is only as good as what has been ingested. A portfolio that has not populated the store will return empty search results.
- **The AI does not validate recommendations against policy.** Recommendations are generated from the document text. A qualified practitioner should review them before circulation.
- **Pattern detection requires corpus depth.** `get_systemic_patterns` requires at least 5 lessons and produces the most reliable output with 20 or more lessons from 5 or more distinct projects.
- **Requires ANTHROPIC_API_KEY** for `extract_lessons`, `get_systemic_patterns`, and `generate_lessons_section`. `get_project_lessons` and `search_project_lessons` are deterministic and have no API dependency.
