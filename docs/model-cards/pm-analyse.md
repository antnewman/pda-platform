# Model Card: pm-analyse AI Tools

This model card describes the AI-powered and statistical components within the `pm-analyse` module of PDA Platform. It is intended for project managers, schedulers, risk owners, governance teams, and others who need to understand which tools use AI, how those tools behave, and what oversight is required before outputs are used in formal delivery processes.

---

## Model Details

`pm-analyse` is a mixed module: some tools are AI-powered, some are statistical, and some are fully deterministic. The distinction matters for how outputs should be interpreted and reviewed.

| Tool | Method |
|---|---|
| `identify_risks` | Anthropic Claude (AI) |
| `suggest_mitigations` | Anthropic Claude (AI) |
| `forecast_completion` | Statistical regression + Claude interpretation |
| `assess_health` | Deterministic scoring + Claude narrative |
| `detect_outliers` | Statistical (z-score / IQR) |
| `compare_baseline` | Deterministic |

- **Foundation model**: Anthropic Claude accessed via the Anthropic API (`ANTHROPIC_API_KEY`). Model version is pinned in the `agent-task-planning` package — see `packages/agent-task-planning/pyproject.toml` for the current pin.
- **Integration layer**: the `agent-task-planning` package provides provider abstraction and structured output handling for all Claude-powered tools.

---

## Intended Use

The `pm-analyse` module is designed for use by project managers, schedulers, and assurance reviewers working on UK government programmes. The primary use cases are:

- **Early risk identification** (`identify_risks`): surfacing schedule-embedded risks — tasks with high duration, low float, complex dependencies, or structural anomalies — that may not yet appear in the formal risk register.
- **Completion forecasting** (`forecast_completion`): projecting likely completion date based on current progress rate, float consumption, and critical path position for use in governance reporting and escalation decisions.
- **Health assessment** (`assess_health`): producing a scored, narrative assessment of schedule health for use in reviews, gate preparation, and programme reporting.
- **Outlier detection** (`detect_outliers`): identifying tasks with statistically unusual duration, float, or resource loading relative to the project's own distribution.
- **Mitigation suggestion** (`suggest_mitigations`): generating candidate mitigation actions for identified risks as a starting point for risk owner review.
- **Baseline comparison** (`compare_baseline`): computing precise variance between current schedule data and the approved baseline.

All AI-generated outputs are advisory. They are intended to support practitioner analysis, not to replace the judgement of the project manager or risk owner responsible for the programme.

---

## Out-of-Scope Uses

The following uses are outside the intended scope of these tools and should be avoided:

- **Adding AI-generated risks directly to the formal risk register without review**: `identify_risks` output is a starting point for discussion. Risk owners must review and validate each identified risk before it enters the project's formal risk register.
- **Using `forecast_completion` as a contractual or commitment date**: the forecast is a statistical projection based on current data. It is not a programme commitment and should not be presented as one.
- **Treating `suggest_mitigations` output as a pre-approved action plan**: mitigation suggestions are generated without knowledge of the project's commercial constraints, supplier agreements, or organisational dynamics. They must be filtered for feasibility before action.
- **Using `detect_outliers` output as evidence of error without investigation**: statistical outliers may reflect deliberate programme design decisions. Flagged tasks require investigation, not automatic correction.
- **Jurisdictions and frameworks outside UK government project delivery**: the module is designed for GMPP-aligned and IPA-framework programmes. Use in other delivery contexts has not been evaluated.

---

## Training Data

Not applicable for statistical and deterministic tools — these apply standard statistical methods and mathematical operations with no training component. For AI-powered tools, PDA Platform uses a pre-trained foundation model (Anthropic Claude) via API. No fine-tuning or additional training has been performed using project delivery data. The model's training data, training methodology, and data governance are Anthropic's responsibility and are documented in Anthropic's published model cards.

---

## Per-Tool Behaviour and Evaluation

### identify_risks

Claude analyses schedule structure — task names, durations, float values, dependency chains, and resource loading — to surface risks that may not have been explicitly logged. The model applies pattern recognition across these schedule properties to identify structural risk signals.

Practitioners should be aware that:
- The model has a tendency to flag more risks than a human reviewer might. It errs toward sensitivity over specificity. Treat output as a candidate list for discussion, not a definitive risk assessment.
- The model does not know what the project manager knows. Contextual information not present in the schedule data — such as a deliberately long task reflecting a procurement process, or a low-float path that is being actively managed — will not be factored into the output. Some flagged items will be false positives in light of this context.
- Risk identification output does not include confidence scores at the individual risk level. The entire output should be treated as requiring practitioner review.

### forecast_completion

The forecast uses statistical regression on schedule progress data — specifically current progress rate, float consumption rate, and critical path position — to project a likely completion date. A Claude-generated plain-English interpretation of the forecast is included.

Practitioners should be aware that:
- The forecast assumes current progress rate continues linearly for the remainder of the project. It does not account for planned phase transitions (e.g. moving from design to build), known future resource changes, scope changes under consideration, or external dependencies not reflected in current schedule data.
- The primary output is a P50 estimate (50th percentile). To derive a P80 estimate (one that has an 80% probability of being achieved), practitioners should add appropriate schedule contingency based on programme risk exposure.
- The statistical forecast is most reliable when a meaningful amount of schedule progress has been recorded. Forecasts produced early in a project's lifecycle (less than 15–20% progress) should be treated with greater caution.

### assess_health

The overall health score is deterministic: it is computed from a weighted scoring model applied to float levels, resource loading, milestone adherence, and task completion rates. The score is reproducible given the same input data.

The narrative interpretation of the score is generated by Claude. The narrative elaborates on what the component scores mean in context — it does not alter the underlying numerical assessment.

Practitioners should be aware that:
- The health score reflects only the data available to the platform. A project that scores well on schedule data but is experiencing morale problems, supplier difficulties, political pressure, or commercial disputes will not surface those signals through this tool.
- The deterministic score and the AI narrative should be read together. Discrepancies between the two — where the score appears healthy but the narrative flags concerns — should prompt further investigation.

### detect_outliers

Outlier detection uses standard statistical methods (z-score against the project's own task duration distribution, and IQR for identifying extreme values). No AI is involved. The method is applied to the project's own data distribution — a task is flagged as an outlier relative to the distribution of tasks in that project, not against an external benchmark.

Practitioners should be aware that:
- The method applies no domain knowledge about what is a reasonable duration for a given task type. A twelve-month procurement task flagged as a duration outlier may be entirely appropriate given the task's nature.
- Projects with genuinely unusual task structures — such as research programmes with very long single tasks — will generate outlier flags that are mathematically correct but operationally expected.
- Outlier flags are signals for investigation, not evidence of scheduling error.

### suggest_mitigations

Claude generates candidate mitigation actions based on the identified risks and any contextual project information available in the schedule data. Suggestions are framed as starting points for discussion.

Practitioners should be aware that:
- Suggestions are generic unless the schedule data contains rich contextual information (task names, resource names, dependency labels). Sparse schedule data produces generic suggestions.
- The model has no knowledge of commercial constraints, supplier relationships, contractual limitations, team capacity, or organisational risk appetite. All suggestions must be assessed for feasibility in the project's actual context before being progressed.
- Mitigation suggestions must be reviewed by the project manager or risk owner before being included in the formal risk register or agreed as actions.

### compare_baseline

Fully deterministic. `compare_baseline` performs a mathematical comparison of current schedule data against the approved baseline stored in the platform. It returns precise variances with no AI interpretation. No confidence caveats apply to the comparison itself — variances are exact given the data provided.

---

## Confidence Calibration

The platform does not currently output explicit confidence intervals for AI-generated text in `pm-analyse`. The following principles apply:

- AI-generated outputs (`identify_risks`, `suggest_mitigations`, `forecast_completion` narrative, `assess_health` narrative) should be treated as analytical drafts — useful starting points that require practitioner review and refinement.
- Statistical outputs (`detect_outliers`, `forecast_completion` projection) reflect mathematical operations on the available data. Uncertainty in these outputs stems from the quality and completeness of the schedule data, not from model behaviour.
- Deterministic outputs (`assess_health` score, `compare_baseline`) are reproducible and precise given the same input data.

---

## Limitations

- **Sparse schedule data**: schedules with few tasks, no resource loading, or no recorded progress produce low-quality outputs across all AI and statistical tools. Risk identification defaults toward generic flags; health scores default toward neutral mid-range values; outlier detection operates on very small distributions.
- **No knowledge of off-schedule factors**: the module cannot surface risks or health concerns related to factors not captured in schedule data — stakeholder relationships, morale, supplier financial health, political pressure, or emerging policy changes.
- **Forecast assumes linear progress**: `forecast_completion` will misestimate on projects with known non-linear progress profiles. The model does not currently support specifying expected progress curves.
- **identify_risks context blindness**: the model does not know what the project team knows. Apparent anomalies may have legitimate explanations invisible to the tool.
- **suggest_mitigations feasibility gap**: suggestions are generated without knowledge of the project's constraints. Infeasible suggestions are common and should be filtered by the project manager before progressing.
- **No baseline, no compare**: `compare_baseline` requires that a baseline has been set before use. If no baseline is recorded in the platform, the tool returns an error.
- **API dependency**: all Claude-powered tools require a valid `ANTHROPIC_API_KEY`. Statistical and deterministic tools (`detect_outliers`, `compare_baseline`) remain available if the key is absent. AI tools fail gracefully.

---

## Failure Modes

- **Sparse data producing neutral outputs**: when schedule data is thin, AI tools produce outputs that appear complete but add little analytical value — risk lists that are too generic to act on, health narratives that hedge without specificity. Users should treat sparse-data outputs with heightened scepticism.
- **No baseline error in compare_baseline**: attempting `compare_baseline` without a stored baseline returns an error. The fix is to set a baseline before using the tool, not to work around the error.
- **Outlier false positives on unusual programme structures**: `detect_outliers` on research programmes, transformation programmes with long strategic phases, or programmes with very heterogeneous task types will generate high volumes of outlier flags. Consider whether z-score thresholds need adjustment for the project type.
- **Recency bias in forecast_completion**: if schedule progress has been recently accelerated or recently stalled, the regression may extrapolate the recent trend rather than reflecting the full-programme trajectory. Review the underlying progress data before relying on a forecast that has shifted significantly from prior periods.

---

## Ethical Considerations

- **No PII processed**: the tools process schedule and project-level data. No personal data or named individuals should be submitted. Responsibility for data minimisation rests with the user.
- **Advisory outputs**: all AI-generated outputs are explicitly advisory. The platform documentation consistently describes AI outputs as requiring practitioner review before use in formal delivery processes.
- **Auditability**: AI-generated and statistical outputs stored in the AssuranceStore include the tool name, timestamp, project identifier, and relevant input parameters, enabling retrospective audit of what analysis was performed and when.
- **Risk register integrity**: `identify_risks` and `suggest_mitigations` outputs should never bypass the project's formal risk management process. AI surfacing a risk is not equivalent to a risk being formally identified, owned, and logged.

---

## Human Oversight Requirements

The following oversight requirements apply before `pm-analyse` outputs are used in formal delivery processes:

- **Risk identification**: AI-generated risk lists must be reviewed by the project manager or risk owner. Only risks validated by a human reviewer should be added to the formal risk register.
- **Completion forecast**: `forecast_completion` outputs should be reviewed by a qualified scheduler before being reported to governance. The reviewer should assess whether the input data is current and whether the linear progress assumption is appropriate.
- **Health narrative**: all `assess_health` narratives are advisory. The project manager should review the narrative against their knowledge of the project before including it in governance reporting.
- **Mitigation suggestions**: `suggest_mitigations` outputs must be reviewed and filtered by the project manager or risk owner for feasibility before being progressed as actions.
- **Outlier flags**: `detect_outliers` outputs require investigation by a scheduler before being treated as evidence of scheduling error.

---

## Appropriate Use Boundary

`pm-analyse` is suitable for: early risk identification from schedule data as a starting point for risk owner review; generating an initial health assessment for practitioner refinement; producing completion forecasts for governance reporting after scheduler review; identifying schedule quality issues for investigation; reducing the time required to prepare analytical materials for governance.

`pm-analyse` is not suitable as: the primary input to formal risk registers without practitioner review; the basis for programme commitment dates; automatic schedule correction without scheduler investigation; or the sole determinant of health status in formal gate reviews.

---

## Caveats

- Deployments on Render's free tier may experience cold start latency of several seconds on the first request after a period of inactivity. Statistical and deterministic tools are not affected by this in terms of output quality; AI tool response time may increase.
- The `agent-task-planning` package is under active development. The specific Claude model version may change between releases. Significant changes will be noted in the package changelog.
- The analytical value of `pm-analyse` increases with data richness. Teams are encouraged to ensure schedule data is current, resource-loaded, and baseline-tracked before using analysis tools for governance preparation.
