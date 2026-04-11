# Earned Value Analysis — A Guide for Practitioners

This guide explains the Earned Value Management (EVM) capabilities available
in the PDA Platform. No technical or financial modelling background is needed.
The module is designed for Project Managers, PMO leads, and Senior Responsible
Owners who need objective cost and schedule performance data for governance
reporting.

---

## What this module does

Self-reported progress is one of the most unreliable inputs in project assurance.
When teams report "80% complete," that figure typically reflects effort spent or
time elapsed — not the value of work that has actually been delivered. A project
can be 80% through its timeline while having delivered only 60% of its planned
outputs, with the remaining 40% still to be built and costs already exceeding
the approved budget.

Earned Value Management addresses this directly. It measures what has actually
been produced (Earned Value) against what was planned to be produced by this
date (Planned Value) and what has actually been spent (Actual Cost). The
resulting ratios — the Schedule Performance Index and Cost Performance Index —
give an objective reading of whether the project is on track that is not
dependent on team self-assessment.

The PDA Platform's EV module computes the full set of earned value metrics
from your project's task schedule data and produces a self-contained HTML
dashboard suitable for board packs and governance submissions.

---

## When to use it

- Monthly project review meetings where you need objective cost and schedule
  performance data, not just a status update.
- When you suspect a project may be further behind or over budget than team
  reporting suggests and you want an independent measure.
- Before a gate review, to establish an objective baseline of delivery
  performance to date.
- When a project's Estimate at Completion (the projected total cost based on
  current performance) is materially different from the approved Budget at
  Completion — triggering a review of the business case.
- When producing a board pack or submission to a spend control panel that
  requires an objective performance measure.

---

## Key EV concepts

Before using these tools, it helps to understand what the metrics mean. These
explanations are written for practitioners, not for EV specialists.

### The three inputs

- **Planned Value (PV)** — also called BCWS (Budgeted Cost of Work Scheduled).
  The value of the work that was supposed to have been completed by today,
  expressed in cost terms. If you planned to complete £500,000 worth of work
  by the end of March, that is your PV for March.
- **Earned Value (EV)** — also called BCWP (Budgeted Cost of Work Performed).
  The budgeted value of the work that has actually been completed by today. If
  you planned those tasks at £500,000 but only £350,000 worth has been done,
  your EV is £350,000.
- **Actual Cost (AC)** — also called ACWP. What you have actually spent to
  deliver the EV so far. If you spent £420,000 to deliver £350,000 of planned
  value, your AC is £420,000.
- **Budget at Completion (BAC)** — the total approved budget for the project.

### Schedule Performance Index (SPI)

SPI = EV divided by PV.

- SPI of 1.0: the project is delivering exactly on schedule.
- SPI above 1.0: the project is ahead of the planned schedule.
- SPI below 1.0: the project is behind. An SPI of 0.90 means you are
  delivering at 90% of the planned rate — roughly ten days behind on a 100-day
  plan.
- SPI below 0.85: a significant concern. At this level of underperformance,
  the project will not recover schedule without a material change to approach
  or resources.

### Cost Performance Index (CPI)

CPI = EV divided by AC.

- CPI of 1.0: the project is spending exactly as planned for the work done.
- CPI above 1.0: the project is under budget for the work completed.
- CPI below 1.0: the project is over budget. A CPI of 0.90 means you are
  spending £1.00 to deliver £0.90 of value.
- CPI below 0.9: the project is on a cost overrun trajectory. Research on
  completed government projects consistently shows that a CPI below 0.9 at
  the midpoint of a project rarely recovers to 1.0 by completion.

### Estimate at Completion (EAC)

EAC is the projected total cost of the project if current performance
continues to completion. It is calculated as BAC divided by CPI.

If your BAC is £10 million and your CPI is 0.82, the EAC is approximately
£12.2 million — £2.2 million above the approved budget. This is a governance
trigger: the business case was approved on the basis of a £10 million cost,
and the current trajectory delivers the same scope for £12.2 million.

### To-Complete Performance Index (TCPI)

TCPI is the cost efficiency that the project team must achieve on all remaining
work to hit the BAC. It is calculated as the remaining budget divided by the
remaining work.

- TCPI of 1.0: the team needs to perform at current efficiency to hit budget.
- TCPI above 1.0: the team must perform better than their current efficiency.
- TCPI above 1.1: the team must perform significantly better than current.
  This is a strong signal that the BAC is no longer achievable without scope
  reduction or budget revision. Governance should be alerted.

### Schedule Variance (SV) and Cost Variance (CV)

- **Schedule Variance (SV)** = EV minus PV. Expressed in monetary terms. A
  negative SV means the project is behind schedule by that value of work.
- **Cost Variance (CV)** = EV minus AC. A negative CV means the project has
  spent more than the budgeted cost of the work performed.

---

## Tools

### compute_ev_metrics

**What it does.** Computes the full set of earned value metrics from the
project's loaded task schedule data: PV, EV, AC, SPI, CPI, SV, CV, EAC, ETC
(Estimate to Complete), VAC (Variance at Completion), and TCPI. Returns all
metrics as structured data with interpretation strings that explain what each
value means in plain English.

**Key parameters.**
- `project_id` (required): the identifier of the project, as returned when the
  project was loaded via the pm-data tools.
- `status_date` (optional): the data date to compute metrics against, in
  YYYY-MM-DD format. Defaults to today. Use this to compute metrics for a
  specific past date — for example, to reconstruct the EV position at a
  previous month-end for a retrospective review.

**When to use it.** Use at any monthly review, gate review, or governance
submission where you need an objective performance measure. The interpretation
strings make the output accessible to non-specialist audiences.

---

### generate_ev_dashboard

**What it does.** Produces a self-contained HTML dashboard that visualises
all EV metrics, displays SPI and CPI with traffic-light colour coding, and
renders an S-curve chart (Planned Value, Earned Value, and Actual Cost over
time) as inline SVG. The dashboard has no external dependencies and can be
opened in any browser or attached directly to a board pack.

**Key parameters.**
- `project_id` (required).
- `status_date` (optional): as above.
- `output_path` (optional): a file path to write the HTML file to. If omitted,
  the HTML is returned as text which can be saved manually.

**When to use it.** Use when you need a visual output for a board presentation,
a monthly report attachment, or a gate review pack. The dashboard is designed
to be intelligible to a non-technical governance audience: the S-curve makes
the gap between planned and actual performance immediately visible, and the
traffic-light indices communicate the severity of any issues without requiring
the reader to understand the underlying arithmetic.

---

## Common workflows

### Workflow 1: Monthly EV review

1. Ensure the project schedule data has been loaded via `load_project` in
   pm-data.
2. Run `compute_ev_metrics` with today's date (or the month-end date).
3. Review the SPI and CPI. If either is below 1.0, read the interpretation
   strings for EAC and TCPI.
4. If TCPI is above 1.1, or EAC materially exceeds BAC, this is a governance
   trigger — the project needs to explain how it will recover or request a
   budget revision.
5. Run `generate_ev_dashboard` to produce a visual output for the monthly
   report pack.

### Workflow 2: Pre-gate performance baseline

1. Run `compute_ev_metrics` with the status date set to the day before the
   gate review.
2. Use the EAC to check whether the business case cost estimate remains
   credible given current delivery efficiency.
3. Use the SPI to check whether the planned completion date remains achievable.
4. Include the dashboard output in the gate review evidence pack.

### Workflow 3: Investigating a cost concern

1. Run `compute_ev_metrics` at the current date.
2. Check the CPI. If it is below 0.9, read the EAC: this is what the project
   is projected to cost at completion.
3. Compare EAC to BAC. The difference (VAC) is the projected overspend.
4. Check the TCPI. If it is above 1.1, the project cannot recover to BAC at
   current delivery efficiency.
5. Escalate the EAC and TCPI findings at the next governance forum and consider
   whether a revised business case is required.

---

## Worked examples

### Example 1: Computing EV metrics at a monthly review

**Scenario.** You are the Project Manager for a £8 million IT transformation
project. At the end of March, the project sponsor asks for a performance update.
Team reporting says the project is "roughly on track."

**What to do.** Ask Claude to run `compute_ev_metrics` for your project with
a status date of 31 March.

**What Claude does.** It processes the task schedule data, computes PV, EV,
and AC as of 31 March, and returns all derived indices with interpretation
text. In this example, results show: PV £4.2m, EV £3.8m, AC £4.5m. SPI 0.90,
CPI 0.84.

**How to interpret the output.** The project is 10% behind schedule (SPI 0.90)
and spending at a rate that is 16% less efficient than planned (CPI 0.84). The
EAC is approximately £9.5 million — £1.5 million above the £8 million BAC.
"Roughly on track" does not reflect the objective position. This finding should
be raised at the next governance meeting.

---

### Example 2: Interpreting a CPI of 0.82 and what it means for EAC

**Scenario.** You are an assurance reviewer conducting a mid-project review.
The compute_ev_metrics output shows CPI 0.82. You need to explain to the SRO
what this means and what action is required.

**What to do.** Note the BAC from the project data. Divide BAC by the CPI to
compute EAC. Check the TCPI.

**What Claude does.** With a BAC of £12 million and CPI of 0.82, EAC is
approximately £14.6 million. TCPI is calculated as the remaining budget divided
by remaining work — if significant work remains, TCPI will be materially above
1.0.

**How to interpret the output.** The project is projected to cost £14.6 million
against an approved budget of £12 million — a £2.6 million overrun. A CPI of
0.82 at this stage of delivery is unlikely to recover to 1.0 by completion.
The SRO should be informed that the business case cost assumption is no longer
supported by actual performance data, and a formal cost review is warranted.
The TCPI tells you how efficient the team must be for the rest of the project
to avoid this overrun — if it is above 1.1, recovery to BAC is not realistic
without scope reduction.

---

### Example 3: Generating an HTML dashboard for a board pack

**Scenario.** Your departmental board meets in two days. The board secretary
has asked for a one-page visual summary of the project's delivery performance
to include in the board papers.

**What to do.** Ask Claude to run `generate_ev_dashboard` for the project with
an `output_path` pointing to a local file. Attach the resulting HTML file to
the board pack.

**What Claude does.** It computes all EV metrics, renders the SPI and CPI as
traffic-light indicators, and produces an S-curve showing the PV, EV, and AC
curves over the project timeline. The HTML is self-contained — it requires no
internet connection or external stylesheet.

**How to interpret the output.** The S-curve tells the story at a glance.
Where EV falls below PV, the project is behind schedule. Where AC rises above
EV, the project is overspending for the work done. A board member who has
never seen EV analysis before can read the direction of the curves and
understand the performance picture. The traffic-light indices anchor the visual
to the two key governance questions: are we on time, and are we on budget?

---

## Limitations and considerations

- EV analysis is only as reliable as the underlying schedule data. If tasks are
  not accurately baselined with planned values and completion percentages, the
  resulting metrics will not reflect reality. Garbage in, garbage out applies
  here more than anywhere.
- The SPI becomes less meaningful in the final stages of a project, when most
  work is nearly complete and the index converges towards 1.0 regardless of
  actual performance.
- EV does not measure quality. A project can deliver high EV while accumulating
  technical debt, defects, or scope compromise.
- The EAC calculated here assumes the current CPI will continue for the
  remainder of the project. This is a reasonable statistical assumption for
  planning purposes but may not reflect specific planned interventions.
- Interpreting EV results requires some understanding of the project context.
  An SPI of 0.90 on a project that has just completed a difficult early phase
  may recover; an SPI of 0.90 on a project that is 80% through its timeline
  almost certainly will not. Use professional judgement alongside the metrics.

---

## Related modules

- **pm-data**: used to load the project schedule data that EV analysis depends
  on. The project must be loaded before EV tools can be run.
- **pm-financial**: for project-level financial tracking including budget
  approvals, spend to date, and forecast to completion.
- **pm-analyse**: for schedule analysis including critical path, float
  consumption, and milestone compliance — complements the schedule dimension
  of EV analysis.
- **pm-synthesis**: for AI-generated executive summaries that incorporate EV
  findings alongside other assurance data.
- **pm-knowledge**: for IPA benchmark data on typical cost overrun and schedule
  slip for comparable project types — provides context for interpreting your
  CPI and SPI readings.
