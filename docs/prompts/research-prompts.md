# PDA Platform — Research Prompts

## Overview

These three prompts are ready-to-run analytical workflows for use with the PDA Platform MCP tools. Each prompt is a structured, step-by-step instruction set that guides Claude through a complete analysis — calling the right tools in the right sequence and synthesising the results into a professional report.

**How to use:**
1. Set the appropriate system prompt (e.g. `ipa-gate-review-methodology.md` for gate reviews)
2. Copy the prompt from the code block below
3. Replace `[PROJECT_ID]` with your actual project identifier
4. Paste as the user message and run

All three prompts are designed to be self-contained. Claude will call the tools, interpret the outputs, and produce a structured report in a single conversation turn.

---

## Research Prompt 1: Full Gate Readiness Analysis

**Purpose:** A comprehensive IPA-style gate readiness assessment, drawing on schedule data, risk exposure, financial health, assumption stability, and artefact currency to produce a Delivery Confidence Assessment with evidence-based ratings across all eight dimensions.

**Best used with:** The IPA Gate Review system prompt (`docs/prompts/ipa-gate-review-methodology.md`).

```
You are conducting a full IPA-style gate readiness analysis for project [PROJECT_ID].
Work through the following steps in order. Call each tool, interpret the output, and
carry the findings forward into the next step. Do not skip any step. After completing
all steps, synthesise the findings into a complete gate review report.

---

STEP 1 — Establish project context
Call: get_project_summary(project_id="[PROJECT_ID]")

Record:
- Project name, current phase, and stated gate target
- Overall status and any headline flags
- Approved budget and current forecast
- Planned and forecast completion dates

---

STEP 2 — Assess current gate readiness
Call: assess_gate_readiness(project_id="[PROJECT_ID]")

Record:
- Overall readiness rating and score
- Which gate is being assessed
- The top three readiness gaps
- Any mandatory criteria that are currently unmet

---

STEP 3 — Establish the readiness trend
Call: get_gate_readiness_history(project_id="[PROJECT_ID]")

Determine:
- Is readiness improving, stable, or deteriorating over the last three assessments?
- Which dimensions show the sharpest decline?
- Is the trend consistent with the time remaining to the gate?

---

STEP 4 — Compare against the previous assessment
Call: compare_gate_readiness(project_id="[PROJECT_ID]")

Note:
- Which dimensions have improved since the last assessment?
- Which have deteriorated?
- Are the deteriorating dimensions on the critical path to gate passage?

---

STEP 5 — Check artefact currency
Call: check_artefact_currency(project_id="[PROJECT_ID]")

Flag:
- Any mandatory artefacts that are missing
- Any artefacts that are stale (not updated within the expected review cycle)
- Whether the business case, risk register, and benefits realisation plan are all current

---

STEP 6 — Assess risk exposure
Call: get_risk_register(project_id="[PROJECT_ID]")

Assess:
- The number of open High and Very High risks
- Whether each high-severity risk has a named owner and active mitigation
- Whether any risks have breached tolerance without being escalated
- The overall risk exposure relative to the gate timeline

---

STEP 7 — Check assumption stability
Call: get_assumption_drift(project_id="[PROJECT_ID]")

Identify:
- Which assumptions are drifting furthest from their original basis
- Whether any drifting assumptions underpin critical cost, schedule, or benefits estimates
- Whether drifting assumptions have been converted to risks where appropriate

---

STEP 8 — Assess financial health
Call: get_cost_performance(project_id="[PROJECT_ID]")

Record:
- Cost Performance Index (CPI) and current spend against forecast
- Whether there is a credible, approved financial position
- Any variance trends that suggest the approved budget is under pressure
- Whether optimism bias was applied and is still reflected in current estimates

---

STEP 9 — Check confidence divergence
Call: check_confidence_divergence(project_id="[PROJECT_ID]")

Flag:
- Any dimensions where stated confidence is materially higher than the evidence supports
- Any patterns of overconfidence relative to objective indicators
- Whether project team confidence and independent evidence are broadly aligned

---

STEP 10 — Run the ARMM report
Call: get_armm_report(project_id="[PROJECT_ID]")

Extract:
- Overall ARMM maturity level (0-4) and score percentage
- The four dimension scores: TC (Technical Completeness), OR (Organisational Readiness),
  GA (Governance and Assurance), CC (Controls and Compliance)
- Any blocking topics — topics scored at zero that prevent a higher maturity level
- The top improvement priorities identified by the assessment
- Whether the ARMM maturity level is consistent with the gate being targeted
  (a project targeting Gate 3 should typically be at ARMM Level 2 or above)

---

STEP 11 — Get AI-suggested risk mitigations
Call: suggest_mitigations(project_id="[PROJECT_ID]")

Review:
- Which risks does the AI flag as highest priority for mitigation?
- Are the suggested mitigations already in place, or are they gaps?
- Are there mitigations suggested that conflict with current assumptions?
- Cross-reference with the risk register from Step 6 — are any High/Very High risks
  missing from the suggested mitigations?

---

STEP 12 — Run the full assurance workflow
Call: run_assurance_workflow(project_id="[PROJECT_ID]", workflow_type="FULL_ASSURANCE")

Record:
- The overall project health classification: HEALTHY / ATTENTION_NEEDED / AT_RISK / CRITICAL
- The aggregated risk signals across all assurance modules (P1–P8)
- The recommended actions generated by the workflow engine
- The executive summary produced by the workflow
- Whether the workflow health classification is consistent with your assessment
  from Steps 1–11. Material divergence between the workflow classification and
  your independent assessment should be flagged as a governance concern.

---

STEP 13 — Synthesise into a gate review report

Using the findings from all twelve steps above, produce a complete IPA Gate Review output
structured as follows. Apply the five-point DCA scale (Green / Amber-Green / Amber /
Amber-Red / Red) to the overall assessment and to each dimension individually.

OUTPUT FORMAT:

DELIVERY CONFIDENCE ASSESSMENT: [RATING]

Executive Summary
[2–3 sentences: overall DCA, the primary reasons for the rating, and the single most
important action required before the gate review proceeds]

Strengths
[Bullet list of genuine strengths, each grounded in tool outputs from Steps 1–12 above]

Areas Requiring Management Attention
[Bullet list of significant issues. For each, state which step's tool output evidences it
and why it matters to gate passage. Include findings from ARMM (Step 10), AI mitigations
(Step 11), and the assurance workflow (Step 12) where relevant.]

Conditions
[List any conditions that must be met before the project may proceed to the next gate.
Conditions are blocking — the project cannot progress without meeting them.
Format each as: "The project may not proceed to [next gate/stage] until [specific 
requirement] has been met and confirmed to [named authority]."
If no conditions apply, state: "No conditions — project may proceed subject to
the recommendations below."]

Recommended Actions
[Numbered list of advisory recommendations. Each must include: owner role, specific
action, target completion date or milestone. Prioritise by impact on gate readiness.
Recommendations do not block progression but must be formally responded to by the SRO.]

Assessment by Dimension
For each of the eight IPA dimensions below, provide:
- Dimension name and RAG rating
- 2–3 sentences of evidence-based assessment
- Where tool output was absent or insufficient to assess a dimension, state explicitly:
  "Evidence was not available to assess [dimension] — this should be treated as a gap
  requiring resolution before the gate review proceeds."

Dimensions to rate:
1. Strategic Context and Benefits
2. Leadership and Stakeholder Management
3. Risk Management
4. Governance and Assurance
5. Financials
6. Delivery Approach and Schedule
7. People and Capability
8. Commercial and Procurement

Evidence Gaps
[List any dimensions or specific questions where the tool outputs did not provide
sufficient evidence to support a rating. Do not assign a rating where evidence is absent
— flag the gap instead.]
```

---

## Research Prompt 2: Benefits Realisation Review

**Purpose:** A structured Green Book-aligned benefits realisation review, assessing whether planned benefits are on track to be delivered, identifying benefits at risk, and producing evidence-based recommendations for intervention.

**Best used with:** A benefits or outcome-focused system prompt, or standalone.

```
You are conducting a comprehensive benefits realisation review for project [PROJECT_ID],
aligned to HM Treasury Green Book principles. Work through the following steps in order.
Call each tool, interpret the output, and carry the findings forward. After completing
all steps, synthesise the findings into a benefits review report.

Green Book principles to apply throughout:
- Benefits must be specific and measurable — vague outcomes do not count
- Every benefit must have a named owner who is accountable for its realisation
- Attribution must be clear — benefits should be directly linkable to the project's
  interventions, not to external factors
- Benefits should be tracked against a baseline that was established at business case
  approval, not retrospectively set

---

STEP 1 — Establish strategic context
Call: get_project_summary(project_id="[PROJECT_ID]")

Record:
- The project's stated strategic objectives and intended outcomes
- The approved benefits realisation plan (if referenced)
- The current phase and proximity to benefits realisation milestones
- Whether a named Senior Responsible Owner (SRO) is identified

---

STEP 2 — Get overall benefits status
Call: get_benefits_health(project_id="[PROJECT_ID]")

Record:
- Overall benefits health rating
- Number of benefits currently On Track, At Risk, and Off Track
- Any benefits that have already been partially or fully realised
- Whether measurement mechanisms are in place for each benefit

---

STEP 3 — Forecast benefit realisation
Call: forecast_benefit_realisation(project_id="[PROJECT_ID]")

Assess:
- Which benefits are forecast to be delivered on time and in full?
- Which benefits have a forecast shortfall (partial realisation)?
- What is the aggregate benefits realisation confidence score?
- Are any benefits now forecast beyond the approved realisation horizon?

---

STEP 4 — Detect benefits drift
Call: detect_benefits_drift(project_id="[PROJECT_ID]")

Identify:
- Which benefits have drifted furthest from their original approved target values?
- Is the drift in timing, magnitude, or both?
- Were the original benefit targets based on realistic assumptions, or is the drift
  evidence of optimism bias at business case stage?

---

STEP 5 — Map benefit interdependencies
Call: get_benefit_dependency_network(project_id="[PROJECT_ID]")

Understand:
- Which benefits are dependent on other benefits being realised first?
- Are any high-value benefits downstream of at-risk benefits?
- Are there single points of failure in the benefit dependency chain?

---

STEP 6 — Assess cascade impact of drift
The get_benefits_cascade_impact tool takes a node_id (a specific benefit or enabler node
in the dependency network), not a project_id. For each benefit identified as At Risk or
Off Track in Steps 3 and 4, call:
  get_benefits_cascade_impact(node_id="[BENEFIT_NODE_ID]")
where [BENEFIT_NODE_ID] is the ID returned for that benefit in the dependency network
(Step 5). If multiple benefits are at risk, call the tool once per at-risk benefit.

Calculate:
- For each at-risk benefit, which downstream benefits are exposed if it fails to materialise?
- Is there a single at-risk benefit whose failure would cascade to multiple downstream benefits
  (a single point of failure in the benefits chain)?
- In aggregate, if all at-risk benefits fail, what proportion of the total approved benefits
  case is at risk?
- Does the remaining benefits case (excluding benefits at risk) still justify the approved
  whole-life cost?

---

STEP 7 — Evaluate benefits management maturity
Call: assess_benefits_maturity(project_id="[PROJECT_ID]")

Rate:
- How mature is the project's benefits management practice?
- Are benefits owners engaged and accountable?
- Is there a live benefits tracker with regular reporting?
- Is there evidence of benefits being actively measured (not just claimed)?

---

STEP 8 — Retrieve the AI-drafted narrative
Call: generate_benefits_narrative(project_id="[PROJECT_ID]")

Review the narrative for:
- Internal consistency with the quantitative data from Steps 2–7
- Any claims that are not supported by the measurement data
- Language that overstates confidence or attributes benefits to the project without
  sufficient evidence

---

STEP 9 — Synthesise into a Green Book-aligned benefits review

Using all findings from the steps above, produce a structured benefits review report.

OUTPUT FORMAT:

BENEFITS REALISATION REVIEW — PROJECT [PROJECT_ID]
Date of Assessment: [today's date]

Overall Realisability Confidence: [High / Medium / Low]
[Justify the confidence rating in 2–3 sentences, referencing specific tool outputs]

Benefits Summary Table
[For each benefit identified in the data, provide a one-line entry:
Benefit name | Owner | Target value | Forecast value | Status | Variance %]

Benefits at Risk
[For each benefit rated At Risk or Off Track, provide:
- Benefit name and original approved target
- Current forecast and variance from target
- Primary root cause of drift (timing / scope / assumption failure / dependency failure)
- Whether the drift has been formally escalated and a remediation plan agreed]

Root Cause Analysis
[Synthesise the patterns from across the at-risk benefits. Is the drift systematic
(pointing to a failure in how benefits were defined or planned) or isolated (specific
delivery failures)? Does the evidence suggest optimism bias was applied at business case
stage?]

Green Book Compliance Assessment
Rate each principle as Met / Partially Met / Not Met, with one sentence of evidence:
- Benefits are specific and measurable
- Every benefit has a named accountable owner
- Attribution is clear and defensible
- Benefits are tracked against a pre-established baseline
- A live benefits realisation plan is maintained and regularly reviewed

Recommended Interventions
[Numbered list. Each intervention must include: owner role, specific action, target
date, and expected impact on benefits confidence if the action is taken]

Evidence Gaps
[List any benefits or dimensions where data was absent or insufficient. Note where
benefit targets appear to have been set retrospectively, which would undermine the
credibility of the benefits case.]
```

---

## Research Prompt 3: Schedule and Cost Health Review

**Purpose:** A thorough schedule and cost health assessment combining Earned Value analysis, critical path examination, outlier detection, resource loading, and risk cross-referencing to produce an integrated schedule and cost confidence report.

**Best used with:** A programme controls or delivery assurance system prompt, or standalone.

```
You are conducting a full schedule and cost health review for project [PROJECT_ID].
Work through the following steps in order. Call each tool, interpret the output, and
carry the findings forward. After completing all steps, synthesise all findings into a
structured schedule and cost health report.

---

STEP 1 — Load project data and establish context
Call: load_project(project_id="[PROJECT_ID]")
Then call: get_project_summary(project_id="[PROJECT_ID]")

Record:
- Project name, current phase, and delivery methodology
- Planned start and end dates, and the current forecast completion date
- Approved budget (Budget at Completion, BAC) and current cost forecast
- Number of tasks, milestones, and workstreams
- Overall reported health status

---

STEP 2 — Understand the critical path
Call: get_critical_path(project_id="[PROJECT_ID]")

Analyse:
- How many tasks sit on the critical path?
- What is the total float available on the longest chain?
- Are there near-critical paths (float within 10% of the critical path duration) that
  could become critical if a single task slips?
- Are critical path tasks resourced and owned?

---

STEP 3 — Identify schedule outliers
Call: detect_outliers(project_id="[PROJECT_ID]")

Flag:
- Tasks with unusually long durations relative to comparable tasks at the same level
- Tasks with zero or negative float that are not currently on the critical path
  (these are hidden risks)
- Tasks that have not been updated recently relative to their planned progress date
- Any pattern of outliers concentrated in a single workstream or delivery phase

---

STEP 4 — Forecast the AI-predicted completion date
Call: forecast_completion(project_id="[PROJECT_ID]")

Record:
- The point estimate for forecast completion date
- The confidence interval (P50 and P80 completion dates, if available)
- The key assumptions driving the forecast
- The gap between the AI forecast and the current project-reported forecast date
- Whether the forecast completion date is before or after any contractual or political
  deadline

---

STEP 5 — Compare against the approved baseline
Call: compare_baseline(project_id="[PROJECT_ID]")

Assess:
- Schedule variance (SV): how many days/weeks ahead or behind baseline?
- Cost variance (CV): how much over or under the approved baseline cost?
- Which workstreams account for the largest share of variance?
- Has scope changed since the baseline was set, and if so, has the baseline been
  formally rebaselined through change control?

---

STEP 6 — Compute Earned Value metrics
Call: compute_ev_metrics(project_id="[PROJECT_ID]")

Extract and interpret:
- Schedule Performance Index (SPI): SPI < 0.85 indicates significant schedule slippage
- Cost Performance Index (CPI): CPI < 0.9 indicates cost overrun trajectory
- Estimate at Completion (EAC): compare to the approved BAC — what is the projected
  overrun or underspend?
- To-Complete Performance Index (TCPI): is the remaining work achievable at the
  required efficiency?
- Note any divergence between SPI and CPI — a project that is on schedule but over
  budget may be accelerating spend to recover schedule, which is unsustainable

---

STEP 7 — Cross-check financial data
Call: get_cost_performance(project_id="[PROJECT_ID]")

Verify:
- Is the financial data consistent with the EV metrics from Step 6?
- What is the current spend profile — front-loaded, back-loaded, or broadly linear?
- Is there a credible, funded cost-to-complete?
- Has any draw-down of contingency or management reserve occurred, and if so, is the
  remaining reserve sufficient for the residual risk?

---

STEP 8 — Assess resource loading on the schedule
Call: analyse_resource_loading(project_id="[PROJECT_ID]")

Identify:
- Are there resource over-allocations on the critical path or near-critical paths?
- Are any key resources (named individuals or scarce skill sets) over-committed in
  the next 90 days?
- Is the resource plan consistent with the forecast completion date — i.e., is the
  schedule achievable with the resources actually available?
- Are there resource conflicts between workstreams that could create cascading delays?

---

STEP 9 — Get the overall health assessment
Call: assess_health(project_id="[PROJECT_ID]")

Record:
- The overall health score and component scores by dimension
- Any automatic red flags raised by the assessment
- Whether the health trajectory is improving or deteriorating
- The health assessment's alignment with the EV data from Step 6

---

STEP 10 — Cross-reference schedule risks
Call: get_risk_register(project_id="[PROJECT_ID]")

Identify:
- Which open risks could directly affect the critical path?
- Are schedule risks owned by the appropriate workstream leads?
- Is the aggregate schedule risk exposure quantified and reflected in the programme's
  schedule contingency?
- Are there any risks flagged as High or Very High that have no active mitigation and
  sit on, or adjacent to, the critical path?

---

STEP 11 — Synthesise into a schedule and cost health report

Using all findings from Steps 1–10, produce a complete schedule and cost health report.

OUTPUT FORMAT:

SCHEDULE AND COST HEALTH REVIEW — PROJECT [PROJECT_ID]
Date of Assessment: [today's date]

Overall Verdict: [On Track / At Risk / Off Track]
[2–3 sentences summarising the headline position on both schedule and cost, and the
single most significant factor affecting delivery confidence]

---

Schedule Confidence

Current Status:
- Baseline completion date: [from Step 5]
- Current reported completion date: [from Step 1]
- AI forecast completion date (P50): [from Step 4]
- AI forecast completion date (P80): [from Step 4]
- Schedule variance from baseline: [from Step 5]
- Schedule Performance Index (SPI): [from Step 6]

Schedule Confidence Rating: [High / Medium / Low]
[Justify in 2–3 sentences. A rating of Medium or Low requires a specific explanation
of the evidence that has reduced confidence]

Key Schedule Risks:
[For each material schedule risk, state: risk description, probability, impact in days,
whether it is on the critical path, and the current mitigation status]

Schedule Outliers Requiring Attention:
[List the top outlier tasks from Step 3, with explanation of why each is a concern]

---

Cost Confidence

Current Status:
- Budget at Completion (BAC): [from Steps 1 and 6]
- Estimate at Completion (EAC): [from Step 6]
- Projected variance (EAC minus BAC): [from Step 6]
- Cost Performance Index (CPI): [from Step 6]
- To-Complete Performance Index (TCPI): [from Step 6]
- Remaining contingency: [from Step 7]

Cost Confidence Rating: [High / Medium / Low]
[Justify in 2–3 sentences. Note whether the CPI trend is improving or deteriorating,
and whether the remaining contingency is proportionate to the residual risk]

---

Resource Assessment
[Summarise the findings from Step 8: whether the schedule is resourced to succeed,
and the top resource constraints that need to be resolved]

---

Top Recommended Recovery Actions
[Numbered list, ordered by priority. Each action must include:
1. Owner role (not a name — a role)
2. Specific action required
3. Target completion date or milestone
4. Expected impact on schedule or cost confidence if the action is taken]

---

Evidence Quality
[Note any steps where data was absent, inconsistent, or of insufficient quality to
support a confident assessment. Flag where EV data and reported schedule/cost data
are materially inconsistent — this itself is a governance concern.]
```

---

## Tips for Best Results

**Always load the project first if working with schedule data.**
The `load_project` tool parses the source schedule file and populates the store. Tools
like `get_critical_path`, `detect_outliers`, and `forecast_completion` depend on this
data being present. If these tools return empty results or "project not found", call
`load_project(project_id="[PROJECT_ID]", file_path="/path/to/schedule.mpp")` first, then
re-run the analysis.

**Combine with a role system prompt for calibrated output.**
Each prompt produces better-calibrated results when paired with a system prompt that
establishes the reviewer's role and standards. For gate readiness analysis, use
`docs/prompts/ipa-gate-review-methodology.md`. For benefits reviews, a Green Book
reviewer persona prompt will produce output that uses the correct HMT language and
applies the right tests.

**For portfolio analysis, run across multiple project IDs and use `compare_project_health`.**
To analyse a portfolio rather than a single project, run the relevant research prompt
for each project ID in turn, then call:
`compare_project_health(project_ids=["[ID_1]", "[ID_2]", "[ID_3]"])`
to get a cross-portfolio comparison. The `summarise_project_health` tool can then
produce a consolidated portfolio narrative. This approach works well for PIR panels,
investment committees, and departmental portfolio reviews.

**If tools return "project not found", use `load_project` first.**
The PDA Platform stores project data in a local SQLite store. If a project has not been
loaded in the current session — or if the store has been reset — tools that read from the
store will return a not-found error. Resolve this by calling
`load_project(file_path="/absolute/path/to/your/schedule-file")` before running the
research prompt. The `project_id` returned by `load_project` is the one to use in
subsequent calls.

**Supply real data for the most useful output.**
These prompts are most valuable when run against actual project files — an MPP export,
a CSV task list, a risk register JSON, or structured data ingested via the `ingest_*`
tools. When run against minimal or synthetic data, Claude will produce the correct
structure but will flag evidence gaps rather than speculate — which is the correct
behaviour, but limits the depth of the analysis. The more complete the input data, the
fewer evidence gaps will appear in the output.
