# Financial Management — A Guide for Project Delivery Professionals

This guide explains the financial management capabilities available in the PDA
Platform. No technical background is needed.

---

## What this module does

Cost overruns are among the most consistently documented failure patterns
across UK government projects. The IPA's annual data shows that the gap between
approved budgets and out-turn costs, even at Full Business Case stage, remains
substantial across the portfolio. The causes are varied — optimism bias,
inadequate cost modelling, scope creep, and poor tracking of actuals against
baseline — but the common thread is that the deterioration was visible in the
data before it became a crisis. Projects that track actuals rigorously against
a structured baseline catch cost problems earlier and have more options for
recovery.

The `pm-financial` module provides structured tracking of your project's
financial position against an approved baseline, aligned to IPA and HM Treasury
reporting requirements. It records the Budget at Completion, actual spend by
period, and Estimate at Completion updates with rationale. From these inputs it
computes the standard cost performance metrics — Cost Performance Index,
Estimate at Completion variance, and spend trajectory — that appear in IPA
reviews and HMT spending round submissions.

The module is designed to complement rather than replace your finance team's
systems. It provides a practitioner-facing view of financial health that can
be queried conversationally, surfacing the metrics and narratives needed for
governance reporting without requiring access to complex financial systems.

---

## When to use it

- When setting up a project at gate approval and wanting to record the
  approved budget baseline for ongoing tracking.
- When recording monthly or quarterly actual spend against the baseline and
  checking whether cost performance is within tolerance.
- When a scope change, procurement event, or external shock has altered the
  expected final cost and you need to update the Estimate at Completion with
  a documented rationale.
- When preparing a financial section for an IPA Gateway pack, SRO quarterly
  report, or HMT spending return.
- When the project's cost trajectory suggests it may breach the approved
  budget and you need to quantify the exposure before escalating.
- When conducting a mid-year review and needing to compare planned versus
  actual spend profile to identify periods of underspend or overspend.

---

## Key financial concepts

### Budget at Completion (BAC)

The total approved budget for the project, as recorded in the approved
business case or most recent funding approval. This is the baseline against
which all cost performance is measured.

### Estimate at Completion (EAC)

The current best estimate of the total cost the project will incur by
completion. The EAC changes over time as actuals are recorded and forecasts
are revised. A rising EAC against a fixed BAC signals cost deterioration.

### Cost Performance Index (CPI)

CPI measures cost efficiency: the ratio of earned value to actual cost.
A CPI above 1.0 means the project is delivering more value per pound spent
than planned. A CPI below 1.0 means it is spending more than planned for the
work completed. CPI trends over time are more informative than point-in-time
readings.

| CPI Range | Interpretation |
|-----------|----------------|
| Above 1.05 | Ahead of plan — verify whether baseline is realistic |
| 0.95–1.05 | Within tolerance |
| 0.90–0.94 | Watch — approaching tolerance boundary |
| 0.80–0.89 | Concern — formal replan or recovery action likely needed |
| Below 0.80 | Critical — probable breach of approved budget |

### Variance at Completion (VAC)

VAC = BAC minus EAC. A negative VAC means the project is forecast to overspend.
This is the number that appears in escalation reports and spending reviews.

---

## Tools

### set_financial_baseline

Records the approved Budget at Completion and planned spend profile for a
project. This is a one-time setup action at gate approval, though it can be
updated if a formal re-baseline is approved.

**Key parameters:** `project_id`, `bac` (total budget in £), `baseline_date`
(date of approval), `spend_profile` (planned spend by period, typically by
financial year quarter), `approval_reference` (business case or HMT approval
reference).

**When to use it:** At Gate 2 or Gate 3 when the project receives formal
budget approval. The spend profile entered here becomes the baseline against
which `get_spend_profile` compares actuals. A well-structured baseline — with
spend broken down by period rather than entered as a single lump sum — makes
cost tracking significantly more useful.

---

### log_financial_actuals

Records actual spend for a specific period. Each call appends a period record
to the actuals history without overwriting previous entries.

**Key parameters:** `project_id`, `period` (e.g., "2024-Q3"), `actual_spend`
(£ for the period), `spend_category` (optional: capital, resource, non-pay),
`notes`.

**When to use it:** Monthly or quarterly, immediately after the finance team
confirms the period's actual spend figures. Consistent, timely recording of
actuals is the foundation of useful cost performance analysis. Actuals recorded
late or in bulk at year-end reduce the value of trend analysis significantly.

---

### get_cost_performance

Returns the project's current cost performance metrics: CPI, EAC, VAC, and
cost trajectory. If Earned Value data is available from the `pm-ev` module,
it incorporates SPI as well.

**Key parameters:** `project_id`, optional `as_of_date` to view performance
at a historical point.

**When to use it:** Before any governance meeting, gate review, or financial
reporting submission. The CPI trend — not just the current value — is the
most important output. A CPI declining from 0.97 to 0.94 to 0.91 across three
periods tells a different story from a CPI that has been stable at 0.93 for
six months.

---

### log_cost_forecast

Records an updated Estimate at Completion with the rationale for the change.
This creates an auditable forecast history showing how and why the expected
final cost has evolved.

**Key parameters:** `project_id`, `eac` (updated Estimate at Completion in £),
`forecast_date`, `rationale` (plain-English explanation of why the EAC has
changed), `change_driver` (optional: `SCOPE_CHANGE`, `RISK_MATERIALISATION`,
`INFLATION`, `EFFICIENCY`, `REPLAN`, `OTHER`).

**When to use it:** Whenever there is a material change to the cost forecast —
after a scope change is approved, after a significant risk materialises, after
a contract is let at a different value than estimated, or at each quarterly
review cycle. Recording the rationale at the time of the change is essential:
it provides the narrative for cost variance explanations in assurance reviews
and prevents the "we can't remember why the forecast changed" problem that
commonly arises when projects are scrutinised months later.

---

### get_spend_profile

Returns a period-by-period comparison of planned versus actual spend, with
cumulative variance at each point. Identifies periods of underspend or
overspend against the baseline profile.

**Key parameters:** `project_id`, optional `from_period` and `to_period`
to restrict the view.

**When to use it:** In monthly financial reviews to check whether spend is
tracking to the planned profile. Persistent underspend against profile is
often as significant a concern as overspend: it frequently indicates that
delivery activity has slipped, which will either create future overspend
pressure as work compresses, or indicate that planned outputs will not be
delivered on time. Both warrant investigation.

---

## Common workflows

### Workflow 1: Setting up financial tracking at gate approval

1. After the Investment Committee or HMT has approved the Full Business Case,
   use `set_financial_baseline` to record the approved BAC and the quarterly
   spend profile from the financial model.
2. Record the approval reference so that all subsequent cost tracking can be
   linked to the approved baseline.
3. Use `get_cost_performance` immediately after setup to confirm the baseline
   is correctly recorded — CPI should show as 1.0 with no actuals yet logged.

### Workflow 2: Monthly financial health check

1. After receiving the period's confirmed actuals from the finance team, use
   `log_financial_actuals` to record the spend.
2. Run `get_cost_performance` to see the updated CPI, EAC, and VAC.
3. Run `get_spend_profile` to check whether the period's spend tracked to
   profile or deviated materially.
4. If the CPI has deteriorated since last month, investigate the cause and
   consider whether a forecast update via `log_cost_forecast` is warranted.
5. Use the CPI trend and VAC figure in the project's monthly report to the
   SRO or Programme Management Office.

### Workflow 3: Updating the forecast after a scope change

1. After a scope change is approved through the change control process
   (see `pm-change`), calculate the cost impact.
2. Use `log_cost_forecast` to record the new EAC with rationale referencing
   the approved change request ID and the cost delta.
3. Run `get_cost_performance` to confirm the updated VAC and check whether
   the project remains within its delegated financial tolerance.
4. If the VAC now shows a projected overspend relative to the approved BAC,
   prepare an escalation to the SRO or Investment Committee. The forecast
   history from `log_cost_forecast` provides the audit trail showing when
   the overspend was identified and why it arose.

---

## Worked examples

### Example 1: Setting up a baseline at Gate 3

**Scenario.** Project ALBION has just received Gate 3 approval with a total
budget of £47.3 million. The approved spend profile is: £4.2m in 2024-Q4,
£11.8m in 2025-Q1, £13.1m in 2025-Q2, £10.4m in 2025-Q3, £7.8m in 2025-Q4.
The business case approval reference is BC-2024-0147.

**What to do.** Ask Claude: "Set the financial baseline for Project ALBION.
BAC is £47.3 million. Baseline date is today. Approval reference BC-2024-0147.
Spend profile: 2024-Q4 £4.2m, 2025-Q1 £11.8m, 2025-Q2 £13.1m, 2025-Q3
£10.4m, 2025-Q4 £7.8m."

**What Claude does.** Calls `set_financial_baseline` with the parameters
provided, stores the baseline with the approval reference and period breakdown.

**How to interpret the output.** The baseline is now set. All subsequent actual
spend logging will be compared against this profile. If the project later
requests a re-baseline — perhaps after a scope change increases the BAC — the
original baseline is preserved in history so reviewers can see the full
evolution of the financial plan.

---

### Example 2: Logging monthly actuals and checking cost performance

**Scenario.** It is the end of 2025-Q1. Finance has confirmed actual spend of
£13.4 million against a planned £11.8 million. You want to understand the cost
performance impact.

**What to do.** Ask Claude: "Log actual spend for Project ALBION, period
2025-Q1: £13.4 million. Then show me the current cost performance."

**What Claude does.** Calls `log_financial_actuals` to record the period spend,
then calls `get_cost_performance` to compute updated metrics.

**How to interpret the output.** The output will show: actual cumulative spend
of £17.6m (£4.2m + £13.4m) against planned £16.0m — an overspend of £1.6m at
this point. CPI will be below 1.0, reflecting the cost efficiency shortfall.
The EAC will be revised upwards from £47.3m. The VAC will show a projected
overspend. The critical question is whether this overspend is due to work
accelerating ahead of schedule (meaning earned value is also up) or due to
genuine cost inefficiency. Use `get_cost_performance` in conjunction with the
`pm-ev` module's SPI to distinguish between the two.

---

### Example 3: Updating a forecast after a scope change

**Scenario.** A scope change has been approved adding £3.2 million of work
to Project ALBION following a policy change from the sponsoring department.
The change control reference is CR-0023.

**What to do.** Ask Claude: "Log a cost forecast update for Project ALBION.
New EAC is £50.5 million. Change driver is SCOPE_CHANGE. Rationale: approved
scope change CR-0023 adds £3.2m of additional integration work following
the department's revised digital strategy. Forecast date today."

**What Claude does.** Calls `log_cost_forecast` with the updated EAC, change
driver, and rationale, appending to the forecast history.

**How to interpret the output.** The forecast history now records that on this
date, the EAC increased by £3.2m, with the approved change request as the
documented cause. The new VAC is £47.3m minus £50.5m = -£3.2m, meaning the
project is forecast to overspend its original approved budget. This is now the
figure that must be reported to the Investment Committee for a formal re-
baseline decision. The audit trail — original BAC, date of change, reference
to the change request, and updated EAC — is complete and defensible under
scrutiny.

---

## Limitations and considerations

- The module records data as provided. The quality of cost performance analysis
  depends entirely on the accuracy and timeliness of the actuals logged. Late
  or estimated actuals reduce the reliability of CPI and EAC calculations.
- CPI calculations assume that the budget baseline accurately reflects the
  work planned. If the original spend profile was poorly modelled — for example,
  heavily back-loaded to pass affordability tests — the CPI will be misleading
  in the early stages of the project.
- The module does not have access to your organisation's financial systems.
  Actuals must be entered manually, drawing on the confirmed figures from your
  finance team.
- EAC computed by the module uses the data you have provided. It does not
  independently validate cost estimates or apply optimism bias correction. That
  analytical judgment remains with the SRO and cost assurance team.
- For full Earned Value analysis including Schedule Performance Index, this
  module should be used in conjunction with `pm-ev`.

---

## Related modules

- **pm-ev** — Earned Value Management provides SPI alongside CPI. Cost
  performance analysis is most powerful when combined with schedule
  performance data.
- **pm-change** — Scope changes are a primary driver of EAC updates. Use
  `get_change_impact_summary` from pm-change to verify the cost impact of
  approved changes before logging a forecast update.
- **pm-risk** — FINANCIAL risks identified in the risk register should be
  cross-referenced with cost performance trends. A deteriorating CPI is
  often the materialisation of a risk that was identified months earlier.
- **pm-schedule** — Spend profile deviations often reflect schedule slippage.
  Persistent underspend against profile warrants investigation using schedule
  analysis tools.
- **pm-brm** — Financial overruns directly affect the cost-benefit ratio
  underpinning the business case. A rising EAC should prompt a review of
  whether the benefits case remains viable.
