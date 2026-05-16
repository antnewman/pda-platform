# Project Analysis — A Guide for Project Managers and Programme Leads

This guide explains the six analytical tools available in the pm-analyse module
of PDA Platform.  No technical background is needed.  It is written for project
managers, programme leads, and senior responsible owners who want to use these
tools through a Claude conversation.

---

## What is pm-analyse for?

Every project generates signals — schedule performance data, cost actuals,
resource assignments, task progress — that, taken individually, can look
unremarkable.  Taken together, and analysed systematically, those same signals
can reveal risks before they become problems, forecast where a project is
heading, and surface data quality issues that would otherwise distort reporting.

The pm-analyse module provides six tools that do exactly that:

1. **identify_risks** — Identifies risks across eight dimensions before they
   surface through normal monitoring.
2. **forecast_completion** — Forecasts when the project will complete, using
   multiple methods and expressing uncertainty honestly.
3. **detect_outliers** — Finds tasks and data points that are statistically
   unusual and may indicate data entry errors or emerging problems.
4. **assess_health** — Produces a scored, multi-dimensional health picture of
   the project across schedule, cost, scope, resource, and quality.
5. **suggest_mitigations** — Generates specific mitigation strategies for
   identified risks, with effort estimates and residual risk levels.
6. **compare_baseline** — Compares the current plan against the original and
   approved baselines to quantify drift and support accountability.

---

## The prerequisite: loading your project

Before using any pm-analyse tool, you must load your project data into the
session using the `load_project` tool from the pm-data module.  Without this
step, the analysis tools have no schedule or cost data to work with.

Ask Claude:

- "Load project PROJ-001 so I can run some analysis."
- "Load the data for PROJ-001 from the project store."

Once the project is loaded, you can run any of the six tools described in this
guide without needing to load the project again in the same conversation.

---

## Understanding the analysis workflow

The six tools are designed to complement each other.  Used in combination, they
provide a coherent picture rather than isolated metrics.

| Tool | Feeds into |
|------|-----------|
| identify_risks | suggest_mitigations — risks identified here are referenced by ID when requesting mitigations |
| assess_health | itself over time — run repeatedly to track whether health is improving, stable, or declining |
| forecast_completion | gate review preparation — provides the predicted completion date and scenarios needed for a programme board |
| detect_outliers | data quality decisions — outliers should be investigated and corrected before running forecast or health assessments |
| compare_baseline | accountability and governance — variance against baseline informs SRO and programme board decisions |

The recommended order for a thorough pre-gate analysis is:

1. detect_outliers (clean data quality issues first)
2. identify_risks (understand the risk landscape)
3. forecast_completion (understand where the project is heading)
4. assess_health (get the multi-dimensional scored picture)
5. compare_baseline (quantify drift from the approved plan)
6. suggest_mitigations (generate actions for the risks identified in step 2)

You do not need to run all six every time.  For a quick health check, running
assess_health alone is sufficient.  For a gate review, running all six gives the
most complete evidence base.

---

## identify_risks

### What it does

This tool analyses your project data and identifies risks across eight
dimensions: schedule, cost, resource, scope, technical, external, organisational,
and stakeholder.  For each risk it finds, it returns a probability score (how
likely the risk is to materialise), an impact score (how severe the consequence
would be if it did), and a confidence score (how certain the analysis is).

It does not simply flag what is already red on a RAG report.  It looks for
patterns — combinations of data points — that together indicate an emerging
risk, even when no single indicator is yet at a concerning level.

### When to use it

- At the start of a project phase, to establish the risk baseline for that phase.
- Before a gate review, to ensure the risk register reflects the current
  analytical picture rather than only risks the team has already noticed.
- When the schedule has been substantially replanned, to check whether the
  replan has introduced new risk patterns.
- Periodically during delivery, to catch emerging risks early.

### Depth settings

| Depth | What it does | When to use it |
|-------|-------------|----------------|
| quick | Screening pass across all eight dimensions.  Faster, focuses on the most prominent signals. | Weekly check-ins; initial triage when time is short |
| standard | Normal analysis depth.  Examines patterns within each dimension and across dimensions. | Most situations; routine gate preparation |
| deep | Comprehensive analysis including dependency chains — risks that could cascade through the schedule.  Slower. | Before a major gate; after a significant replan; when the project is in an amber or red state |

### Example prompts

- "Identify risks for PROJ-001 at standard depth."
- "Run a deep risk identification for PROJ-001 before the Gate 3 review."
- "Do a quick risk scan for PROJ-001 to check whether anything new has come up
  this week."
- "Identify risks in just the schedule and resource dimensions for PROJ-001."

### What the output means

Each identified risk includes:

- **Dimension** — which of the eight dimensions the risk belongs to.
- **Description** — a plain-language description of the risk pattern found.
- **Probability** — a score from 0 to 1.  0.7 means the analysis assesses a
  70% likelihood of materialisation if no action is taken.
- **Impact** — a score from 0 to 1.  Higher scores mean more severe
  consequences for the project.
- **Confidence** — how certain the analysis is about this risk.  A lower
  confidence score does not mean the risk should be ignored; it means the
  supporting evidence is less clear-cut and human judgement is more important.
- **Risk ID** — a reference used when requesting mitigations (see
  suggest_mitigations below).

### What to do with the results

Compare the identified risks against your existing risk register.  Risks that
appear in the analysis but are not already on the register should be reviewed
with your risk manager and, where appropriate, added.  Risks on the register
that the analysis does not surface may be adequately controlled — or they may
need re-examining.

Do not treat the probability and impact scores as definitive.  They are
analytical signals, not organisational decisions.  The decision about how to
classify and respond to any risk remains with your risk manager and SRO.

---

## forecast_completion

### What it does

This tool produces a forecast of when the project will complete, using up to
five methods and combining their outputs into a single predicted date.  Rather
than giving a single point estimate, it expresses the forecast as a range —
an optimistic scenario, a likely scenario, and a pessimistic scenario — so that
you can communicate uncertainty honestly to the programme board.

### Forecasting methods

| Method | How it works | When it is most reliable |
|--------|-------------|--------------------------|
| earned_value | Uses Earned Value Management metrics (SPI and CPI) to extrapolate from current performance. | When the project has consistent performance data over at least several reporting periods |
| monte_carlo | Runs thousands of simulated completions using the variability in your task duration data. | When you have enough historical task actuals to model variability accurately |
| reference_class | Compares your project to similar past projects and applies the statistical distribution of their outcomes. | When good reference data is available for comparable projects |
| simple_extrapolation | Extends the current trend in progress data forward to completion. | Quick estimates; cross-checking other methods |
| ml_ensemble | Combines all available methods, weighting them by their reliability for this project type. | Default setting; most accurate overall |

For most purposes, use the ml_ensemble method (the default).  The other methods
are useful when you want to understand why the ensemble is producing a particular
forecast, or when you need to show the programme board the range of analytical
approaches underpinning the prediction.

### Example prompts

- "Forecast the completion date for PROJ-001."
- "Run a Monte Carlo forecast for PROJ-001."
- "Show me the completion forecast for PROJ-001 using all available methods so
  I can compare them."
- "What is the optimistic, likely, and pessimistic completion date for PROJ-001?"

### What the output means

- **Predicted completion date** — the central forecast, expressed as a date.
- **Confidence interval** — the date range within which the project is expected
  to complete (for example, an 80% confidence interval means there is an 80%
  probability the project completes within that range).
- **Optimistic scenario** — the completion date under favourable conditions.
- **Likely scenario** — the most probable completion date.
- **Pessimistic scenario** — the completion date if current negative trends
  continue or worsen.
- **Method breakdown** — if the ensemble method is used, the weight given to
  each contributing method is shown.

### What to do with the results

Use the likely scenario as your primary planning figure.  Use the confidence
interval to express uncertainty to the programme board — it is more honest than
a single date with no range.  If the pessimistic scenario crosses a programme
milestone or contractual deadline, treat this as a risk requiring a mitigation
response.

If the optimistic and pessimistic scenarios are very far apart, this indicates
high uncertainty in the project data.  Running detect_outliers may reveal data
quality issues that are contributing to the wide range.

---

## detect_outliers

### What it does

This tool applies statistical anomaly detection to your task and schedule data,
looking for data points that are unusual enough to warrant investigation.  It
examines four types of anomaly:

| Type | What it looks for |
|------|------------------|
| Duration | Tasks whose planned or actual duration is unusually long or short compared to similar tasks in the project |
| Progress | Tasks reporting a percentage complete that is inconsistent with the time elapsed or the work remaining |
| Float | Tasks with suspicious zero or near-zero float — particularly where this appears to have been artificially introduced rather than arising naturally from dependencies |
| Dates | Tasks with constraint violations, dates set in the past that have not been updated, or date patterns inconsistent with the network logic |

Outliers are not necessarily errors.  Some tasks genuinely are unusually long,
or genuinely have zero float because of a hard constraint.  The tool surfaces
them for human review; it does not automatically correct anything.

### Sensitivity setting

The sensitivity parameter controls how aggressive the detection is.  It runs on
a scale from 0.5 to 2.0.

| Sensitivity | Behaviour | When to use |
|-------------|-----------|------------|
| 0.5 | Conservative — only the most extreme outliers are flagged | Large programmes where you want to focus only on clear anomalies |
| 1.0 | Default — standard statistical thresholds | Most situations |
| 2.0 | Aggressive — flags a wider range of unusual values | Before a gate review when you want to be thorough; when the forecast is behaving unexpectedly |

### Example prompts

- "Detect outliers in the PROJ-001 schedule data."
- "Run outlier detection for PROJ-001 at a higher sensitivity — I want to check
  for data quality issues before the gate review."
- "Are there any tasks in PROJ-001 with suspicious float values?"
- "Check PROJ-001 for tasks with unexpected progress percentages."

### What the output means

Each flagged item includes:

- **Task reference** — the task ID or name.
- **Anomaly type** — which of the four detection categories triggered the flag.
- **Description** — a plain-language explanation of what is unusual about this
  task.
- **Severity** — how statistically extreme the anomaly is.

### What to do with the results

Treat outliers as a list of questions to put to your planner or project
controls team, not as a list of confirmed errors.  For each flagged item, ask:
is there a genuine reason for this, or does it need correcting?  If data is
corrected, re-run detect_outliers to confirm the flags have cleared before
running forecast_completion or assess_health.

Running detect_outliers before a gate review is good practice.  Submitting
analysis to a gate that is based on data containing uncorrected anomalies
undermines the credibility of the evidence.

---

## assess_health

### What it does

This tool produces a scored health assessment across five dimensions: schedule,
cost, scope, resource, and quality.  Each dimension receives a score from 0 to
100.  The dimensions are combined — using configurable weights — into a single
overall score.

If you have run assess_health on the same project before, the tool can also
produce a trend analysis showing whether each dimension is improving, stable,
or declining since the previous assessment.

### Health dimensions

| Dimension | What it measures |
|-----------|----------------|
| Schedule | Progress against the plan — whether the project is on time or slipping |
| Cost | Expenditure against budget — whether the project is within its cost envelope |
| Scope | Control of the project scope — whether change is being managed or drifting |
| Resource | Availability and utilisation of people and other resources against what the plan requires |
| Quality | Indicators of delivery quality — defect rates, rework, review outcomes where available |

### Configurable weights

By default, all five dimensions are weighted equally.  If your programme has a
specific concern — for example, if cost control is the primary governance
priority — you can ask Claude to apply different weights.

Example: "Assess the health of PROJ-001 with double weighting on cost and
schedule."

### Example prompts

- "Assess the health of PROJ-001."
- "Run a health assessment for PROJ-001 and compare it to the last one."
- "What is the schedule health score for PROJ-001?"
- "Assess PROJ-001 health with higher weighting on resource and quality."
- "Is PROJ-001's health improving or declining?"

### What the output means

| Score range | Indicative meaning |
|-------------|-------------------|
| 80–100 | Healthy — no significant concerns in this dimension |
| 60–79 | Satisfactory — some areas to monitor but within acceptable bounds |
| 40–59 | Concerning — attention and action required |
| Below 40 | At risk — significant intervention needed |

These ranges are indicative.  Your programme may have its own thresholds for
translating scores into RAG ratings.

The trend analysis returns one of three values per dimension:

| Trend | Meaning |
|-------|---------|
| Improving | The score has risen meaningfully since the previous assessment |
| Stable | The score is broadly unchanged |
| Declining | The score has fallen meaningfully — this dimension warrants closer attention |

### What to do with the results

Use the overall score and dimension breakdown to inform your RAG rating and the
written narrative for the programme board.  Where dimensions are declining,
investigate the underlying cause before the next reporting cycle.  An overall
score that is stable but with one or two declining dimensions is a warning sign
that the aggregate figure is masking emerging problems.

---

## suggest_mitigations

### What it does

This tool generates specific, actionable mitigation strategies for risks that
have been identified.  You can reference a specific risk by its ID (from the
output of identify_risks) or ask for mitigations across a risk category.

For each mitigation it returns:

- **Mitigation approach** — a description of the proposed action.
- **Effectiveness rating** — an assessment of how much the mitigation is
  expected to reduce the risk, expressed as a score from 0 to 1.
- **Implementation steps** — a sequenced list of what needs to happen to put
  the mitigation in place.
- **Effort estimate** — a broad estimate of the time and resource needed to
  implement the mitigation.
- **Residual risk level** — the expected probability and impact of the risk
  after the mitigation has been implemented.

### Example prompts

- "Suggest mitigations for risk RISK-007 from the PROJ-001 analysis."
- "What can we do about the schedule risks identified for PROJ-001?"
- "Generate mitigation strategies for all resource risks on PROJ-001."
- "I need practical actions for the top three risks identified for PROJ-001.
  Keep the effort estimates realistic — this is a small team."

### What the output means

The effectiveness rating is not a guarantee.  It represents the analytical
assessment of how much the proposed mitigation would reduce exposure if
implemented as described.  Mitigations with a high effectiveness rating but high
effort may not be practical for all projects; the right response to a risk
depends on the project's circumstances and risk appetite.

The residual risk level shows what remains after mitigation.  If the residual
level is still high, consider whether an additional or alternative mitigation
is needed, or whether the risk needs to be formally accepted by the SRO.

### What to do with the results

Use the suggested mitigations as a starting point for discussion with your risk
manager and the risk owner.  They are AI-generated proposals, not directives.
The implementation steps need to be reviewed for feasibility against your
project's actual resources and constraints before being added to the risk
register as agreed actions.

---

## compare_baseline

### What it does

This tool compares the current project plan against two reference points: the
original baseline (as approved at the start of the project) and the most recent
approved baseline (which may have been re-baselined since).  It quantifies how
far the project has drifted from each and classifies the severity of the drift.

It examines:

- **Schedule slip** — how many days the forecast completion has moved against
  each baseline.
- **Duration change** — the percentage change in total planned duration.
- **Cost variance** — the difference in total project cost (in pounds and as a
  percentage).

Each variance is classified by severity:

| Severity | Meaning |
|----------|---------|
| Minor | Small variance within expected tolerance.  No escalation required. |
| Moderate | Variance is outside normal tolerance but not critical.  Should be reported and monitored. |
| Major | Significant variance.  Programme board awareness and a response plan required. |
| Critical | Severe variance.  Likely to trigger a formal reset, re-baseline, or escalation to the SRO. |

### Threshold filtering

You can ask for only variances above a certain severity level, which is useful
when a large programme has many work packages and you want to focus attention on
the most significant changes only.

### Example prompts

- "Compare PROJ-001 against its baseline."
- "How much has PROJ-001 slipped against the original approved baseline?"
- "Show me the baseline comparison for PROJ-001 — only show variances that are
  major or critical."
- "What is the cost variance for PROJ-001 against the last approved baseline?"
- "Has the total duration of PROJ-001 changed significantly since it was
  re-baselined in January?"

### What the output means

When two baselines are shown (original and last approved), the comparison
between them tells you how much the project was already adjusted before the
current drift.  A project that has already been re-baselined once and is now
drifting again from its re-approved plan carries a different governance
implication than one experiencing its first deviation.

### What to do with the results

The baseline comparison report provides the factual evidence base for
conversations with the programme board about whether a further re-baseline
is warranted, whether contingency needs to be released, or whether the project
needs a formal reset.  It should be included in gate review documentation as a
matter of course, as it demonstrates awareness of and accountability for plan
drift.

---

## Preparing for gate reviews

The following sequences are recommended for structured gate preparation.  They
assume your project data has already been loaded.

### Gate 2 — Delivery readiness

Gate 2 typically assesses whether the project has a credible delivery plan and
has understood its risks before moving into execution.  The analysis should
demonstrate that the plan is sound and the risks are known.

Recommended sequence:

1. **detect_outliers** (standard sensitivity) — confirm the schedule data is
   clean before analysis.
2. **identify_risks** (standard depth) — produce a current analytical risk
   picture across all eight dimensions.
3. **forecast_completion** (ml_ensemble) — establish the forecast completion
   date and the confidence interval for the delivery plan.
4. **suggest_mitigations** — for the highest-probability, highest-impact risks
   from step 2, generate mitigations for inclusion in the risk register.
5. **assess_health** — get the baseline health scores that will be used for
   trend analysis at future gates.

At Gate 2, you will not yet have a meaningful compare_baseline result unless
the project has already been running for some time.  You can omit it or use it
to confirm the plan has not already drifted from the original business case.

### Gate 3 — Delivery in progress

Gate 3 occurs during delivery.  The analysis should demonstrate that the
project is being managed effectively and that risks and variances are
understood.

Recommended sequence:

1. **detect_outliers** (standard sensitivity) — clean data quality issues.
2. **compare_baseline** — quantify how far the project has moved from its
   approved plan and present the evidence to the board.
3. **identify_risks** (standard depth) — update the analytical risk picture.
4. **forecast_completion** (ml_ensemble) — provide an updated completion
   forecast with scenarios.
5. **assess_health** (with trend analysis) — show whether health is improving
   or declining since the previous gate.
6. **suggest_mitigations** — for any new or elevated risks, generate
   mitigation proposals.

The trend analysis in assess_health is particularly important at Gate 3, as it
shows the programme board whether the trajectory is in the right direction.

### Gate 4 — Completion and close-out

Gate 4 typically confirms that delivery outcomes have been achieved and the
project is ready to close.  The analysis should provide a final factual record
of how the project performed against its plan.

Recommended sequence:

1. **compare_baseline** (both original and last approved baselines) — produce
   the definitive account of schedule and cost variance across the project
   lifecycle.
2. **assess_health** (with trend analysis) — provide the final health picture
   and demonstrate the trajectory across all gates.
3. **detect_outliers** — confirm there are no remaining data quality issues in
   the final schedule record.

identify_risks and suggest_mitigations are generally less relevant at Gate 4
unless the project has residual risks that will be handed over to operational
management.  If so, run identify_risks (standard depth) and suggest_mitigations
for any risks that will transfer to the receiving organisation.

---

## Reading the outputs

The following terms appear across multiple tool outputs.  This section explains
what they mean in plain English.

### Schedule Performance Index (SPI)

SPI is an Earned Value Management metric.  It compares the value of work
completed against the value of work that was planned to be complete by now.

- SPI above 1.0 means the project is ahead of schedule.
- SPI of 1.0 means the project is exactly on schedule.
- SPI below 1.0 means the project is behind schedule.  An SPI of 0.8 means
  the project has completed only 80% of the work it should have by this point.

SPI is one of the inputs to the earned_value forecasting method.

### Cost Performance Index (CPI)

CPI is the cost equivalent of SPI.  It compares the value of work completed
against the actual cost of doing it.

- CPI above 1.0 means the project is delivering more value per pound spent than
  planned — it is under budget for the work done.
- CPI of 1.0 means cost performance is exactly as planned.
- CPI below 1.0 means the project is spending more than planned for the work
  completed.  A CPI of 0.9 means the project is spending approximately 11%
  more than planned for each unit of progress.

### Float (also called total float or slack)

Float is the amount of time a task can be delayed without delaying the overall
project completion date.  A task with 10 days of float can slip by 10 days
without affecting the end date.

Tasks with zero float are on the critical path — any delay to them directly
delays the project.  The detect_outliers tool flags tasks where zero float
appears suspicious, for example where a soft constraint has been applied to
force a task onto the critical path artificially, which can mask genuine
schedule risk.

### Confidence interval

A confidence interval gives you a range rather than a single point, and tells
you how confident the analysis is that the true outcome falls within that range.
An 80% confidence interval around a forecast completion date means that,
based on current data, there is an 80% probability that the project completes
within that date range.

A wider confidence interval means greater uncertainty.  If the interval spans
several months, the data is not yet giving a precise signal — either because
the project is early in its lifecycle, or because there is high variability in
task performance.

### Drift severity

The compare_baseline tool classifies variances using four severity levels:
minor, moderate, major, and critical.  These are based on the absolute and
relative magnitude of the variance.  Your programme may define specific
thresholds for each severity level; if not, the platform applies default
thresholds.  Drift severity is not the same as a RAG rating — it is an
analytical classification that informs, but does not replace, the governance
judgement of the programme board.

### Residual risk

After a mitigation has been applied to a risk, some level of exposure typically
remains.  This remaining exposure is the residual risk.  The suggest_mitigations
tool shows the expected residual probability and impact after the proposed
mitigation, so that you can judge whether the residual level is acceptable or
whether further action is needed.

---

## Choosing the right depth setting

The identify_risks tool offers three depth settings.  Choosing the right one
depends on the situation.

**Use quick when:**
- You are doing a routine weekly check and want to know whether anything
  material has changed.
- Time is limited and you need a fast result to inform an immediate decision.
- You have already run a recent standard or deep analysis and want to monitor
  for new signals in between.

**Use standard when:**
- You are preparing for a routine gate review or programme board meeting.
- You are onboarding a new project into the platform and want to establish a
  baseline risk picture.
- You want to update the risk register at a scheduled review point.
- You are monitoring a project in delivery at a normal cadence.

**Use deep when:**
- You are preparing for a major gate (particularly Gate 3 or Gate 4) where a
  comprehensive evidence base is required.
- The project has recently been replanned, re-baselined, or has experienced
  a significant change event.
- The project is in an amber or red state and you need the most thorough
  analytical picture available.
- You want to understand dependency chains — how a risk in one part of the
  schedule could cascade through to affect other areas.

Deep analysis takes longer to run.  For large programmes with complex schedules,
allow extra time.  It is generally not necessary to run deep analysis on every
cycle; standard depth is appropriate for most routine use, with deep reserved
for significant moments in the project lifecycle.

---

## Frequently asked questions

**Do I need to load the project before every conversation?**

Yes.  Each conversation starts fresh.  If you start a new conversation with
Claude, you need to ask it to load your project before running any analysis.
Within a single conversation, you only need to load the project once.

**Can I run analysis on a project that has only just started?**

Yes, but some tools will have less data to work with.  identify_risks and
assess_health will work from the earliest stages.  forecast_completion and
compare_baseline will be more informative once the project has accumulated
several periods of actual performance data.  detect_outliers requires enough
tasks in the schedule to compute meaningful statistics.

**How often should I run assess_health?**

As a minimum, run it before each gate review.  For projects in delivery, running
it monthly provides enough data points for meaningful trend analysis.  For
projects in an amber or red state, consider running it at each reporting cycle
so that the trend line is granular enough to detect whether interventions are
having an effect.

**The forecast completion date is later than my target date.  What does that mean?**

It means the current trajectory of the project is not consistent with the target
date.  This is a signal, not a statement of what will happen — it tells you that
if current performance continues unchanged, the project will not meet its target.
The next step is to understand why (compare_baseline for plan drift, identify_risks
for emerging issues) and then determine whether recovery actions can change the
trajectory.

**Can I ask for mitigations without running identify_risks first?**

Yes.  You can ask for mitigations by risk category rather than by specific risk
ID.  For example: "Suggest mitigations for schedule risks on PROJ-001."  However,
running identify_risks first produces more targeted mitigations because the tool
can work with the specific patterns it found, rather than generating generic
category-level responses.

**Are the outputs suitable for inclusion in formal gate review documents?**

The outputs are analytical evidence.  They are intended to inform the judgements
made in gate reviews, not to replace them.  Numbers, scores, and forecasts
produced by the platform should be reviewed by the project manager and, where
appropriate, the project controls lead before being included in formal
documentation.  As with any analytical tool, the results are only as reliable
as the underlying data.

**How do I know whether the analysis is based on current data?**

Check when the project data was last updated.  If there is any doubt about
whether the schedule reflects recent actuals, ask your planner to confirm before
running analysis.  Running detect_outliers can also surface indicators of stale
data, such as tasks with dates that have passed but whose progress has not been
updated.

## evaluate_calibration — measuring how well-calibrated your forecasts are

A **calibrated** forecaster has confidence equal to accuracy on every subset of
its predictions.  If you say five projects have an 80% chance of meeting their
Gate 3 milestone, you'd expect four of them to actually meet it.  When forecasts
are systematically over- or under-confident, the headline DCA distribution stops
being a useful planning signal.

`evaluate_calibration` measures this empirically.  You supply a paired list of
predictions (your confidence scores, between 0 and 1) and actuals (what
happened, encoded as 1 = forecast met, 0 = missed), and it returns the
**Expected Calibration Error** plus per-bin reliability-diagram data.

### Worked example

You ran `score_assumption_confidence` quarterly for the past year and have
recorded which assumptions turned out to be valid.  Run:

```
evaluate_calibration —
  predictions: [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35]
  actuals:     [1,    1,    1,    1,    0,    0,    0]
  n_bins: 7
  project_id: "PRJ-ALPHA"
```

A perfectly-calibrated forecaster in this example would produce ECE close to
zero.  If you get ECE = 0.08, the interpretation tells you it's acceptable but
not excellent — and points you at **temperature scaling** as the standard
correction.  Above ECE = 0.15 you're materially overconfident or
underconfident and should not be using the raw probabilities for board
decisions until they're recalibrated.

The `bins` output is a reliability-diagram dataset ready to plot: each bin
carries its confidence range (`lower`, `upper`), how many samples fall in it
(`count`), the mean confidence and mean accuracy within the bin
(`mean_confidence`, `mean_accuracy`), and the gap between them (`gap`).  A
visualisation tool can render this directly.

### When to use

- After a gate review, to check whether the RAG ratings used by the team in
  the run-up actually predicted gate outcomes.
- Quarterly, on assumption-confidence outputs, to detect drift between
  forecast confidence and observed outcomes.
- Before relying on AI-generated confidence scores for budget-setting, to
  satisfy the HMT Green Book optimism-bias check.

### Limitations

- Requires a history of forecast/actual pairs.  Not useful for one-off point
  forecasts.
- Binary outcomes only (0/1).  Multi-class calibration would need a future
  extension.
- Sample size matters: ECE on fewer than 50 paired observations is noisy.

---
