# Assurance Quality Tracking — A Guide for Project Managers

This guide explains three capabilities available in the PDA Platform that help
you track assurance quality over time.  No technical background is needed.

---

## What is this for?

Every project goes through regular assurance reviews and gate assessments.
Over time, the same weaknesses can appear in review after review without being
resolved, compliance scores can quietly drift downwards between reporting
cycles, and the evidence artefacts submitted to a gate may not be as current
as they appear.

These three features help you spot all of those problems early:

1. **Artefact Currency Validator** checks whether the evidence documents
   submitted to a gate review are genuinely current — or whether they were
   hastily updated right before the gate without substantive change.

2. **Longitudinal Compliance Tracker** tells you whether your project's data
   compliance is getting better, getting worse, or staying flat — and raises
   an alert if it drops sharply or falls below a safe minimum.

3. **Cross-Cycle Finding Analyzer** captures every action point from a review,
   watches for the same action appearing in multiple consecutive reviews, and
   shows you which actions have been resolved and which are still open.

---

## Artefact Currency Validator

### What it does

When a project submits evidence artefacts — risk registers, benefits profiles,
delivery plans — to a gate review, the platform checks each document's last
modification timestamp against the gate date and a configured currency window.

It detects two distinct problems:

- **Genuinely outdated artefacts**: documents that have not been updated within
  the acceptable staleness window (default: 90 days).
- **Last-minute compliance updates**: documents updated within a very short
  window immediately before the gate date (default: 3 days).  This pattern —
  hastily updating stale documents right before a gate review — does not
  represent genuine evidence currency and should be investigated.

### What you see

For each artefact the platform returns a currency status:

| Status | What it means |
|--------|---------------|
| Current | The artefact has been updated within the acceptable window and was not updated immediately before the gate. |
| Outdated | The artefact has not been updated within the acceptable window.  It may not reflect the current state of the project. |
| Anomalous Update | The artefact was updated within a very short window before the gate date.  This is consistent with last-minute compliance updates and should be reviewed before accepting the evidence. |

### Configurable thresholds

| Setting | Default | Meaning |
|---------|---------|---------|
| Maximum staleness | 90 days | Artefacts not updated within this window are flagged as Outdated. |
| Anomaly window | 3 days | Updates this close to the gate date are flagged as Anomalous. |

### Example prompts

- "Check the currency of the evidence artefacts submitted for PROJ-001 against
  the June gate date."
- "Which artefacts for PROJ-001 were last updated more than 90 days ago?"
- "Were any documents updated within 3 days of the gate for PROJ-001?"

---

## Longitudinal Compliance Tracker

### What it does

Every time your project data is validated against the NISTA Programme and
Project Data Standard, the score is saved.  Over time this builds a history
that the platform uses to answer three questions:

- Is the score going up, staying flat, or going down?
- Has the score dropped sharply between two consecutive validation runs?
- Has the score fallen below an acceptable minimum?

### What you see

When you ask for a compliance trend report, the platform returns:

- **History**: a list of every validation run with its date and score.
- **Trend**: one of three values.

  | Trend | What it means |
  |-------|---------------|
  | Improving | Scores have risen meaningfully over recent runs. |
  | Stagnating | Scores are broadly flat — neither improving nor declining. |
  | Degrading | Scores have fallen meaningfully over recent runs. |

- **Active breaches**: any alert conditions that are currently triggered.

  | Breach | What it means |
  |--------|---------------|
  | Drop breach | The score fell by more than the configured tolerance between the last two runs.  This can signal a data quality problem that needs immediate attention. |
  | Floor breach | The score has fallen below the configured minimum.  This means the project data may not be sufficient for reporting purposes. |

### Configurable thresholds

Your programme office can adjust the alert thresholds to match your
organisation's tolerance for compliance risk:

| Setting | Default | Meaning |
|---------|---------|---------|
| Drop tolerance | 5 points | How large a single-run drop must be before an alert is raised. |
| Floor | 60% | The minimum compliance score before a floor alert is raised. |
| Stagnation window | 3 runs | How many recent runs are examined when computing the trend. |

### Example prompts

- "Show me the NISTA compliance trend for project PROJ-001."
- "Have there been any threshold breaches for PROJ-001 recently?"
- "Is PROJ-001's compliance score improving or degrading over time?"

---

## Cross-Cycle Finding Analyzer

### What it does

When you submit a project review document to the platform, it automatically:

1. Reads every recommended action from the text.
2. Removes any duplicates within the same review.
3. Checks whether any of the new actions match open actions from a previous
   review cycle.
4. Saves all actions to a shared record so they can be tracked over time.

### Review action lifecycle

Every action has a status:

| Status | Meaning |
|--------|---------|
| Open | Newly identified; no action taken yet. |
| In progress | Work is under way to address this action. |
| Closed | The action has been resolved. |
| Recurring | This action has appeared in a previous review and was not yet closed.  Recurring actions are a signal that something is not being addressed. |

### What "recurring" means in practice

If the platform identifies that an action in your Q2 review is essentially the
same as an open action from your Q1 review, the Q2 action is automatically
flagged as recurring.

Recurring actions are a management signal.  They suggest that either the action
has not been taken yet, or that the underlying issue is proving difficult to
resolve.  Your programme or assurance manager should investigate why the action
has not been closed.

### Confidence and human review flags

The platform extracts review actions using an AI model with a self-consistency
check (it runs the extraction several times and looks for agreement).  Each
extraction is given a confidence score.

If the confidence score is below a configured threshold (default: 60%), the
action is flagged for human review.  It is still recorded and included in the
results — it is never automatically discarded.  A flag means "a human should
check this before acting on it", not "this is wrong".

### Example prompts

- "Extract the actions from this review document and track them against our
  open actions for PROJ-001."
- "Show me all open review actions for PROJ-001."
- "Which actions for PROJ-001 are recurring from previous reviews?"

---

## Using these features through Claude

All three features are available as tools in the pm-assure MCP server.  You
can use them by asking Claude directly in a conversation where the server is
connected.

**Artefact Currency Validator:**

- "Check whether the evidence artefacts for PROJ-001 are current for the
  June gate."
- "Flag any documents for PROJ-001 that were updated within 3 days of the
  gate date."

**Longitudinal Compliance Tracker:**

- "Show me the NISTA compliance trend for project PROJ-001."
- "Have there been any threshold breaches for PROJ-001 recently?"

**Cross-Cycle Finding Analyzer:**

- "Extract the recommendations from this review document and track them
  against our open actions for PROJ-001."
- "Show me all open review actions for PROJ-001."
- "Which actions for PROJ-001 are recurring from previous reviews?"

---

## Frequently asked questions

**Do I need to do anything to start tracking compliance scores?**

No.  Score tracking begins automatically the first time your project data is
validated through the platform with the history feature enabled.  Contact your
programme office or technical team if you are unsure whether it is active.

**How many reviews does the platform need before it can show a compliance trend?**

At least two validation runs are needed before a trend can be computed.  With
only one run, the trend is shown as Stagnating until more data is available.

**What counts as an anomalous artefact update?**

An update is flagged as anomalous when it occurs within the configured anomaly
window (default: 3 days) before a gate date.  The platform does not assess
whether the content changed; it flags the timing pattern for human review.
Your assurance manager should compare the current version of the document
against the previous version to determine whether the update represents a
genuine revision.

**Can I mark a review action as closed myself?**

Yes.  Your programme office or platform administrator can update the status of
any action using the review action management tools.

**What happens if the AI misses a recommendation?**

Extraction is run multiple times and the results are compared for consistency.
Low-agreement extractions are flagged for review.  As with any AI-assisted
tool, a human reviewer should check the output before using it for formal
reporting purposes.

**Is review action text stored securely?**

Review action text is stored in a local SQLite database on the server where
the platform is running.  The same data security controls that apply to your
other project management data apply here.  Talk to your information security
team if you have specific requirements.

---

## Confidence Divergence Monitor

### What it does

When the platform extracts review findings from project documents it does so
multiple times and compares the results.  The Confidence Divergence Monitor
watches for three warning signs in those extractions:

- **High divergence**: individual extraction runs disagree significantly with
  each other, meaning the source text is ambiguous or unclear.
- **Low consensus**: the overall agreement score across all runs is below the
  acceptable minimum, regardless of how spread the individual runs are.
- **Degrading confidence**: the agreement score has been falling across
  consecutive review cycles for the same project, suggesting the project
  situation is becoming harder to interpret or that review quality is declining.

### What you see

Each check produces one of four signals:

| Signal | What it means |
|--------|---------------|
| Stable | All extraction runs are in agreement.  No action required. |
| High Divergence | Individual runs disagree beyond the acceptable spread.  The extraction output should be reviewed by a human before being relied upon. |
| Low Consensus | The overall agreement score is too low, even if individual runs look reasonable.  Treat outputs as indicative only. |
| Degrading Confidence | Agreement has declined across recent cycles.  This is a trend warning — investigate whether review document quality is declining. |

### Why it matters

When confidence is low or diverging, it is a signal about the *quality of the
input documents*, not a failure of the platform.  It means the project review
text contains ambiguities or inconsistencies that make extraction unreliable.
The appropriate response is to ask the project team to clarify the source
document.

### Configurable thresholds

| Setting | Default | Meaning |
|---------|---------|---------|
| Divergence threshold | 0.30 | Maximum acceptable spread across sample scores. |
| Minimum consensus | 0.60 | Minimum acceptable overall agreement score. |
| Degradation window | 3 cycles | How many consecutive cycles are checked for a declining trend. |

### Example prompts

- "Check the confidence divergence for the latest extraction on PROJ-001."
- "Has the extraction confidence for PROJ-001 been declining recently?"
- "Flag any reviews for PROJ-001 where samples disagreed significantly."

---

## Adaptive Review Scheduler

### What it does

Most programmes schedule gate reviews on a fixed calendar — every six weeks,
every quarter, or at prescribed stage boundaries.  This creates two failure
modes: stable, low-risk projects get reviewed too often (wasting assurance
resource), and deteriorating projects may not get reviewed soon enough.

The Adaptive Review Scheduler analyses the outputs from the four preceding
checks — artefact currency, compliance trend, review action closure, and
extraction confidence — and recommends *when* the next review should happen
based on what those signals are actually saying about the project.

### What you see

The recommendation has four urgency levels:

| Urgency | Timing | Trigger |
|---------|--------|---------|
| Immediate | Within 1 week | Multiple critical signals, or any single severely critical signal |
| Expedited | Within 2 weeks | At least one significant signal (stale artefacts, degrading compliance, many recurring actions) |
| Standard | Normal cadence (default: 6 weeks) | No significant signals |
| Deferred | Extended cadence (default: 12 weeks) | All signals stable or improving — project can safely wait longer |

Along with the urgency level and a recommended date, the platform returns a
plain-language rationale explaining which signals drove the recommendation.

### Example: how signals combine

If a project has:
- Two artefacts flagged as anomalous updates (P1 signal)
- A degrading compliance trend (P2 signal)
- Three recurring open actions (P3 signal)

…the scheduler will likely recommend **Immediate** or **Expedited** review
because multiple concerning signals are present simultaneously.

Conversely, if compliance has been improving for three consecutive cycles, all
artefacts are current, and all actions from the last review are closed, the
scheduler may recommend **Deferred** — saving assurance resource for projects
that need it more.

### Example prompts

- "When should the next review be scheduled for PROJ-001?"
- "Is PROJ-001 due for a review soon based on its current signals?"
- "What is driving the review urgency recommendation for PROJ-001?"

---

## Override Decision Logger

### What it does

Sometimes a governance board makes a decision that goes against assurance
advice: proceeding past a failed gate, accepting a risk that was flagged for
mitigation, or overriding a RAG rating.  These decisions are legitimate —
governance bodies exist precisely to exercise judgement in ambiguous
situations — but they are rarely captured in a structured way.

Without a record of override decisions, it is impossible to:
- Demonstrate accountability if the decision is later questioned.
- Identify patterns (for example, the same gate being overridden repeatedly).
- Track whether an override turned out to be the right call.

The Override Decision Logger captures these decisions with structured
information including who authorised it, what rationale was given, and what
conditions were attached.

### Types of override

| Type | What it covers |
|------|---------------|
| Gate Progression | Proceeding past a failed or red-rated gate |
| Recommendation Dismissed | Dismissing a specific assurance recommendation |
| RAG Override | Changing a RAG rating against the assessor's advice |
| Risk Acceptance | Accepting a risk that was flagged for mitigation |
| Schedule Override | Overriding a recommended review schedule |

### Tracking outcomes

Each override can be updated later with an outcome once the consequences become
clear:

| Outcome | Meaning |
|---------|---------|
| No Impact | The override had no adverse effect |
| Minor Impact | A small, manageable consequence occurred |
| Significant Impact | A notable consequence occurred that required attention |
| Prevented Benefit | The override blocked a positive outcome |

Tracking outcomes over time builds an evidence base for understanding when
governance overrides are well-founded and when they are not.

### Pattern analysis

The platform can analyse the override history for a project and identify:
- Which override type is most common.
- Whether the same issue is being overridden repeatedly.
- What proportion of overrides had adverse outcomes.

This information is valuable for programme reviews and for the assurance
manager's quarterly report.

### Example prompts

- "Log a gate progression override for PROJ-001 — the board agreed to proceed
  despite the amber-red rating.  Authorised by the SRO, rationale: critical
  business deadline."
- "Show me all override decisions for PROJ-001."
- "How many overrides for PROJ-001 resulted in a significant impact?"
- "Are there any patterns in the override history for PROJ-001?"

---

## Lessons Learned Knowledge Engine

### What it does

Every project generates lessons — things that went well, things that went
badly, and things that would be done differently next time.  Most organisations
collect these lessons diligently at project close but then struggle to make
them available at the point of decision-making on future projects.

The Lessons Learned Knowledge Engine provides a structured way to:
- Record lessons with rich contextual metadata (project type, phase,
  department, category, tags).
- Search for lessons relevant to a current situation using plain-language
  queries.
- Surface lessons from similar projects when a team is facing a familiar
  challenge.

### Lesson categories

Each lesson is tagged with the domain it relates to:

| Category | Examples |
|----------|---------|
| Governance | Board structures, decision-making delays, accountability gaps |
| Technical | Architecture decisions, integration failures, technical debt |
| Commercial | Procurement missteps, supplier performance, contract issues |
| Stakeholder | Engagement failures, conflicting requirements, communication breakdowns |
| Resource | Staffing shortages, skills gaps, capacity issues |
| Requirements | Scope creep, poor change control, unclear requirements |
| Estimation | Schedule optimism, cost underestimation, contingency shortfalls |
| Risk Management | Unidentified risks, inadequate mitigation, risk transfer failures |
| Benefits Realisation | Benefit measurement failures, dependency mis-tracking |
| Other | Lessons that don't fit the above categories |

### Lesson sentiment

Each lesson is also marked as:

| Sentiment | Meaning |
|-----------|---------|
| Positive | Something that worked well and should be repeated |
| Negative | Something that went wrong and should be avoided |
| Neutral | An observation without a clear positive or negative valence |

### Searching lessons

The engine supports two search modes:

- **Keyword search**: Matches words across the lesson title, description, and
  tags.  Fast and requires no additional setup.
- **Semantic search**: Uses a language model to find lessons that are
  *conceptually* similar, even if different words are used.  Requires the
  optional semantic search package to be installed.

### Example prompts

- "Search for lessons about stakeholder engagement on infrastructure projects."
- "What lessons do we have about procurement on PROJ-001?"
- "Add a lesson from PROJ-001: early supplier engagement reduced procurement
  delays significantly."
- "Show all negative lessons about requirements management."

---

## Assurance Overhead Optimiser

### What it does

Assurance activities consume project time, budget, and senior attention.
Without measurement, organisations cannot tell whether they are investing too
much (redundant reviews that add overhead without improving outcomes) or too
little (missing real issues that surface later as expensive problems).

The Assurance Overhead Optimiser tracks every assurance activity — gate
reviews, document reviews, compliance checks, audits — and analyses the effort
invested against the outcomes achieved.  It identifies:

- **Duplicate artefact reviews**: the same document being reviewed across
  multiple activities without new findings.
- **Zero-finding reviews**: reviews that consumed significant effort but found
  nothing.
- **Activities with no measurable confidence impact**: reviews that did not
  change the project's confidence score in either direction.

### Activity types tracked

| Activity | Examples |
|----------|---------|
| Gate Review | Stage gate, delivery readiness review |
| Document Review | Risk register review, benefits profile review |
| Compliance Check | NISTA validation run, data quality check |
| Risk Assessment | Risk identification workshop, risk scoring |
| Stakeholder Review | Senior Responsible Owner review, board presentation |
| Audit | Independent programme review, IPA deep dive |

### Efficiency rating

After analysing all activities for a project, the platform returns an overall
efficiency rating:

| Rating | Meaning |
|--------|---------|
| Efficient | Effort is proportionate to findings and confidence outcomes |
| Moderate | Some waste is present but the overall investment is reasonable |
| Inefficient | Significant redundant effort detected — review the assurance plan |

### What you see

A full overhead analysis includes:
- Total hours invested across all activities.
- Average findings per hour.
- A list of specific wasteful patterns with the activities involved.
- Recommended actions to reduce overhead.

### Example prompts

- "Log a gate review for PROJ-001: Stage 3 readiness, 16 hours, 4
  participants, 3 findings."
- "Analyse the assurance overhead for PROJ-001."
- "Are there any duplicate artefact reviews in the assurance history for
  PROJ-001?"
- "What is the efficiency rating for assurance activities on PROJ-001?"

---

## Assurance Workflow Engine

### What it does

The seven features described above (P1–P8, excluding P9 and P10) can each be
run individually.  The Assurance Workflow Engine runs them in a coordinated
sequence so that the outputs of earlier steps automatically feed into later
ones.  In particular, the review schedule recommendation (P5) automatically
uses the currency scores, compliance trend, action closure rates, and confidence
divergence produced by P1–P4 in the same workflow run.

### Workflow types

Choose the workflow type that matches what you need to know:

| Workflow | Steps included | Use when |
|----------|---------------|----------|
| Full Assurance | All steps (P1–P8) | Comprehensive review at a gate or programme milestone |
| Risk Assessment | P1, P2, P3, P4, P5 | You need a scheduling recommendation with full signal input |
| Compliance Focus | P2, P5, P6 | Your primary concern is compliance trends and override patterns |
| Trend Analysis | P2, P3, P5 | You want to understand how actions and scores are trending |
| Currency Focus | P1, P5 | You only need to check artefact currency and scheduling |

### Overall health

At the end of every workflow run the platform produces an overall health
classification for the project:

| Health | Meaning |
|--------|---------|
| Healthy | No significant signals detected |
| Attention Needed | Minor signals present — monitor closely |
| At Risk | Moderate signals — consider escalation |
| Critical | Severe signals — immediate action required |

### What you see

A workflow result contains:
- The health classification and a plain-language executive summary.
- The result of each step that ran, including any signals it produced.
- A list of all risk signals sorted by severity.
- A list of recommended actions.

If a step cannot run because the required data is not yet in the store (for
example, no compliance scores have been recorded yet), it is marked as
Not Applicable and the workflow continues with the remaining steps.

### Example prompts

- "Run a full assurance workflow for PROJ-001."
- "Run a risk assessment workflow for PROJ-001 and tell me when the next review
  should be."
- "What is the overall health of PROJ-001?"
- "Show me the workflow history for PROJ-001."

---

## Project Domain Classifier

### What it does

Not all projects need the same type or frequency of assurance.  A low-complexity
project with stable requirements and an experienced team needs different
governance from a high-complexity project with significant organisational change
and novel technical risk.  Applying the same assurance approach to both is
either too burdensome (for the simple project) or insufficient (for the complex
one).

The Project Domain Classifier places a project into one of four complexity
domains and returns a tailored assurance profile with recommended review
frequency and appropriate toolset.

### The four domains

| Domain | Description | Default review frequency |
|--------|-------------|--------------------------|
| Clear | Low complexity.  Stable requirements, proven approach, experienced team. Best practices apply directly. | Every 90 days |
| Complicated | Moderate complexity.  Specialist input and expert analysis needed, but cause and effect are understood. | Every 60 days |
| Complex | High complexity.  Emergent behaviour, significant organisational change, adaptive management required. | Every 42 days |
| Chaotic | Crisis state.  Novel situation requiring immediate stabilisation. | Every 14 days |

### What the classifier uses

**Explicit indicators** — information you provide directly about the project:

| Indicator | What it measures |
|-----------|----------------|
| Technical complexity | How novel or intricate the technology is |
| Stakeholder complexity | How many diverse stakeholders are involved |
| Requirement clarity | How well-defined requirements are (higher clarity = lower complexity) |
| Delivery track record | The team's past success rate (higher track record = lower complexity) |
| Organisational change | How much change the project requires of the organisation |
| Regulatory exposure | Level of regulatory or compliance scrutiny |
| Dependency count | Number of external dependencies (expressed as a score 0–1) |

Note: Requirement clarity and delivery track record are *inverse* indicators —
a high score on these reduces the complexity classification, because a well-
specified project with an experienced team is less complex, not more.

**Store-derived signals** — information the platform draws automatically from
its history for the project:

| Signal | Drawn from |
|--------|-----------|
| Compliance trend | P2 — whether NISTA scores are degrading |
| Recurring actions | P3 — proportion of review actions that recur across cycles |
| Override rate | P6 — frequency of governance override decisions |
| Overhead efficiency | P8 — whether assurance overhead is inefficient |

You do not need to provide all indicators.  If only some are available, the
classifier adjusts its weights accordingly.

### Assurance profile

Along with the domain classification, the platform returns a recommended
assurance profile:

- **Review frequency**: how often the project should be reviewed.
- **Recommended toolset**: which assurance features are most relevant for this
  domain.
- **Governance intensity**: the level of governance oversight recommended.
- **Description**: a plain-language explanation of what this domain means for
  the project.

### Reclassification

If you want the classifier to re-run using only the signals already in the
store (without providing any new explicit indicators), use the reclassify
option.  This is useful for periodic re-assessment as new data accumulates.

### Example prompts

- "Classify the complexity domain for PROJ-001.  Technical complexity is
  medium-high (0.7), stakeholder complexity is high (0.8), requirement
  clarity is low (0.3)."
- "What domain is PROJ-001 classified in?"
- "Reclassify PROJ-001 based on its current store signals."
- "How often should PROJ-001 be reviewed based on its domain?"
- "What assurance tools are recommended for a Complex domain project?"

---

## Using all ten features together

The ten features form a layered assurance capability:

| Layer | Features | Purpose |
|-------|---------|---------|
| Evidence quality | P1 — Artefact Currency, P4 — Confidence Divergence | Is the evidence reliable? |
| Compliance trajectory | P2 — Longitudinal Compliance | Is the project's data quality improving? |
| Action management | P3 — Cross-Cycle Finding Analyzer | Are recommendations being acted on? |
| Scheduling | P5 — Adaptive Review Scheduler | When should the next review happen? |
| Governance | P6 — Override Decision Logger | Are governance decisions being recorded? |
| Organisational learning | P7 — Lessons Learned | Are we learning from the past? |
| Efficiency | P8 — Assurance Overhead | Is assurance time being well spent? |
| Orchestration | P9 — Workflow Engine | Run everything in a coordinated sequence |
| Profiling | P10 — Domain Classifier | Is the right type of assurance being applied? |

For a first-time setup, a recommended starting sequence is:

1. Run the **Project Domain Classifier** (P10) to understand what level of
   assurance intensity is appropriate.
2. Start recording **NISTA compliance scores** (P2) at each validation run.
3. After each gate review, **extract and track review actions** (P3).
4. Before scheduling the next review, run the **Adaptive Review Scheduler**
   (P5) using the accumulated signals.
5. When comfortable, run a **full assurance workflow** (P9) to get a complete
   picture in one step.

---

## Frequently asked questions (continued)

**Do I need to use all ten features?**

No.  Each feature works independently.  You can start with the three features
described at the beginning of this guide and add more as your team becomes
comfortable with the platform.

**Can I run a workflow if I have not yet accumulated much data?**

Yes.  Steps that cannot run because required data is absent are marked as Not
Applicable and the workflow continues.  The result will note which steps had
insufficient data so you know what to collect for future runs.

**How does the Domain Classifier decide if a project is Complex vs Complicated?**

The classifier combines all available indicators into a composite score between
0 and 1.  Scores below 0.25 map to Clear, 0.25–0.50 to Complicated,
0.50–0.75 to Complex, and 0.75 and above to Chaotic.  You do not need to worry
about the exact score — the platform returns the domain label and the
recommended profile.

**What happens when a governance override is logged?**

The override is saved to the platform store with the decision date, type,
authoriser, and rationale.  It immediately becomes part of the project's history
and will appear in override pattern analysis and contribute to the Domain
Classifier's store-derived signals.  Nothing is automatically sent to anyone —
the platform records information but does not trigger notifications.

**Can the Lessons Learned Engine search across multiple projects?**

Yes.  If you ask for lessons without specifying a project, the search covers the
entire lessons corpus — all projects in the store.  This is the most useful mode
when looking for lessons relevant to a new project that is just starting.

**Is the Workflow Engine the same as an AI agent?**

No.  The Workflow Engine is deterministic — it runs the same steps in the same
order every time, with no AI decision-making about what to do next.  It is a
structured pipeline, not an autonomous agent.  This means it is fully
reproducible and auditable.

---

## P11 — Assumption Drift Tracker

Every project runs on assumptions: that a third-party system will be delivered on
time, that a key resource will remain available, that regulatory approval will
follow the expected timeline. When those assumptions are no longer true, the project
is exposed to risk. The Assumption Drift Tracker monitors whether assumptions are
holding.

**What it does**

You register an assumption at the point it is made — with a description and the
baseline state it represents. At each review, you validate the assumption by
recording what the current state actually is. The platform computes whether the
assumption is still valid, how far it has drifted from baseline, and what would be
affected if it failed.

**Three tools:**

- *Ingest an assumption* — register a new assumption with baseline
- *Validate an assumption* — record a check and mark whether it still holds
- *Get assumption drift* — retrieve all assumptions and their current drift status

**Why it matters**

Assumption failure is one of the most common causes of project overruns. Projects
that track assumptions formally catch emerging problems earlier and have a documented
record for gateway reviews.

**Example prompts:**

> "Register this assumption for project ALPHA-01: 'The legacy database migration
> will complete by Q2.' The baseline state is 'migration not yet started'."

> "Validate the assumption we registered last month. The current state is: the
> migration is six weeks behind schedule."

> "Show me all assumptions for project ALPHA-01 and flag any that are drifting."

---

## P12 — Agent Readiness Maturity Model (ARMM)

The Agent Readiness Maturity Model assesses how ready a project or programme is
to deploy AI agents in its delivery. It evaluates 251 criteria across 28 topics
in four dimensions: data readiness, process maturity, governance structures, and
technical infrastructure. The result is a maturity level from 1 (initial) to 5
(optimised).

**What it does**

You ask Claude to run an ARMM assessment for a project. The platform analyses
available data in the assurance store and produces a structured report with your
maturity level per dimension, a breakdown of which criteria are met and which are
not, and prioritised recommendations for improvement.

**When to use it**

ARMM is most useful when your organisation is planning to introduce AI-assisted
project management, or when responding to OGP or IPA questions about AI governance
in major project delivery.

**Example prompt:**

> "Run an ARMM assessment for project DELTA-02 and tell me what level we are at,
> and what the biggest gaps are."

---

## P13 — Benefits Realisation Management

Benefits are why projects exist. The Benefits Realisation Management module (P13)
gives project teams a structured, IPA and Green Book-compliant way to register,
track, and report on the benefits their project is expected to deliver — from initial
identification through to post-project review.

Benefits are classified using three frameworks simultaneously:

- **Green Book financial type** — cash-releasing, non-cash-releasing, quantifiable,
  or qualitative
- **IPA recipient type** — government, private sector, or wider UK public
- **Ward and Daniel explicitness** — financial, quantifiable, measurable, or observable

**Core capabilities:**

- Register benefits and dis-benefits with full metadata
- Record measurements over time and compute drift from baseline
- Map benefits in a dependency network (DAG) connecting project outputs to
  strategic objectives
- Detect drift using time-series analysis — ordered by severity
- Forecast realisation probability using current trajectory
- Identify cascade impacts through the dependency network
- Generate IPA-compliant gate review narratives (with AI confidence scoring)
- Score benefits management maturity against P3M3 criteria (Levels 1–5)

**Example prompts:**

> "Register a benefit for project BETA-03: 'Reduction in manual processing time',
> financial type QUANTIFIABLE, recipient GOVERNMENT, baseline 40 hours per week,
> target 8 hours per week by March 2027."

> "Record a measurement for that benefit — we measured 32 hours per week last month."

> "Show me the benefits health for project BETA-03. Which benefits are at risk?"

> "Generate an IPA benefits assurance narrative for project BETA-03 for Gate 3."

> "What is the benefits maturity score for project BETA-03?"

For full documentation, see [Benefits Realisation Reference](brm.md) and the
[Benefits Practitioner Guide](brm-for-practitioners.md).

---

## P14 — Gate Readiness Assessor

Gate reviews are high-stakes events. The Gate Readiness Assessor (P14) synthesises
all available assurance signals — from P1 through P13 — into a single composite
readiness score, broken down by eight assessment dimensions with gate-specific
weighting.

**The eight dimensions:**

| Dimension | What it measures |
|-----------|-----------------|
| Artefact readiness | Are all required artefacts current and complete? |
| Compliance trajectory | Is NISTA compliance improving? |
| Assumption integrity | Are assumptions still valid? |
| Confidence quality | Is AI extraction consistent and high-confidence? |
| Governance | Are override decisions being documented? |
| Learning | Is the project drawing on lessons from past reviews? |
| Benefits maturity | Are benefits being tracked and realised? |
| Domain alignment | Is the assurance approach appropriate for the project's complexity? |

Each dimension is weighted differently depending on the gate type. Early gates
(0, 1) weight assumptions and governance heavily. Later gates (3, 4, 5) weight
artefact completeness and benefits evidence more.

**Four readiness levels:**

- **READY** — All blocking issues resolved; proceed with confidence
- **CONDITIONALLY READY** — Minor gaps; proceed with named actions
- **AT RISK** — Significant gaps; review recommended before gate
- **NOT READY** — Blocking issues unresolved; gate submission not advised

**Example prompts:**

> "Run a gate readiness assessment for project GAMMA-01 at Gate 3."

> "Show me the gate readiness history for project GAMMA-01 — how has it
> progressed over the last three assessments?"

> "Compare the Gate 3 assessment from last month with this month's assessment
> for project GAMMA-01."

For full documentation, see [Gate Readiness Reference](gate-readiness.md) and the
[Gate Readiness Practitioner Guide](gate-readiness-for-practitioners.md).

---

## Using all fourteen features together

The fourteen features form a complete, layered assurance capability:

| Layer | Features | Purpose |
|-------|---------|---------|
| Evidence quality | P1, P4 | Is the evidence reliable and consistent? |
| Compliance trajectory | P2 | Is data quality improving over time? |
| Action management | P3 | Are review findings being addressed? |
| Scheduling | P5 | When is the next review needed? |
| Governance | P6 | Are override decisions documented? |
| Organisational learning | P7 | Are we learning from past projects? |
| Efficiency | P8 | Is assurance effort well spent? |
| Orchestration | P9 | Run P1–P8 in a coordinated sequence |
| Profiling | P10 | Is the right intensity of assurance applied? |
| Assumption tracking | P11 | Are underlying assumptions still holding? |
| AI readiness | P12 | Is the project ready for AI-assisted delivery? |
| Benefits tracking | P13 | Are expected benefits being realised? |
| Gate readiness | P14 | Is the project ready for its next gateway? |

## route_outputs_to_review — four-tier escalation

`route_outputs_to_review` applies the **four-tier escalation router** from
Verified Autonomy §5.3 to a project's stored assumption-confidence outputs.
The router answers a specific governance question: **does this project's
output need human review before it reaches a board or gate panel, and at
what intensity?**

The four tiers are:

| Tier | Trigger | What happens |
|------|---------|--------------|
| `EXPERT_REQUIRED` | Any statistical outlier in the inputs **OR** overall confidence below 0.4 | Route to a domain expert. The output is not acted upon until reviewed. |
| `DETAILED_REVIEW` | No outliers AND confidence in [0.4, 0.6) | A human reads every output in this tier before action. |
| `SPOT_CHECK` | No outliers AND confidence in [0.6, 0.8) | Periodic sampling — a proportion are reviewed. |
| `NONE` | No outliers AND confidence ≥ 0.8 | Auto-process without human review. |

The crucial property is the **OR fail-safe**: outliers OR low confidence each
**independently** trigger escalation.  A project with strong overall confidence
but a single anomalous assumption still routes to expert review — because the
anomaly is exactly the kind of thing optimism-bias screens are designed to
catch.  Only the AND-clean path (no outliers, high confidence) gets to
auto-process.

### Worked example

```
route_outputs_to_review —
  project_id: "PRJ-ALPHA"
```

The tool reads the project's stored confidence scores (one per assumption,
populated by `score_assumption_confidence`), normalises them to `[0, 1]`,
computes the overall confidence, and returns a `RoutingDecision`.  A typical
response:

```json
{
  "level": "EXPERT_REQUIRED",
  "reason": "EXPERT_REQUIRED: 1 statistical outlier(s) detected. Confidence 0.82 alone would not have escalated, but the OR fail-safe routes any outlier to a domain expert.",
  "consensus": 0.84,
  "confidence": 0.82,
  "outliers": [
    {"field": "confidence", "consensus_value": 0.84, "outlier_value": 0.15,
     "sample_index": 4, "divergence_score": 4.3,
     "reason": "PRJ-ALPHA-A005: 4.3x IQR below the consensus of 0.84"}
  ],
  "triggered_by_outliers": true,
  "triggered_by_confidence": false,
  "thresholds_used": [0.4, 0.6, 0.8],
  "sample_size": 7
}
```

The reviewer reads this and goes straight to assumption `A005` — the one
that fired the OR clause — rather than scanning the whole assumption
register.

### Override the overall confidence

When you want to test the routing logic independently of the stored scores
(for example, you've taken a board-level decision that the project's
overall confidence is 0.95 regardless of the assumption-level scores):

```
route_outputs_to_review —
  project_id: "PRJ-ALPHA"
  confidence_override: 0.95
```

The OR fail-safe still fires on outliers, so if the assumption register has
any single outlier the project still routes to `EXPERT_REQUIRED`.  This is
deliberate — it's the kind of governance failure-mode the layer is designed
to catch.

### When to use

- Before promoting a project's reports to a board pack: route first to
  confirm whether expert review is required.
- As part of the IPA Gate Review run-up: integrate into the assurance
  workflow so the gate panel sees the routing decision alongside the
  technical findings.
- Periodically across the portfolio: identify which projects need the most
  intensive review intensity this cycle.

### Limitations

- Requires `score_assumption_confidence` to have been run for the project.
  Without stored confidence scores, the tool returns a structured
  `NO_CONFIDENCE_HISTORY` error rather than attempting to route.
- The thresholds (0.4 / 0.6 / 0.8) are paper §5.3 defaults; they can be
  overridden per call but should be agreed at portfolio level rather than
  tuned per-project to avoid gaming.
- Outlier detection uses IQR (Tukey's fence at 1.5 × IQR by default).
  Heavy-tailed confidence distributions may need a wider multiplier — pass
  through configurable thresholds if needed.
