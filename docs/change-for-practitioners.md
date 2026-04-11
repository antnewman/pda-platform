# Change Control — A Guide for Project Delivery Professionals

This guide explains the change control capabilities available in the PDA
Platform. No technical background is needed.

---

## What this module does

Uncontrolled scope change is one of the most reliably documented failure
patterns in UK government project delivery. The IPA's project failure analysis
consistently identifies "requirements defined too late" as a primary cause of
cost overruns and schedule slippage. The mechanism is straightforward: when
requirements continue to evolve after a project has been baselined, every
change consumes time and money that was not planned for, pushes the critical
path out, and introduces integration complexity that compounds over time. By
the time the cumulative impact becomes visible, recovery is expensive and
options are limited.

The `pm-change` module provides a structured, auditable change control log
that captures every change request with its type, impact assessment, and
approval status. It tracks each change through the governance lifecycle from
identification to implementation, and computes the aggregate impact of
approved changes on cost, schedule, and scope. Critically, it provides
change pressure analysis — a diagnostic that detects when the volume or rate
of change requests indicates that the project's scope is not stable, which
is itself a leading indicator of delivery risk independent of any individual
change's impact.

The module is designed for use by Project Managers, Change Authorities, and
SROs who need a reliable record of what has changed, when it was approved,
by whom, and at what cost — both for day-to-day governance and for the
retrospective analysis that IPA reviews and public accounts scrutiny require.

---

## When to use it

- When a change request has been raised and needs to be formally recorded
  before it is assessed and routed for approval.
- When tracking a change through the approvals process and needing to
  update its status at each stage.
- When preparing the change section of a Gateway Review pack or SRO
  quarterly report and needing a structured log rather than a spreadsheet.
- When cost variance has appeared and you need to explain to the SRO or
  Investment Committee how much of it is attributable to approved scope
  changes versus cost inefficiency.
- When you suspect the project is experiencing scope instability and want
  to test that hypothesis with data before raising it as a governance concern.
- When a supplier is claiming additional cost and you need to check whether
  an approved change request supports the claim.
- Before a replan, to confirm that all approved changes have been formally
  incorporated and their cost and schedule impacts are reflected in the
  updated baseline.

---

## Change request types

| Type | What it covers |
|------|----------------|
| SCOPE | Changes to what the project will deliver — adding, removing, or modifying outputs |
| COST | Changes to the approved budget or contingency draw-down |
| SCHEDULE | Changes to key milestones, phase boundaries, or the overall project end date |
| RISK | Changes to risk treatments, contingency plans, or risk transfer arrangements |
| GOVERNANCE | Changes to the project's accountability structure, delegated authorities, or reporting arrangements |

---

## Change request lifecycle

| Status | What it means |
|--------|---------------|
| PENDING | Change request logged and under assessment; not yet submitted to the Change Authority |
| APPROVED | Change Authority has approved the change; implementation authorised |
| REJECTED | Change Authority has rejected the change; project continues on existing baseline |
| IMPLEMENTED | The approved change has been fully delivered and incorporated into the project baseline |

---

## Tools

### log_change_request

Records a new change request in the change log. This should be done as soon
as a change is identified — before assessment, before approval, and before
any work is done on implementing it.

**Key parameters:** `project_id`, `title`, `description`, `change_type`
(`SCOPE`, `COST`, `SCHEDULE`, `RISK`, `GOVERNANCE`), `raised_by`,
`raised_date`, `cost_impact` (estimated £ cost of implementing the change,
can be positive or negative), `schedule_impact_days` (estimated number of
days added to or removed from the schedule), `scope_impact` (plain-English
description of what changes in the project's deliverables), `priority`
(`LOW`, `MEDIUM`, `HIGH`, `URGENT`).

**When to use it:** The moment a change is identified, regardless of whether
it has been assessed or is expected to be approved. An incomplete change log
— one that only records changes after approval — is not a change log; it is
an approval record. The log should capture all requests including those that
are ultimately rejected, because the rejected changes are as informative as
the approved ones when assessing scope stability.

---

### update_change_status

Moves a change request to a new status and records who made the decision,
when, and with what rationale. Each status transition creates an audit entry
in the change history.

**Key parameters:** `change_id`, `new_status` (`PENDING`, `APPROVED`,
`REJECTED`, `IMPLEMENTED`), `decision_maker`, `decision_date`,
`decision_rationale`, `revised_cost_impact` (if the assessed cost differs
from the initial estimate), `revised_schedule_impact_days`.

**When to use it:** At each stage of the change governance process: when the
Change Authority convenes to assess a PENDING request (move to APPROVED or
REJECTED), and when the delivery team confirms a change has been fully
implemented (move APPROVED to IMPLEMENTED). Recording the decision-maker and
rationale is important for retrospective audit. An approved change with no
recorded rationale is a governance gap that IPA reviewers and PAC committees
will flag.

---

### get_change_log

Returns the full change log for a project, with filtering options. The log
shows each change request's type, status, cost impact, schedule impact, and
current position in the lifecycle.

**Key parameters:** `project_id`, optional filters for `change_type`,
`status`, `from_date`, `to_date`, `min_cost_impact`.

**When to use it:** Before any governance meeting where changes are discussed,
when preparing the changes section of a board report, or when a supplier
raises a cost claim and you need to verify whether it is supported by an
approved change request. The `status` filter is particularly useful:
filtering for APPROVED changes gives you the formally authorised scope of
the project; filtering for PENDING gives you the queue of unresolved
decisions.

---

### get_change_impact_summary

Returns the aggregate impact of all approved changes on cost, schedule, and
scope. This is the tool for answering the question "how much of our cost
variance is explained by approved scope changes?"

**Key parameters:** `project_id`, optional `from_date` and `to_date` to
restrict to changes approved within a specific period.

**When to use it:** When explaining cost or schedule variance to the SRO,
Investment Committee, or IPA reviewer. The summary separates the variance
that is attributable to approved and understood changes from the residual
variance that requires a different explanation — cost inefficiency, risk
materialisation, or unrealistic baseline assumptions. This is a standard
requirement in Gateway Review packs and HMT spending review submissions.

---

### analyse_change_pressure

Analyses the volume, rate, and pattern of change requests over time to
detect scope instability. It computes a change pressure score and identifies
whether the rate of change is increasing, stable, or declining. It also
identifies patterns associated with specific change types — for example,
a sustained flow of SCOPE changes late in the delivery lifecycle is a
strong indicator that requirements were not adequately defined at project
initiation.

**Key parameters:** `project_id`, `lookback_days` (how many days of change
history to analyse, default 90), `include_rejected` (whether to include
rejected changes in the pressure calculation, default true — rejected changes
still indicate scope instability even if not approved).

**When to use it:** Before a Gate Review or IPA assurance visit, when the
project board is concerned about scope creep, and proactively at regular
intervals during delivery. The inclusion of rejected changes is important:
a project that is receiving many change requests but rejecting most of them
is still experiencing high scope pressure — the rejected changes represent
scope that stakeholders want but cannot get, which typically manifests as
dissatisfaction, workarounds, or escalation to ministerial level.

---

## Common workflows

### Workflow 1: Logging a change and routing it through governance

1. As soon as a change is raised (by the delivery team, a stakeholder, the
   sponsoring department, or a supplier), use `log_change_request` to record
   it with all available metadata including the initial cost and schedule
   impact estimates.
2. The change sits in PENDING status until the Change Authority reviews it.
3. When the Change Authority meets, use `update_change_status` to record
   the decision: APPROVED or REJECTED, with the decision-maker, date, and
   rationale. If the assessed impact differs from the initial estimate,
   record the revised figures.
4. After implementation is confirmed, use `update_change_status` again to
   move the change to IMPLEMENTED.
5. After approval, update the cost forecast in `pm-financial` using
   `log_cost_forecast` to reflect the approved cost impact, referencing
   the change ID in the rationale.

### Workflow 2: Preparing a change impact summary for a gate review

1. Use `get_change_log` filtered for APPROVED and IMPLEMENTED changes to
   see the full scope of authorised changes since project baseline.
2. Use `get_change_impact_summary` to produce the aggregate cost and
   schedule impact of all approved changes.
3. Cross-reference with the cost performance data from `pm-financial` to
   show what proportion of the cost variance is explained by approved
   changes and what requires separate explanation.
4. Run `analyse_change_pressure` to show the Gateway Review team whether
   scope instability is a current concern or has been resolved.
5. Use the outputs to structure the narrative in the change section of
   the Gateway pack.

### Workflow 3: Monitoring change pressure during delivery

1. At each monthly project board, run `analyse_change_pressure` to check
   whether the rate of change requests is increasing, stable, or declining.
2. If pressure is increasing, look at the `change_type` breakdown: a spike
   in SCOPE changes suggests requirements drift; a spike in COST changes
   may indicate cost pressures not yet visible in actuals; a spike in
   SCHEDULE changes suggests planning assumptions are not holding.
3. Use `get_change_log` filtered by recent dates to review the specific
   changes driving the pressure.
4. If the analysis indicates high scope instability, escalate to the SRO
   with the quantified evidence: number of change requests, rate of increase,
   proportion affecting cost and schedule.

---

## Worked examples

### Example 1: Logging a scope change and routing it through governance

**Scenario.** The sponsoring department has asked Project SOLSTICE to add a
new reporting dashboard to the digital output originally specified. The
delivery team estimates this will cost £180,000 and add three weeks to the
delivery schedule. The request has been raised by the Deputy Director of
Digital.

**What to do.** Ask Claude: "Log a change request for Project SOLSTICE.
Title: Additional reporting dashboard. Type: SCOPE. Raised by: Deputy
Director of Digital. Cost impact: £180,000. Schedule impact: 21 days.
Scope impact: Addition of a new stakeholder reporting dashboard to the
digital platform, not included in the original FBC specification. Priority:
MEDIUM."

**What Claude does.** Calls `log_change_request` with the parameters
provided. The change is logged in PENDING status.

**How to interpret the output.** The change is now formally recorded with
a timestamp, a unique change ID, and all impact assessments. When the
Change Authority meets to review it, call `update_change_status` with the
decision. If approved: the cost forecast in pm-financial should be updated
using `log_cost_forecast` referencing this change ID. If rejected: the
change remains in the log as a rejected request — useful evidence when the
Deputy Director raises the same request again at a later date, or when the
absence of the dashboard becomes a point of stakeholder dissatisfaction.

---

### Example 2: Running change pressure analysis before a gate review

**Scenario.** Project VANGUARD is approaching Gate 4. In the past three
months, the project board has processed 14 change requests. The SRO wants
to know whether this level of change activity is a concern before the IPA
review team arrives.

**What to do.** Ask Claude: "Run change pressure analysis for Project
VANGUARD over the last 90 days. Include rejected changes in the analysis."

**What Claude does.** Calls `analyse_change_pressure` with a 90-day lookback
and `include_rejected=true`. It computes the volume, rate, type distribution,
and trend of change requests.

**How to interpret the output.** If the output shows that 14 changes in 90
days represents a significant increase from the 4 changes logged in the
preceding 90-day period, and that 10 of the 14 are SCOPE type, this is
evidence of active scope instability — a pattern the IPA specifically
associates with requirements defined too late. The SRO should use this
analysis to brief the review team proactively: here is the evidence of
scope pressure, here is what is driving it (ideally referenced to specific
policy changes or stakeholder decisions), and here is what the project is
doing to stabilise requirements. An SRO who presents this analysis
unprompted demonstrates governance maturity; an SRO who is surprised by
it during the review demonstrates the opposite.

---

### Example 3: Using the change log to explain cost variance to the SRO

**Scenario.** Project HELIOS is projecting a £2.4 million cost overrun
against the approved budget. The SRO has asked for an explanation before
the next Investment Committee. The finance team believes most of the
overrun is attributable to approved scope changes, but the details are
spread across multiple spreadsheets.

**What to do.** Ask Claude: "Show me the change impact summary for Project
HELIOS. Then show me the full change log filtered for approved changes, with
cost and schedule impacts."

**What Claude does.** Calls `get_change_impact_summary` to compute the
aggregate cost impact of all approved changes, then calls `get_change_log`
filtered for APPROVED status to show the individual change records.

**How to interpret the output.** If the change impact summary shows that
approved changes account for £2.1 million of the £2.4 million projected
overrun, the Investment Committee narrative becomes clear: £2.1 million is
the direct and authorised consequence of ten scope changes approved by the
Change Authority over the past 12 months, and the remaining £0.3 million
represents residual cost variance from efficiency shortfalls and risk
materialisation. The individual change log provides the detail behind
each line. This is a qualitatively different briefing from "we have a
£2.4 million overrun" — it shows the overrun was known, authorised, and
traceable. The absence of this analysis is what causes Investment Committees
to question whether the project team has control of its costs.

---

## Limitations and considerations

- The module records change requests as provided. It does not independently
  validate cost or schedule impact estimates. The quality of the impact
  analysis depends on the rigour applied when the change is logged.
- Change pressure analysis measures the volume and rate of requests. It does
  not distinguish between changes that are genuinely necessary (policy shifts,
  legislation, security requirements) and changes that reflect poor upfront
  requirements definition. That distinction requires human interpretation of
  the change descriptions.
- The module tracks formal change requests through the governance process.
  Informal scope additions — work that is simply added without a change
  request being raised — will not appear in the change log. The completeness
  of the log depends on the discipline of the project team in logging all
  changes, not just the large ones.
- Aggregate impact summaries assume that the cost and schedule impacts
  recorded on individual change requests are accurate and non-overlapping.
  If changes interact (one change enabling another, or two changes affecting
  the same deliverable), the aggregate impact may not be a simple sum.
- The change log does not replace the project's formal Change Management
  Plan. It provides data; governance process and decision authority structures
  must be defined in the project's own documentation.

---

## Related modules

- **pm-financial** — Approved scope changes should be reflected in an updated
  cost forecast. Use `log_cost_forecast` in pm-financial after each approved
  change, referencing the change ID in the rationale.
- **pm-schedule** — SCHEDULE type changes should be cross-referenced with
  the schedule analysis in pm-schedule to confirm that the stated schedule
  impact is consistent with the critical path.
- **pm-risk** — Unresolved change pressure is a risk in its own right.
  If `analyse_change_pressure` returns a high pressure score, log a DELIVERY
  or STRATEGIC risk in pm-risk to ensure it is tracked and mitigated.
- **pm-resource** — SCOPE changes frequently increase resource demand. After
  a significant scope change is approved, run resource conflict detection
  in pm-resource to check whether the additional work can be absorbed.
- **pm-brm** — Scope changes can affect which benefits the project will
  deliver and by when. Material scope changes should trigger a review of
  the benefits dependency network in pm-brm to confirm that the business
  case remains valid.
