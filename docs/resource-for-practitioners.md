# Resource Capacity Planning — A Guide for Project Delivery Professionals

This guide explains the resource capacity planning capabilities available in
the PDA Platform. No technical background is needed.

---

## What this module does

Resource constraints are one of the most reliably underestimated sources of
delivery risk in UK government projects. Schedules are built assuming people
will be available; business cases are approved on the basis of resource plans
that look adequate on paper. The reality — that key individuals carry multiple
concurrent commitments, that specialist skills are scarce across the portfolio,
and that the departure of a single person can stall a workstream — frequently
becomes visible only when delivery is already in difficulty.

The `pm-resource` module provides structured analysis of resource demand
against supply, both within a single project and across the portfolio. It
identifies over-allocations, contention points, and critical dependencies
before they translate into schedule slippage. Because resource conflicts are
a leading indicator of schedule risk, catching them early creates options for
intervention — resequencing, supplementing capacity, or adjusting scope —
that are not available once the slippage has occurred.

The module supports the resource planning requirements that IPA Gateway
Reviews and programme assurance boards examine: whether the project has the
right people with the right skills at the right time, and whether the
portfolio as a whole is trying to draw on more resource than is realistically
available. This is particularly relevant in the UK government context where
specialist delivery skills — commercial, digital, project controls — are
shared across many competing programmes.

---

## When to use it

- When building the resource plan for a new project and wanting to check it
  against known commitments elsewhere in the portfolio.
- When you suspect a workstream is at risk because a key individual has been
  redirected to another priority.
- Before finalising a project schedule, to check that the roles required on
  the critical path are actually available at the planned times.
- When preparing for an IPA Gateway Review that will examine whether the
  project's resource assumptions are realistic.
- When a team member is due to leave and you want to assess the delivery
  impact systematically.
- When a Programme Director needs to understand whether the portfolio has
  the aggregate capacity to start a new project without de-prioritising
  existing commitments.
- When a project is running late and you want to test whether bringing in
  additional resource would recover the schedule, or whether critical-path
  constraints mean more people would not help.

---

## Key concepts

### Resource loading

Resource loading describes the degree to which a person or role is committed
across their planned working time. A resource loaded at 100% has no capacity
for unplanned work, risk responses, or knowledge transfer. IPA guidance and
experienced project managers routinely flag any resource plan that assumes
key individuals at sustained high utilisation rates as unrealistic.

### Over-allocation

Over-allocation occurs when a person or role is assigned more work than their
available capacity allows within a given period. Even brief over-allocations
on the critical path create schedule risk: if the work cannot slip, the person
must absorb the overload, which typically leads to quality issues, fatigue,
and eventual delivery failure.

### Critical resources

A critical resource is any person or role whose absence would directly delay
the critical path. This is distinct from being generally important: a resource
is critical in this sense if there is no available substitute with the
equivalent skill, clearance level, or relationship, and if their tasks sit
on or directly feed the critical path.

### Portfolio capacity

At portfolio level, the same individual or skill pool may appear in the
resource plans of several projects simultaneously. Portfolio capacity analysis
aggregates these demands to identify systemic shortfalls — situations where
the portfolio as a whole is competing for resource that does not exist in
sufficient quantity.

---

## Tools

### log_resource_plan

Records the planned resource profile for a project: which roles or named
individuals are required, in what volumes, and across which time periods.
This is the baseline against which all subsequent analysis is run.

**Key parameters:** `project_id`, `resource_entries` (list of entries, each
with `role`, `individual` (optional), `fte_required`, `start_date`,
`end_date`, `workstream` (optional)).

**When to use it:** At project initiation and whenever the resource plan is
formally updated — typically at gate approvals, after a replan, or when
significant scope changes affect the resource demand profile. A plan that is
not updated after a replan will produce misleading analysis.

---

### analyse_resource_loading

Computes utilisation by role or individual across the project schedule.
Returns a period-by-period breakdown showing where utilisation is within
normal bounds, approaching maximum capacity, or already over-allocated.

**Key parameters:** `project_id`, `granularity` (weekly or monthly),
optional `role` or `individual` filter, optional `from_date` and `to_date`.

**When to use it:** Before finalising a schedule or confirming resource
commitments. Run it at monthly intervals during delivery to confirm that
loading assumptions are holding. Pay particular attention to periods where
multiple workstreams peak simultaneously — these create compound loading
pressure that is not visible when workstreams are reviewed in isolation.

---

### detect_resource_conflicts

Identifies specific over-allocations and contention points: periods where
a person or role is assigned more than their available capacity, or where
the same scarce skill is required in two places at once.

**Key parameters:** `project_id`, optional `severity_threshold` (flag only
conflicts above a specified percentage of over-allocation), optional
`include_portfolio` (flag to check the same individuals against their
portfolio-level commitments, not just this project's plan).

**When to use it:** After logging or updating a resource plan, before
committing to a schedule baseline, and whenever a change request affects
resource demand. The `include_portfolio` flag is particularly important
for individuals whose time is split across projects: a conflict may not
be visible within one project's plan but becomes obvious when their total
portfolio commitments are aggregated.

---

### get_critical_resources

Identifies the people and roles whose absence would critically impact
delivery. The analysis considers: whether the individual's tasks sit on
the critical path, whether a suitably qualified substitute is available,
and whether there is a single point of knowledge dependency — situations
where only one person holds essential knowledge, relationships, or
clearances.

**Key parameters:** `project_id`, optional `include_single_point_of_failure`
flag (default: true).

**When to use it:** Before any IPA Gateway Review that examines resource
risk, before an annual leave or secondment period that will remove key
individuals, and proactively when the project is still in planning — the
earlier a critical resource dependency is identified, the more options
exist for mitigating it through knowledge transfer, cross-training, or
adjusted scheduling.

---

### get_portfolio_capacity

Aggregates resource demand and supply across all projects in the portfolio.
Returns the total FTE demand by role and time period, set against the known
available supply, and identifies periods and roles where aggregate demand
exceeds supply.

**Key parameters:** `portfolio_id`, optional `role` filter, optional `period`
range, optional `flag_new_project` (to model the impact of adding a new
project to the portfolio without yet committing to it).

**When to use it:** Before approving a new project start, before a portfolio
board that must make prioritisation decisions, and whenever a cross-cutting
delivery event — such as a major system go-live requiring many projects to
draw on the same specialists simultaneously — is approaching. Use the
`flag_new_project` parameter to model hypothetical scenarios: "if we start
Project X next quarter, what does that do to aggregate capacity for the
commercial team?"

---

## Common workflows

### Workflow 1: Validating a resource plan before schedule baseline

1. Use `log_resource_plan` to record the resource requirements from the
   project's schedule.
2. Run `analyse_resource_loading` at monthly granularity to see the demand
   profile across the full project timeline.
3. Run `detect_resource_conflicts` with `include_portfolio=true` to check
   for over-allocations, taking into account the individuals' other
   commitments.
4. For any conflicts identified, either resequence the affected tasks in
   the schedule, identify substitute resources, or escalate the capacity
   gap to the programme board before the schedule is baselined.
5. Run `get_critical_resources` to identify where single-point dependencies
   exist, and record the findings in the risk register using `pm-risk`.

### Workflow 2: Monitoring resource health during delivery

1. At each monthly project review, run `analyse_resource_loading` to confirm
   that actual loading is tracking to the plan.
2. Run `detect_resource_conflicts` to surface any emerging over-allocations
   caused by schedule changes, additional work, or individuals being drawn
   to other priorities.
3. If a conflict is identified on the critical path, escalate to the project
   board with the specific resource, period, and magnitude of the conflict.
4. Update `log_resource_plan` if the resource profile has materially changed
   since the last update, to keep the analysis current.

### Workflow 3: Portfolio capacity check before approving a new project

1. Before the portfolio board considers approving a new project start date,
   use `get_portfolio_capacity` with the `flag_new_project` parameter to model
   the aggregate demand if the new project proceeds as planned.
2. Identify any roles or individuals where aggregate demand would exceed supply
   during the proposed start period.
3. Present the capacity analysis to the portfolio board alongside the business
   case, so that the approval decision explicitly accounts for resource
   realism — not just strategic priority and financial value.
4. If capacity is constrained, model alternative start dates or phased
   mobilisation options using different period ranges in `get_portfolio_capacity`.

---

## Worked examples

### Example 1: Detecting a resource conflict on the critical path

**Scenario.** Project MERIDIAN is in Month 4 of delivery. A replan has
compressed the schedule by two months, meaning two workstreams now overlap
that were previously sequential. Both require the same senior technical
architect, who is also committed 40% of his time to Project NOVA.

**What to do.** Ask Claude: "Run resource conflict detection for Project
MERIDIAN including portfolio commitments. Focus on the senior technical
architect role."

**What Claude does.** Calls `detect_resource_conflicts` with
`include_portfolio=true`. It computes the total demand on the technical
architect across both projects in the overlap period and compares it to
their available capacity.

**How to interpret the output.** If the output shows the technical architect
is loaded at 140% during Months 5 and 6 — 100% from MERIDIAN and 40% from
NOVA — this is a confirmed over-allocation on the critical path. Options to
consider: negotiate a temporary reduction in the NOVA commitment during Months
5-6, bring in a second architect to share the MERIDIAN workload, or resequence
the compressed workstreams. Each option has schedule and cost implications that
should be assessed before choosing. Log the conflict as a RESOURCE risk in the
risk register with a proximity of 30 days.

---

### Example 2: Identifying a key-person dependency before they leave

**Scenario.** The programme's lead commercial manager, who has managed all
supplier relationships since contract award, has announced she will be taking
a secondment in six weeks. You want to understand the delivery impact before
her departure.

**What to do.** Ask Claude: "Run critical resource analysis for Programme
AURORA. Include single point of failure identification. I'm particularly
concerned about the lead commercial manager role."

**What Claude does.** Calls `get_critical_resources` with
`include_single_point_of_failure=true`. It assesses whether the commercial
manager's tasks sit on the critical path, whether there is a qualified
successor, and whether there are knowledge or relationship dependencies
that are not currently documented.

**How to interpret the output.** If the output flags the lead commercial
manager as a critical single-point-of-failure — tasks on the critical path,
no identified substitute with equivalent contract knowledge, and supplier
relationships not documented — you have six weeks to act. Initiate a
structured knowledge transfer programme immediately: document all active
contract provisions, introduce a successor to key supplier contacts, and
review any upcoming contractual milestones that will fall within the
secondment period. Log this as a RESOURCE risk and record the mitigation
plan in pm-risk.

---

### Example 3: Portfolio capacity check before approving a new project start

**Scenario.** The Portfolio Board is considering approving Project CLIO to
start in the next quarter. It requires 2.0 FTE of digital delivery specialists
and 1.0 FTE of senior commercial resource from Month 1. The portfolio already
has four active projects.

**What to do.** Ask Claude: "Run a portfolio capacity analysis for the next
two quarters. Then model what happens to aggregate digital delivery and
commercial capacity if we add Project CLIO starting next month."

**What Claude does.** Calls `get_portfolio_capacity` across the existing
portfolio for the next two quarters, then calls it again with
`flag_new_project` parameters representing CLIO's resource requirements.

**How to interpret the output.** If the current portfolio is already drawing
on 4.5 FTE of digital delivery specialists against a known supply of 5.0 FTE,
adding CLIO's 2.0 FTE demand would create a shortfall of 1.5 FTE that has no
funded solution. The portfolio board should not approve CLIO's current start
date without either identifying additional capacity or confirming that one of
the existing projects will reduce its digital demand in the same period. This
is the kind of quantified capacity evidence that transforms a portfolio board
from a priority-ranking exercise to a genuine resource governance function.

---

## Limitations and considerations

- The module analyses the resource data it has been given. If the resource
  plan has not been updated to reflect schedule changes, staff movements, or
  revised scope, the analysis will reflect the outdated plan rather than
  the current reality.
- Available supply must be entered manually. The module does not have access
  to HR systems, organisational directories, or leave calendars. Capacity
  figures should be agreed with the relevant line managers or PMO.
- Resource loading analysis treats FTE as a homogeneous unit within a role
  category. In practice, individuals within the same role classification
  may have very different skills, clearance levels, or relationship capital.
  The module flags the quantitative conflict; the qualitative assessment of
  substitutability requires human judgment.
- The module identifies conflicts and dependencies; it does not recommend
  specific solutions. The right response to a resource conflict depends on
  the project's risk appetite, budget flexibility, and schedule tolerance.
- Portfolio capacity analysis is only as comprehensive as the projects and
  resource plans that have been logged. Projects not recorded in the system
  will not appear in the aggregate demand picture.

---

## Related modules

- **pm-schedule** — Resource conflicts identified here should be cross-
  referenced with the critical path analysis in pm-schedule. A conflict
  matters most when it falls on the critical path; pm-schedule identifies
  which tasks have zero float.
- **pm-risk** — Critical resource dependencies and portfolio capacity
  shortfalls identified here should be logged as RESOURCE risks in pm-risk,
  with mitigations and owners assigned.
- **pm-change** — Approved scope changes often increase resource demand.
  After any significant change approval, re-run resource loading analysis
  to check whether the change creates new conflicts.
- **pm-financial** — Resolving resource conflicts through additional capacity
  (contractors, additional headcount) has cost implications. Log the cost
  impact via pm-financial.
