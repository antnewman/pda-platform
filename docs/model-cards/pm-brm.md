# Model Card: pm-brm AI Tools

This model card describes the AI-powered components within the `pm-brm` module of PDA
Platform. It is intended for information governance teams, senior responsible owners,
assurance reviewers, and others who need to understand what AI is doing within the
benefits realisation management toolchain.

---

## Model Details

- **Foundation model**: Anthropic Claude (`claude-3-5-sonnet`) accessed via the
  Anthropic API.
- **Version**: The model version is pinned in the `agent-task-planning` package. See
  `packages/agent-task-planning/pyproject.toml` for the current pin.
- **Integration layer**: The `agent-task-planning` package provides provider
  abstraction, multi-sample confidence extraction, and structured output handling. The
  underlying model is called via the `anthropic` Python SDK.
- **Purpose**: Generating IPA-compliant benefits assurance narratives for gate reviews
  with multi-sample confidence scoring.

---

## Module Overview

The `pm-brm` module has 10 tools. Two distinct categories of tool exist:

**AI-powered tools (require `ANTHROPIC_API_KEY`):**

| Tool | What the AI does |
|---|---|
| `generate_benefits_narrative` | Drafts an IPA-compliant benefits assurance narrative for a specified gate review, using data from the benefits register as context. Uses multi-sample consensus to produce a confidence score. |

**Deterministic tools (no AI, no API key required):**

| Tool | What it does |
|---|---|
| `ingest_benefit` | Registers a benefit with IPA/Green Book metadata; validates required fields. |
| `track_benefit_measurement` | Records a measurement; computes drift percentage, drift severity, trend direction, and realisation percentage using arithmetic. |
| `get_benefits_health` | Aggregates health metrics across a project's benefits register; computes the overall health score using a weighted formula. |
| `map_benefit_dependency` | Creates nodes and edges in the benefit dependency DAG; validates acyclicity. |
| `get_benefit_dependency_network` | Retrieves the full dependency graph. |
| `forecast_benefit_realisation` | Projects forward using linear extrapolation from the current measurement trajectory. |
| `detect_benefits_drift` | Identifies statistically significant deviations from planned realisation profiles using time-series analysis. |
| `get_benefits_cascade_impact` | Propagates through the dependency DAG to identify all downstream nodes affected by a change at a given node. |
| `assess_benefits_maturity` | Scores benefits management maturity against P3M3-aligned criteria based on data completeness, process maturity, dependency mapping, and measurement tracking. |

---

## Intended Use

The AI component in `pm-brm` is designed for use by project delivery professionals,
SROs, and benefits managers preparing for IPA Gateway Reviews. The primary use case is:

- **Gate-specific benefits assurance narrative** (`generate_benefits_narrative`): given
  the project's current benefits register data (total benefits, health score, aggregate
  realisation percentage, at-risk count), the model drafts a narrative suitable for
  inclusion in a gate review pack. Gate-specific probe questions from the IPA's 2021
  Assurance Guide are injected as context when a gate number is provided, which orients
  the narrative toward the specific evidential questions an IPA reviewer will ask at
  that gate.

All outputs are advisory. They are intended to support human review, not to replace it.

---

## Per-Tool Behaviour

### AI-powered tool

| Tool | Method | What the AI does | Key limitation |
|---|---|---|---|
| `generate_benefits_narrative` | Multi-sample consensus via `NarrativeGenerator` | Synthesises the benefits register data into prose that explains the benefits picture, highlights risks to realisation, and addresses the IPA gate probe questions for the specified gate. | The narrative is based entirely on the structured data the tool reads from the store. It has no access to qualitative context (e.g. sponsor confidence, organisational capacity, external dependencies) unless that information has been recorded in the benefits descriptions or notes. A high confidence score means the model was consistent across samples — it does not mean the narrative accurately reflects the full project reality. |

### Deterministic tools with interpretive outputs

While the following tools are deterministic, their outputs involve interpretive
thresholds that practitioners should understand:

**`assess_benefits_maturity`** — The maturity level (P3M3 Level 1–5) is calculated
by testing the stored data against a defined set of criteria (data completeness,
process evidence, dependency mapping, measurement tracking). The tool assesses what
the data shows, not what the project is actually doing. A project could hold a detailed
P3M3 Level 4 conversation at a gateway review while scoring Level 2 in this tool if
the evidence has not been recorded in the store. Conversely, a project can score highly
here without having implemented the practices — if all the fields are populated but the
underlying data quality is poor. The assessment is a prompt for conversation, not an
audit finding.

**`detect_benefits_drift`** and **`track_benefit_measurement`** — Drift is detected
using statistical deviation from the planned realisation profile. Drift detection flags
that a benefit's trajectory has diverged from plan; it cannot determine whether that
divergence is justified (for example, a scope reduction that legitimately reduces the
target value) or problematic. A `SIGNIFICANT` drift severity flag requires a human
review of the underlying cause — it is not automatically an indicator of poor
performance.

**`forecast_benefit_realisation`** — The forecast uses linear extrapolation. This
means it projects the current rate of change forward to the target date. For benefits
with non-linear realisation profiles (ramp-up curves, seasonal patterns, step-change
improvements), the linear forecast may significantly underestimate or overestimate the
probability of realisation. The `interim_targets` field in `ingest_benefit` should be
used to record expected non-linear profiles; the forecast tool reads these to provide
a more calibrated projection.

---

## Known Limitations and Failure Modes

### generate_benefits_narrative

- **Missing qualitative context**: The narrative generator works from structured data
  in the benefits register. If the benefit descriptions are sparse, generic, or have not
  been updated since project initiation, the narrative will reflect that. A narrative
  generated from a register where all benefits have boilerplate descriptions will be
  coherent but superficial. Benefits descriptions should pass the MSP DOAM test
  (Described, Observable, Attributable, Measurable) for the narrative to be substantive.

- **Gate probe orientation**: Gate-specific probe questions are drawn from the IPA's
  2021 Assurance Guide. If the IPA has updated its gate-specific expectations since
  that publication, the probe questions may not reflect current IPA thinking.

- **Confidence score calibration**: Confidence scores reflect agreement across model
  samples, not accuracy against an external reference. A high confidence score means
  the model produced consistent outputs — not that those outputs are correct. The
  multi-sample method reduces variance; it does not eliminate the possibility of a
  confidently wrong narrative.

- **Length and tone**: The narrative generator produces text of broadly appropriate
  length for a gate review narrative. For very early-stage projects (Gate 0, Gate 1)
  with limited benefits data, the narrative may be brief. For Gate 3 and Gate 4
  assessments where the benefits register is comprehensive, the narrative may need
  to be condensed for submission. Treasury and Cabinet Office narrative fields have
  character limits that the tool does not enforce.

- **API dependency**: `generate_benefits_narrative` requires a valid
  `ANTHROPIC_API_KEY` environment variable. If the key is absent, the tool fails
  gracefully with an error message. All other pm-brm tools remain available.

### Deterministic tools

- **`forecast_benefit_realisation`** requires at least two measurement data points to
  compute a meaningful trajectory. With a single measurement, the tool cannot determine
  the rate of change and will return a low-confidence forecast.

- **`detect_benefits_drift`** and **`get_benefits_health`** will flag benefits with
  no measurements as stale. This is correct behaviour — a benefit with no recorded
  measurements has no evidence of progress — but project teams should ensure that
  the measurement schedule (`measurement_frequency` in `ingest_benefit`) reflects
  the actual availability of measurement data for that benefit type.

- **`assess_benefits_maturity`** scores against the data held in the AssuranceStore.
  It does not integrate data from external systems (finance systems, HR systems,
  OGC databases). The maturity score will underestimate true maturity if teams are
  managing benefits well in other systems but have not migrated data to the store.

---

## Confidence Scoring

Every call to `generate_benefits_narrative` returns a `confidence` field (0.0–1.0)
and a `review_level` field.

| Confidence | Review level | Recommended action |
|---|---|---|
| 0.80–1.00 | ROUTINE | Narrative is suitable for final review by the benefits owner before submission. Light editing expected. |
| 0.65–0.79 | RECOMMENDED | Narrative should be reviewed by a benefits professional. Check that the key claims are supported by the underlying data. |
| Below 0.65 | REQUIRED | Narrative should be treated as a structural draft only. Rewrite substantively before including in a gate review pack. |

The confidence score is derived from multi-sample consensus: the `agent-task-planning`
package requests multiple independent completions and measures agreement across samples.
A low score indicates the model produced variable outputs — typically because the
benefits data is sparse or inconsistent, or because the gate probe questions are not
well-addressed by the available data.

---

## Out of Scope

The following uses are outside the intended scope of these tools and should be avoided:

- **Formal P3M3 assessment**: `assess_benefits_maturity` produces a data-driven
  maturity estimate, not a certified P3M3 assessment. Formal P3M3 assessments must be
  conducted by accredited practitioners following the official methodology.
- **Benefits realisation auditing**: the tools track and report what the data shows;
  they cannot audit whether the underlying measurement processes are sound.
- **Investment Committee decisions**: benefit forecasts and health scores are advisory
  inputs to investment decisions; they should not be the sole determining factor in
  a spending review or business case submission.
- **Jurisdictions outside UK government project delivery**: the tools are calibrated
  against IPA and Green Book frameworks. Use in other regulatory contexts has not
  been evaluated.
- **Personal data**: no personal data about named individuals should be submitted to
  the narrative generator. The tool processes project-level data.

---

## Human Oversight Requirements

The following human oversight steps are required before AI outputs are used in
governance processes:

1. **Before using `generate_benefits_narrative` output in a gate review pack**: the
   benefits owner or SRO must review the narrative against the actual benefits register
   data and the project's current situation. The narrative must not be submitted
   unreviewed.

2. **Where `review_level` is `REQUIRED`**: a benefits professional with detailed
   knowledge of the project must rewrite the narrative section before submission.
   The AI output should be used only as a structural guide.

3. **For Gate 3 (Full Business Case) and above**: the narrative must be cross-referenced
   against the Benefits Realisation Plan and the HMT Green Book appraisal. Any
   numerical claims in the AI-generated narrative should be verified against the
   benefits register data.

4. **For any narrative intended for ministerial or Treasury submission**: an additional
   review by the departmental sponsorship team is required. Narratives with
   unsubstantiated claims or generic language should be returned for revision.

---

## How to Combine with Human Judgement

The pm-brm tools are most effective when they are integrated into the benefits
management governance cycle, not used in isolation at submission time.

**Ongoing measurement**: use `track_benefit_measurement` consistently at the
frequency specified during benefit registration. Benefits with quarterly measurement
schedules should have a measurement recorded every quarter; a gap indicates a
governance failure, not a data gap. The health score and drift detection are only
meaningful when the measurement history is complete.

**Dependency network accuracy**: `map_benefit_dependency` records the dependency
relationships that the project team believes exist. The DAG is as accurate as the
thinking behind it — if the project team has not thought through the full chain from
project output to strategic objective, the cascade impact analysis will not surface
hidden dependencies. The dependency network should be reviewed at each gate and
updated if the project's theory of change has evolved.

**Maturity as a diagnostic**: run `assess_benefits_maturity` at each gate review
cycle as a diagnostic, not as a score to optimise. If the maturity level is lower than
expected, use the `evidence_gaps` and `recommendations` outputs to identify the
specific practices that need to be strengthened before the next gate.

**Narrative as a starting point**: the most effective use of `generate_benefits_narrative`
is as a first-pass that surfaces the current benefits picture in structured prose,
which is then reviewed and enriched by the project team. Teams that treat the
narrative as complete will produce submissions that accurately reflect the data but
miss the qualitative context that IPA reviewers consider. Teams that ignore the
narrative generator and write from scratch will produce submissions that may be
eloquent but inconsistent with the data.
