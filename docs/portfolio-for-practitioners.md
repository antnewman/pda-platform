# Portfolio Health and Intelligence — A Guide for Practitioners

This guide explains the portfolio aggregation capabilities available in the PDA
Platform. No technical background is needed. The module is designed for Senior
Responsible Owners, Portfolio Directors, and Programme Management Office leads
who need to understand the health of multiple projects in a single view.

---

## What this module does

Individual project reviews are necessary but not sufficient. A project that
looks acceptable in isolation may be one of several projects sharing the same
external dependency, the same stretched SRO, or the same set of optimistic
assumptions. These systemic risks are invisible until they are viewed together.

The Portfolio module aggregates assurance data across any group of projects held
in the PDA Platform store. It pulls the latest compliance scores, gate readiness
assessments, benefits realisation data, ARMM maturity levels, and assumption
drift readings — then summarises them at portfolio level. The result is a single
structured view that a Portfolio Director or investment committee can use to
make decisions about where to direct assurance attention and resource.

This module does not replace individual project reviews. It complements them by
surfacing the patterns that only become visible when multiple projects are
examined side by side.

---

## When to use it

- Preparing a portfolio dashboard for a Digital Investment Committee (DIC) or
  spend control panel.
- Deciding which projects need a targeted assurance intervention before the
  next gateway cycle.
- Identifying systemic issues — shared assumptions, common blockers, clustered
  gate failures — that point to a programme-level problem rather than individual
  project weaknesses.
- Monthly or quarterly portfolio reporting to a Senior Responsible Owner or
  departmental board.
- Prioritising assurance resource when capacity is constrained and not every
  project can receive a full review in the same period.

---

## Tools

### get_portfolio_health

**What it does.** Retrieves the latest compliance score and health status for
each project, along with the count of open and recurring actions. Returns a
per-project breakdown and portfolio-level averages.

**Key outputs.**
- `latest_compliance_score` per project: a 0–1 score from the assurance
  compliance analysis. Below 0.6 indicates a project in Watch or worse
  condition.
- `health` and `workflow_health`: the health classifications recorded from
  the most recent assurance workflow runs.
- `open_action_count`: the number of unresolved recommendations outstanding
  against each project.
- `portfolio.average_compliance_score`: the mean compliance score across all
  projects with data.
- `portfolio.by_health`: a distribution showing how many projects sit in each
  health category.
- `portfolio.total_open_actions`: the aggregate unresolved action count across
  the portfolio.

**Key parameters.**
- `project_ids` (required): a list of the project identifiers you want to
  aggregate. These are the same IDs used throughout the platform.

**When to use it.** Use this as the starting point for any portfolio review.
It gives you the overall picture — which projects are healthy, which are in
distress, and where unresolved actions are concentrating.

---

### get_portfolio_gate_readiness

**What it does.** Retrieves the most recent gate readiness assessment for each
project and summarises how many projects are ready, blocked, or insufficiently
assessed across the portfolio.

**Key outputs.**
- Per-project: the gate being assessed, the readiness level (READY,
  CONDITIONAL, NOT_READY, or INSUFFICIENT_DATA), and the composite readiness
  score.
- `portfolio.by_readiness`: a count of projects in each readiness category.

**Key parameters.**
- `project_ids` (required).
- `gate` (optional): filter to a specific gate type (e.g. `GATE_2`) if you
  want to compare readiness for a particular review across projects that are
  all at the same stage.

**When to use it.** Use before a gateway cycle to identify which projects are
blocked and which may need expedited assurance support before their review
date. Use with the gate filter when a cohort of projects are all approaching
the same gate.

---

### get_portfolio_brm_overview

**What it does.** Aggregates the benefits registers across all specified
projects. Returns per-project benefit counts, status breakdown, and the sum
of target versus currently-realised benefit values. Returns portfolio-wide
totals.

**Key outputs.**
- Per-project: number of benefits, breakdown by status (Identified, Planned,
  Realizing, Achieved, Evaporated, Cancelled), total target value, and total
  realised value.
- `portfolio.total_benefits`, `portfolio.by_status`, `portfolio.total_target_value`,
  `portfolio.total_realised_value`.

**Key parameters.**
- `project_ids` (required).

**When to use it.** Use when preparing a benefits-focused update for an
investment committee, a Departmental Board, or a post-implementation review
panel. A large gap between `total_target_value` and `total_realised_value`
across the portfolio is a significant governance signal. A concentration of
benefits in Evaporated or Cancelled status is a direct line to the business
case.

---

### get_portfolio_armm_summary

**What it does.** Retrieves the latest ARMM (Assurance and Risk Management
Maturity) assessment for each project and summarises the distribution of
maturity levels across the portfolio.

**Key outputs.**
- Per-project: the overall ARMM maturity level (1–5) and score percentage from
  the most recent assessment.
- `portfolio.average_score_pct`: mean maturity score across all assessed
  projects.
- `portfolio.by_level`: how many projects sit at each maturity level.
- `portfolio.projects_with_no_data`: count of projects that have not yet been
  through an ARMM assessment.

**When to use it.** Use when assessing whether the portfolio as a whole has
adequate risk management and assurance capability in place. A cluster of
Level 1 or Level 2 projects signals that the portfolio is operating on
informal, undocumented assurance practices and is vulnerable to being caught
by surprise. Flag this at programme governance.

---

### get_portfolio_assumptions_risk

**What it does.** Aggregates assumption drift data across all specified
projects. For each project, it reads the latest validation severity for every
assumption in the register and counts how many are drifting at HIGH or CRITICAL
severity. Returns a list of projects with CRITICAL drift.

**Key outputs.**
- Per-project: total assumption count, breakdown by drift severity, and the
  count of HIGH or CRITICAL assumptions.
- `portfolio.total_high_critical_drift`: the aggregate count of HIGH or CRITICAL
  drifting assumptions across the portfolio.
- `portfolio.projects_with_critical_drift`: the specific project IDs where at
  least one assumption has reached CRITICAL severity.

**Key parameters.**
- `project_ids` (required).

**When to use it.** Use when you suspect a shared external factor — a
technology platform, a policy change, a supplier arrangement — is affecting
multiple projects simultaneously. If several projects show CRITICAL drift on
assumptions that describe the same dependency, this is a programme-level
issue, not a series of unrelated individual problems.

---

## Common workflows

### Workflow 1: Monthly portfolio dashboard

1. Run `get_portfolio_health` with all active project IDs.
2. Note which projects have compliance scores below 0.6 or large open action
   counts. These are your watch-list.
3. Run `get_portfolio_gate_readiness` to see which projects are approaching
   reviews and what their readiness status is.
4. Run `get_portfolio_brm_overview` to show the benefits position.
5. Combine the outputs into a single structured summary for the Portfolio
   Director or investment committee.

### Workflow 2: Targeting assurance interventions

1. Run `get_portfolio_health` to identify the lowest-scoring projects.
2. Run `get_portfolio_assumptions_risk` on the same list to see whether the
   low-scoring projects are also carrying unvalidated or critically-drifting
   assumptions.
3. Run `get_portfolio_gate_readiness` on the same list to identify which
   projects are both low-compliance and approaching a gate review.
4. Projects that appear in all three risk lists — low compliance, critical
   assumption drift, and imminent gate review — should be prioritised for
   assurance resource first.

### Workflow 3: Investigating systemic risk

1. Run `get_portfolio_assumptions_risk` across the full portfolio.
2. Identify any projects appearing in `projects_with_critical_drift`.
3. For each flagged project, use `pm-assure` tools to read the specific
   assumptions at CRITICAL severity.
4. If the same assumption text or dependency appears across multiple projects,
   this is a systemic risk. Escalate at programme level rather than treating
   each project as an isolated case.

---

## Worked examples

### Example 1: Preparing a portfolio dashboard for a DIC

**Scenario.** You are a Portfolio Manager in a government department. The
Digital Investment Committee meets in three weeks and you need to produce a
health dashboard for the eight projects on its watch list.

**What to do.** Ask Claude to run `get_portfolio_health` on all eight project
IDs, followed by `get_portfolio_gate_readiness` and `get_portfolio_brm_overview`.

**What Claude does.** It retrieves the latest compliance scores, health
classifications, and open action counts for each project; identifies how many
are READY, CONDITIONAL, or NOT_READY for their next gate; and returns the total
target benefit value against the currently-realised value.

**How to interpret the output.** Look at the `by_health` distribution first.
If three of your eight projects are RED or AMBER-RED and two are approaching
a gate with NOT_READY status, you have a concentrated problem that needs a
clear explanation at the committee meeting. The BRM overview gives you the
benefits line: if the gap between `total_target_value` and
`total_realised_value` is large, the committee should be asking whether the
business cases remain credible.

---

### Example 2: Identifying which projects need urgent assurance intervention

**Scenario.** Your assurance team has capacity to conduct deep-dive reviews on
three projects this quarter, but twelve projects are active. You need to direct
that capacity to the projects most at risk.

**What to do.** Run `get_portfolio_health`, `get_portfolio_gate_readiness`, and
`get_portfolio_assumptions_risk` across all twelve projects.

**What Claude does.** It returns compliance scores, gate readiness levels, and
assumption drift severity for all twelve. Projects appearing with both low
compliance scores and CRITICAL assumption drift are the most exposed. Cross-
reference these with `get_portfolio_gate_readiness` to see which also have an
imminent gate review.

**How to interpret the output.** The three projects that combine the worst
compliance scores, the highest concentration of CRITICAL or HIGH assumption
drift, and the nearest gate review dates are your priority targets. You now
have a defensible, evidence-based rationale for resource allocation decisions.

---

### Example 3: Spotting systemic assumption drift across the portfolio

**Scenario.** Your programme includes five separate projects that all depend
on a shared cloud infrastructure platform being delivered by a central team.
You want to know whether assumption drift is beginning to appear consistently
across these five projects — a signal that the shared dependency is in trouble.

**What to do.** Run `get_portfolio_assumptions_risk` on the five project IDs.
Then, for each project flagged in `projects_with_critical_drift`, use the
pm-assure assumption tools to read the specific assumptions at CRITICAL
severity.

**What Claude does.** It returns the assumption drift breakdown for all five
projects and identifies which ones have reached CRITICAL severity. When you
drill into the specific assumptions, you find that four of the five projects
have an assumption describing the shared platform's delivery date — and all
four are drifting critically.

**How to interpret the output.** This is a programme-level risk, not a set of
five unrelated project problems. The appropriate response is to escalate to the
SRO for the shared platform, convene a cross-project risk meeting, and log a
programme-level risk against all five business cases. Individual project-level
monitoring will not be sufficient.

---

## Limitations and considerations

- The portfolio tools aggregate data that is already in the platform's store.
  They cannot pull data from projects that have not been loaded and assessed.
  A project appearing with `has_data: false` or no ARMM assessment should be
  treated as a data gap requiring follow-up, not as a healthy project.
- Compliance scores and health statuses reflect the most recent assurance run.
  If a project has not been assessed recently, the data may not reflect the
  current position.
- The `total_realised_value` in the BRM overview reflects `current_value`
  recorded in the benefits register. This figure is only as accurate as the
  measurements that have been entered. A benefits register that is not being
  actively maintained will produce misleading totals.
- Portfolio aggregation tools return quantitative data. The interpretation of
  that data — what it means for governance decisions — requires professional
  judgement. These tools inform the conversation; they do not replace it.

---

## Related modules

- **pm-assure**: drill down into individual project compliance, assumptions,
  and ARMM maturity for projects flagged by the portfolio tools.
- **pm-brm**: read, update, and analyse individual project benefits registers
  in detail.
- **pm-gate-readiness**: investigate the specific criteria behind gate readiness
  scores for flagged projects.
- **pm-synthesis**: generate AI-produced executive summaries and cross-project
  comparison briefings based on portfolio data.
- **pm-risk**: review the risk register for projects flagged by portfolio tools.
