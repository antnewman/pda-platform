# AI Health Summaries — A Guide for Practitioners

This guide explains the AI-powered synthesis capabilities available in the PDA
Platform. No technical background is needed. The module is designed for Senior
Responsible Owners, Portfolio Directors, and assurance professionals who need
to communicate project health clearly to governance forums without manually
collating data from multiple sources.

---

## What this module does

Running a full assurance picture on a complex project means drawing on multiple
data sources: compliance scores, open actions, assumption drift, ARMM maturity,
gate readiness, benefits health, and earned value performance. Individually,
each gives a partial view. Together, they tell a coherent story — but
translating that story into a concise, audience-appropriate briefing takes
significant time.

The Synthesis module automates this collation. It queries all available project
data held in the platform store and passes it to the Anthropic Claude AI to
produce a structured executive summary. The output is calibrated to the
audience specified: a bullet-point briefing for an SRO, a prose narrative for
a PMO team, or a short RAG-status headline for a board.

The `compare_project_health` tool extends this to multiple projects, producing
a comparative analysis that identifies which project is healthiest, which is
at most risk, and what issues appear across multiple projects in common — useful
for portfolio reviews, investment committees, and PIR panels.

These tools do not produce data themselves. They synthesise data that has
already been gathered by the other platform modules. For the summaries to be
meaningful, the underlying project data must be current and complete.

---

## When to use it

- Preparing an SRO briefing before a board meeting, gate review, or spend
  control submission, where the SRO needs a concise decision-focused summary
  rather than a set of raw data outputs.
- Producing a PMO narrative for a monthly report that needs to integrate
  findings from risk, schedule, benefits, and compliance in a single readable
  document.
- Comparing two to five projects for a portfolio review or investment committee
  meeting, where the committee needs to understand relative performance rather
  than absolute metrics.
- Identifying the weakest project in a programme for prioritised assurance
  support when capacity is constrained.
- Quickly onboarding a new SRO or assurance reviewer onto a project's current
  status without them having to work through all the underlying data manually.

---

## How these tools work

When you ask for a health summary, the tool retrieves data from all modules
that have information about that project: compliance and workflow data from
pm-assure, open actions and recommendations, assumption drift records, ARMM
maturity assessments, gate readiness scores, and benefits health from pm-brm.
If earned value data is present from pm-ev, it is included. This data is
compiled into a structured prompt and sent to the Anthropic Claude API.

The AI then produces a summary calibrated to the requested audience. It uses
IPA and HM Treasury terminology throughout — DCA ratings, gate nomenclature,
benefits realisation, ARMM levels — so the output is already in the language
of UK government project assurance.

For `compare_project_health`, the same process runs for each project in the
list. The AI then produces both a structured comparison table and a comparative
narrative identifying relative strengths, common weaknesses, and the projects
most in need of attention.

---

## Understanding the confidence score

The summary will include an overall confidence indicator for each project. This
reflects two things simultaneously:

1. **Data completeness**: a project with a full set of recent assessments
   across all platform modules will have a higher base confidence than one where
   several modules have no data. Gaps in the data reduce confidence — not
   because the project is necessarily performing badly, but because the
   assessment cannot be comprehensive.

2. **Delivery performance**: where data exists, projects with low compliance
   scores, CRITICAL assumption drift, NOT_READY gate status, or benefits in
   Evaporated status will have a lower confidence score.

A high confidence score means the project is well-assessed and performing well
across the dimensions that have been measured. A low confidence score may
indicate poor performance, gaps in assessment data, or both. The summary text
will clarify which.

---

## Tools

### summarise_project_health

**What it does.** Gathers all available assurance data for a single project
and produces a plain-English executive briefing via the Anthropic Claude API.
The tone, length, and structure of the output are controlled by the `audience`
parameter.

**Key parameters.**
- `project_id` (required): the project identifier.
- `audience` (optional, default `SRO`): controls the output format.
  - `SRO`: four to six decision-focused bullet points with clear action items.
    Suitable for an SRO reading a briefing pack in advance of a governance
    meeting.
  - `PMO`: a prose paragraph followed by a structured action list. Suitable
    for a monthly PMO report or a project team debrief.
  - `BOARD`: two to three sentences, leading with the RAG status and the
    single most important finding. Suitable for inclusion in board papers or
    a DIC submission.
- `sections` (optional): restrict the summary to specific data domains.
  Available sections are `compliance`, `actions`, `assumptions`, `armm`,
  `gate_readiness`, and `benefits`. If omitted, all available sections are
  included.

**When to use it.** Use this tool whenever you need to move from raw platform
data to a document that can go in front of a governance audience without further
manual editing. The BOARD audience format is suitable for direct inclusion in
board papers; the SRO and PMO formats need the practitioner to review but save
significant collation time.

---

### compare_project_health

**What it does.** Gathers assurance data for two to five projects and produces
a comparative briefing via the Anthropic Claude API. The output includes a
structured comparison table showing key metrics side by side, and a
Claude-generated narrative that identifies the healthiest project, the
highest-risk project, and any common issues appearing across multiple projects.

**Key parameters.**
- `project_ids` (required): a list of two to five project identifiers.

**When to use it.** Use at portfolio reviews, investment committee meetings,
or when a programme manager needs to understand the relative health of projects
within a programme. The comparative narrative is particularly useful when
different projects are at different stages and a like-for-like metric comparison
would be misleading — the AI interprets the data in context.

---

## Using synthesis tools with role system prompts

For the best results, use these tools alongside a role system prompt from
`docs/prompts/role-system-prompts.md`. A role system prompt tells Claude who
is asking and what decisions they are trying to make — this significantly
improves the relevance of the output.

For example, using the SRO role prompt alongside `summarise_project_health`
with `audience: SRO` produces a briefing that addresses the specific decisions
an SRO faces at this stage of the project lifecycle, rather than a generic
health summary.

The PMO role prompt used with `compare_project_health` produces a comparison
written in the language of operational programme management, focusing on
dependency risks and resource implications rather than governance-level findings.

---

## Common workflows

### Workflow 1: SRO briefing before a board meeting

1. Confirm that the project's data is current in the platform — run any
   outstanding assurance tools (pm-assure, pm-brm, pm-gate-readiness) first
   if assessments are overdue.
2. Run `summarise_project_health` with `audience: SRO`.
3. Review the output carefully. Check that the key findings match your own
   understanding of the project. Where they do not, investigate whether the
   platform data may be stale.
4. Use the bullet points as the basis for the SRO's governance briefing.

### Workflow 2: Portfolio review comparison

1. Confirm that all projects in the comparison have been assessed recently.
2. Run `compare_project_health` with the list of project IDs.
3. Review the comparison table and the narrative. Note which project the AI
   identifies as highest-risk and whether the reasoning is consistent with
   your own assessment.
4. Use the output as a starting point for the portfolio discussion. The
   structured table provides evidence; the narrative provides interpretation.

### Workflow 3: Prioritising assurance support

1. Run `compare_project_health` across all projects in scope.
2. Review the narrative to identify which project is flagged as highest-risk.
3. If the comparison surfaces common issues appearing in multiple projects,
   consider whether these represent programme-level risks rather than
   individual project problems. Escalate accordingly.
4. Allocate assurance resource to the projects identified as weakest, using
   the comparison output as the documented rationale.

---

## Worked examples

### Example 1: Generating an SRO-ready project summary before a board meeting

**Scenario.** You are a PMO lead supporting an SRO who chairs a programme board
meeting in 48 hours. The SRO has asked for a concise summary of the project's
current assurance position. The SRO will not have time to read detailed outputs
from each platform module.

**What to do.** Ask Claude to run `summarise_project_health` for the project
with `audience: SRO`. Review the output before passing it to the SRO.

**What Claude does.** It retrieves compliance scores, open actions, assumption
drift, ARMM maturity, gate readiness, and benefits data. It calls the
Anthropic Claude API to produce four to six bullet points structured around
the decisions the SRO needs to make: what is working, what is not, what
requires a decision, and what the recommended action is.

**How to interpret the output.** The bullet points are written for action,
not for information. Each should tell the SRO something they need to know or
do, not merely describe the data. Review the output and ask yourself: does
each point correspond to a real finding in the underlying data? If the platform
data is accurate and current, the answer should be yes. If a finding seems
surprising, check whether the underlying data is up to date before passing
the summary to the SRO.

---

### Example 2: Comparing three projects for a portfolio review

**Scenario.** A Portfolio Director chairs a quarterly portfolio review for a
programme containing three major projects. She needs to understand how they
compare and which requires the most attention in the next quarter.

**What to do.** Ask Claude to run `compare_project_health` with all three
project IDs.

**What Claude does.** It gathers assurance data for all three projects in
parallel and calls the Anthropic Claude API to produce a structured comparison
table showing compliance scores, gate readiness, ARMM maturity, benefits
status, and open action counts side by side. It also produces a comparative
narrative identifying the strongest project, the weakest, and any patterns
appearing across more than one project.

**How to interpret the output.** The structured table gives the Portfolio
Director an at-a-glance comparison of objective metrics. The narrative is more
valuable for governance: it contextualises the numbers, highlights when a weak
result in one project is echoed by a concern in another, and draws attention
to shared risks that might not be visible from the individual project reports.

---

### Example 3: Using compare_project_health to identify the weakest project for prioritised assurance support

**Scenario.** Your assurance team has capacity to conduct one additional
targeted review this month. Four projects are competing for that slot. You
need to make a defensible, evidence-based decision about which project to
prioritise.

**What to do.** Run `compare_project_health` with all four project IDs.

**What Claude does.** It produces a comparison across all four, with the
narrative identifying the highest-risk project and the specific reasons —
which might include a combination of low compliance, critical assumption drift,
NOT_READY gate status, and benefits evaporation risk.

**How to interpret the output.** The project identified as highest-risk by the
AI is your prioritisation recommendation. The specific reasons provided in the
narrative are your documented rationale. If the assurance team or the Portfolio
Director disagrees with the AI's prioritisation, the narrative provides a
starting point for that conversation — it is easier to challenge a reasoned
argument than an unexplained metric ranking.

---

## Limitations and considerations

- These summaries are AI-generated. They should be reviewed by a practitioner
  before use in formal governance documents. The AI synthesises the data it is
  given; it does not know context that has not been captured in the platform —
  for example, recent verbal commitments from a supplier, a policy change that
  invalidates an assumption, or an SRO decision that has not yet been recorded.
- The quality of the output depends directly on the currency and completeness
  of the underlying platform data. If a project has not been assessed recently,
  or if key modules have no data, the summary will reflect that gap. A partial
  summary is not a clean bill of health.
- These tools require the `ANTHROPIC_API_KEY` environment variable to be set
  in the platform environment. If this is not configured, the tools will return
  an error. Contact the platform administrator if this is not working.
- `compare_project_health` accepts a maximum of five project IDs. For larger
  portfolios, use `get_portfolio_health` from pm-portfolio first to identify
  the highest-priority subset, then compare those.
- The AI-generated narrative is not a substitute for professional assurance
  judgement. It is a starting point for the governance conversation, not the
  conversation itself.

---

## Related modules

- **pm-assure**: provides the compliance, action, assumption, and ARMM data
  that synthesis tools draw on.
- **pm-brm**: provides the benefits health data included in summaries.
- **pm-gate-readiness**: provides the gate readiness scores included in
  summaries.
- **pm-ev**: provides earned value metrics that are incorporated when available.
- **pm-portfolio**: for aggregating raw data across large project portfolios
  before using synthesis tools for narrative interpretation.
- **pm-risk**: for detailed risk register data referenced in assurance
  summaries.
