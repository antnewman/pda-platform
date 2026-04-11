# Risk Management — A Guide for Project Delivery Professionals

This guide explains the risk management capabilities available in the PDA
Platform. No technical background is needed.

---

## What this module does

Every project carries risk. The question is not whether risks exist but whether
they are being tracked rigorously enough to act on them in time. The IPA
consistently identifies inadequate risk management as a primary cause of
programme failure — not the risks themselves, but the failure to spot when they
are escalating and to maintain mitigations that actually work.

The `pm-risk` module provides a structured, persistent risk register aligned
to the IPA risk framework and the Cabinet Office Management of Risk (MoR)
guidance. It captures risk metadata, likelihood and impact scores, mitigation
plans, and the history of how scores have changed across review cycles. This
history is what distinguishes the module from a spreadsheet: it enables velocity
analysis — detecting not just how high a risk scores today, but how fast that
score is rising.

Beyond individual project tracking, the module supports portfolio-level
aggregation, allowing Programme Directors and SROs to see the risk picture
across multiple projects simultaneously. It also provides a stale register
detector that flags when a risk register has not been meaningfully updated —
which is often the earliest visible sign that governance has become a
box-ticking exercise rather than active management.

---

## When to use it

- When you need to log a new risk identified in a project board or assurance
  review and want it recorded with full MoR-compliant metadata.
- When preparing for an IPA Gateway Review and need a structured, auditable
  risk register rather than a spreadsheet.
- When you suspect the risk picture is worsening but cannot point to specific
  evidence — velocity analysis makes the trend visible.
- When preparing a brief for a Senior Responsible Owner or Investment Committee
  and need a heat map of the current risk landscape.
- When reviewing a supplier's risk register and want to test whether scores
  have actually changed across review cycles or are simply being restated.
- When managing a portfolio and need to surface which projects carry the most
  critical or fastest-moving risks.
- When conducting a lessons-learned exercise and want to trace how a risk
  progressed from identification to materialisation.

---

## Risk scoring framework

The module uses a standard likelihood-impact matrix aligned to IPA and MoR
practice.

### Likelihood scale

| Score | Label | Plain English |
|-------|-------|---------------|
| 1 | Rare | May occur in exceptional circumstances only |
| 2 | Unlikely | Could occur but not expected |
| 3 | Possible | Might occur at some point |
| 4 | Likely | Will probably occur in most circumstances |
| 5 | Almost Certain | Expected to occur |

### Impact scale

| Score | Label | Plain English |
|-------|-------|---------------|
| 1 | Negligible | Minimal effect; contained within normal tolerances |
| 2 | Minor | Noticeable effect; manageable within project resources |
| 3 | Moderate | Significant effect; requires escalation or replanning |
| 4 | Major | Serious effect; threatens delivery of key objectives |
| 5 | Catastrophic | Project-threatening; may require ministerial involvement |

### Risk score and verbal rating

Risk score = likelihood × impact. Scores map to verbal ratings as follows:

| Score Range | Verbal Rating |
|-------------|---------------|
| 1–6 | LOW |
| 7–12 | MEDIUM |
| 13–19 | HIGH |
| 20–25 | CRITICAL |

### Risk categories

| Category | When to use it |
|----------|----------------|
| DELIVERY | Threats to the project's outputs, milestones, or critical path |
| FINANCIAL | Budget overruns, funding gaps, cost volatility |
| STRATEGIC | Alignment with policy direction, ministerial priorities, or business case objectives |
| LEGAL | Legislative compliance, procurement rules, contractual obligations |
| REPUTATIONAL | Public perception, media exposure, parliamentary scrutiny |
| TECHNICAL | Technology maturity, integration complexity, data quality |
| RESOURCE | Staffing capacity, key-person dependencies, skills shortages |

---

## Tools

### ingest_risk

Records a new risk in the register. This is your primary data entry tool.
Provide the project ID, a title, description, category, likelihood score,
impact score, and risk owner. The module calculates the risk score and verbal
rating automatically.

**Key parameters:** `project_id`, `title`, `description`, `category`,
`likelihood` (1–5), `impact` (1–5), `risk_owner`, `proximity` (how soon the
risk could materialise, in days).

**When to use it:** Whenever a new risk is identified — in a project board,
a supplier review, a team retrospective, or an IPA review. Log it immediately
rather than accumulating risks in meeting notes.

---

### update_risk_status

Updates the status, likelihood, impact, or description of an existing risk.
Each call creates a new record in the audit history, preserving the previous
values. This history is what enables velocity analysis.

**Key parameters:** `risk_id`, `likelihood`, `impact`, `status`
(`OPEN`, `CLOSED`, `TRANSFERRED`, `ACCEPTED`), `review_notes`.

**When to use it:** After each risk review cycle — typically monthly or
fortnightly. Do not simply re-enter unchanged scores; if a score has not
changed, record it with a note confirming it was reviewed and deemed unchanged.
This distinguishes active monitoring from neglect.

---

### get_risk_register

Returns the full risk register for a project, with current scores, statuses,
categories, and owners. Supports filtering by category, status, or minimum
score threshold.

**Key parameters:** `project_id`, optional filters for `category`, `status`,
`min_score`.

**When to use it:** Before any governance meeting, board report, or assurance
review. Use the score filter to surface only HIGH and CRITICAL risks for
executive audiences.

---

### get_risk_heat_map

Returns a heat map of risks plotted by likelihood and impact. The heat map
groups risks into the four verbal rating bands and shows which quadrant of
the likelihood-impact matrix is most densely populated.

**Key parameters:** `project_id`, optional `category` filter.

**When to use it:** For visual communication with SROs, Investment Committees,
or governance boards. The heat map makes the overall risk posture legible at a
glance and supports the narrative in a briefing note.

---

### ingest_mitigation

Records a mitigation action against a specific risk. Each mitigation has a
title, description, owner, due date, and an initial status of PLANNED.

**Key parameters:** `risk_id`, `title`, `description`, `owner`, `due_date`.

**When to use it:** Immediately after logging or reviewing a risk. A risk
without a recorded mitigation is a risk without an owner. The stale register
detector specifically flags high-scoring risks that have no active mitigation.

---

### get_mitigation_progress

Returns all mitigations for a project, grouped by status, with overdue
mitigations highlighted. Supports filtering by risk ID or status.

**Key parameters:** `project_id`, optional `risk_id`, optional `status` filter.

**Mitigation statuses:**

| Status | What it means |
|--------|---------------|
| PLANNED | Mitigation agreed but not yet started |
| IN_PROGRESS | Mitigation actively being delivered |
| COMPLETED | Mitigation delivered; verify whether the risk score has reduced |
| CANCELLED | Mitigation dropped; a replacement should be recorded if the risk remains open |

**When to use it:** In monthly risk reviews to confirm that mitigation actions
are progressing on schedule. Overdue mitigations in IN_PROGRESS status are an
early warning of delivery pressure elsewhere in the project.

---

### get_portfolio_risks

Aggregates risks across all projects in a portfolio. Returns the count and
distribution of risks by category and verbal rating, and surfaces the highest-
scoring individual risks across all projects.

**Key parameters:** `portfolio_id`, optional threshold filters.

**When to use it:** For Programme Directors, SROs with cross-project
responsibility, or IPA analysts reviewing a portfolio. Use before a portfolio
board to identify which projects are carrying the most acute risk.

---

### get_risk_velocity

Analyses the rate of change of risk scores across review cycles. For each
risk, it computes the direction and magnitude of score movement — whether
the risk is stable, escalating, or de-escalating — and flags risks whose
scores are accelerating.

**Key parameters:** `project_id`, `lookback_cycles` (how many review cycles
to analyse, default 3).

**When to use it:** Before any escalation decision or gate review where you
need to distinguish between risks that are high and stable versus risks that
are high and worsening. A risk scored at 16 that has moved from 9 to 12 to 16
over three cycles demands more urgent attention than a risk scored at 16 that
has been static for six months.

Velocity analysis is particularly valuable when preparing evidence for an
IPA Red review or when briefing a minister on programme risk.

---

### detect_stale_risks

Analyses the risk register and returns a staleness score from 0 to 100, where
0 is fully current and 100 indicates a severely neglected register. The
analysis flags:

- Risks not updated within a configurable number of days (default: 30 days).
- Risks whose scores have not changed across three or more consecutive review
  cycles without a recorded review note explaining why.
- High-scoring risks (HIGH or CRITICAL) with no active mitigation in
  IN_PROGRESS or COMPLETED status.

**Key parameters:** `project_id`, `staleness_threshold_days` (default 30).

**When to use it:** When preparing for an assurance review and wanting to
pre-empt scrutiny of the risk register's integrity. Also use it to challenge
a supplier or delivery partner whose risk register looks suspiciously clean —
unchanged scores across multiple reporting periods are a warning sign, not
reassurance.

---

## Common workflows

### Workflow 1: Setting up a risk register at project initiation

1. Use `ingest_risk` to log all risks identified during inception — typically
   drawn from the OBC risk appendix, lessons learned from similar programmes,
   and the project's dependency and assumptions log.
2. For each HIGH or CRITICAL risk, use `ingest_mitigation` to record at least
   one mitigation action with a named owner and due date.
3. Use `get_risk_heat_map` to produce a visual summary for the SRO's initial
   briefing.
4. Schedule a recurring monthly cycle: `update_risk_status` after each review,
   `get_risk_velocity` before each board meeting.

### Workflow 2: Monthly risk review cycle

1. Open `get_risk_register` with a filter for OPEN risks to see the current
   state of the register.
2. After discussing each risk in the risk review meeting, use
   `update_risk_status` to record updated scores and review notes.
3. Run `get_mitigation_progress` to confirm that IN_PROGRESS mitigations are
   on track and escalate any that are overdue.
4. Run `get_risk_velocity` to check whether any risks have accelerated since
   the previous cycle.
5. Use `detect_stale_risks` to confirm the register is fully current before
   the scores go into the monthly report.

### Workflow 3: Pre-gate or pre-IPA assurance preparation

1. Run `detect_stale_risks` to identify any gaps that an IPA reviewer would
   flag — missing mitigations, unchanged scores, overdue reviews.
2. Address the gaps: update scores where reviewed, add mitigations where
   missing, close risks that have materialised or lapsed.
3. Run `get_risk_velocity` to prepare a narrative on risk trajectory — which
   risks are improving, which are worsening, and why.
4. Use `get_risk_heat_map` to produce a heat map for the assurance pack.
5. For portfolio-level reviews, run `get_portfolio_risks` to aggregate the
   picture across all projects under scrutiny.

---

## Worked examples

### Example 1: Logging a supplier dependency risk with a mitigation

**Scenario.** Your project depends on a key supplier delivering a critical
integration component by Month 6. The supplier has recently flagged resourcing
problems. You want to log this formally and record the mitigation.

**What to do.** Ask Claude: "Log a new risk for Project ATLAS. The supplier
Apex Systems is at risk of missing the Month 6 integration delivery due to
staff attrition. Category is DELIVERY. Likelihood 4, Impact 4. Owner is the
Commercial Manager. Proximity is 90 days. Then log a mitigation: convene a
weekly supplier assurance call with Apex and review their resource plan by
end of this month."

**What Claude does.** Calls `ingest_risk` to record the risk with score 16
(HIGH), then calls `ingest_mitigation` to record the weekly supplier assurance
call with the due date provided.

**How to interpret the output.** The risk is logged at HIGH with a score of 16.
The mitigation is in PLANNED status pending the first assurance call. You now
have an auditable record that the risk was identified and responded to on this
date. At next month's review, update the mitigation to IN_PROGRESS and the
risk score based on what the supplier assurance calls have revealed.

---

### Example 2: Running velocity analysis to spot an accelerating risk

**Scenario.** Your programme has been running for eight months. The risk
register shows several HIGH risks, but the board is asking whether things are
getting better or worse overall. You want to distinguish between risks that are
high but stable and risks that are actively escalating.

**What to do.** Ask Claude: "Run risk velocity analysis for Programme DELTA
over the last four review cycles."

**What Claude does.** Calls `get_risk_velocity` with `lookback_cycles=4`. It
retrieves the score history for all open risks and computes the rate of change.
It returns a ranked list showing each risk's trajectory: stable, improving, or
accelerating.

**How to interpret the output.** If a RESOURCE risk that scored 9, 10, 12, 15
over four cycles appears at the top of the accelerating list, that risk demands
immediate attention even though its current score of 15 is not the highest
on the register. The rate of change is telling you something the static score
conceals: something is causing this risk to worsen each month. Investigate the
cause before the score reaches CRITICAL. This is the distinction the IPA
draws between risks that are "known and managed" and risks that are "known but
deteriorating" — the latter require a different governance response.

---

### Example 3: Using detect_stale_risks to challenge a governance board

**Scenario.** You are an SRO preparing for an IPA Amber review. The delivery
team has submitted a risk register showing 12 risks, all marked as reviewed
last month, but several scores look unchanged from the previous quarter. You
want to test the register's integrity before the IPA team does.

**What to do.** Ask Claude: "Run stale risk detection for Project MERIDIAN.
Flag anything not updated in the last 28 days and any high-scoring risks
without active mitigations."

**What Claude does.** Calls `detect_stale_risks` with a 28-day threshold. It
analyses the update timestamps, score change history, and mitigation statuses
across all 12 risks.

**How to interpret the output.** Suppose the staleness score comes back at 64.
The report identifies three risks scored HIGH that have had identical likelihood
and impact scores for four consecutive cycles, with no review notes recorded,
and one CRITICAL risk with only a PLANNED mitigation that is now three months
overdue. This is the evidence you need to go back to the delivery team before
the IPA review and require them to demonstrate that risks are genuinely being
managed. A staleness score above 50 in the month before a Gateway Review is
a serious governance concern.

---

## Limitations and considerations

- Velocity analysis requires at least three review cycles of score history to
  produce meaningful results. On new projects, establish the register early
  and review consistently.
- The staleness detector flags risks whose scores have not changed, but some
  risks genuinely do not change. Always accompany unchanged scores with a
  brief review note confirming they were discussed and reassessed.
- Risk scores are assessments of probability and severity, not predictions.
  The model assumes the assessors are applying the likelihood and impact
  definitions consistently. Calibration discussions at the start of a project
  improve the quality of the data.
- The module does not integrate live supplier or financial feeds. Scores
  reflect the judgment of whoever recorded them.
- Portfolio aggregation assumes all constituent projects use the same scoring
  framework and category taxonomy. Mixed conventions will distort portfolio
  comparisons.

---

## Related modules

- **pm-schedule** — Schedule slippage often triggers or amplifies DELIVERY and
  RESOURCE risks. Use schedule analysis to validate proximity estimates.
- **pm-financial** — Cost overruns frequently appear first as FINANCIAL risks.
  Correlate risk scores with cost performance data from pm-financial.
- **pm-change** — Uncontrolled change is a major source of new risks. High
  change pressure from `analyse_change_pressure` should prompt a fresh risk
  review.
- **pm-resource** — RESOURCE risks identified here can be investigated in
  depth using `detect_resource_conflicts` and `get_critical_resources`.
- **pm-brm** — Strategic risks often threaten benefit realisation. Cross-
  reference STRATEGIC risk scores with the benefits health score.
