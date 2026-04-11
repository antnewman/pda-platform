# Model Card: pm-gate-readiness Tools

This model card describes the Gate Readiness Assessor tools within the `pm-assure`
module of PDA Platform. These tools are grouped under the `pm-gate-readiness` label
in the documentation, though they are implemented within the `pm-assure` package.

This card is intended for information governance teams, senior responsible owners,
assurance reviewers, and IPA practitioners who need to understand what the gate
readiness tools are doing and what weight to give their outputs.

---

## Model Details

- **Foundation model**: Not applicable. The gate readiness tools are deterministic.
  No AI model is called during the assessment, history retrieval, or comparison
  operations.
- **Integration layer**: `GateReadinessAssessor` in the `pm-data-tools` package.
  The assessor reads data from the `AssuranceStore` (SQLite) and applies a
  rule-based, weighted scoring algorithm.
- **Purpose**: Synthesising data from across the assurance modules to produce a
  structured, scored readiness assessment ahead of an IPA Gateway Review or Project
  Assessment Review.

---

## Module Overview

The gate readiness tools are entirely deterministic. There are no AI calls, no
language model outputs, and no stochastic behaviour. The composite score is
computed by a weighted average of eight dimension scores, each derived from
structured data in the AssuranceStore.

| Tool | Method | What it does |
|---|---|---|
| `assess_gate_readiness` | Deterministic weighted scoring | Reads data from all assurance modules, scores eight dimensions against gate-specific weights, and returns a composite readiness score, blocking issues, risk signals, and recommended actions. |
| `get_gate_readiness_history` | Deterministic database query | Returns all past assessments for a project, optionally filtered by gate type, ordered by assessment date. |
| `compare_gate_readiness` | Deterministic arithmetic | Computes the score delta, dimension-level improvements and degradations, and resolved or new blocking issues between two stored assessments. |
| `scan_for_red_flags` | Deterministic cross-module query | Queries risks, benefits, gate readiness, financials, change requests, and resources in a single pass and returns a prioritised alert list filtered by severity threshold. |

---

## Intended Use

These tools are designed for project delivery professionals, PMOs, assurance
teams, and SROs preparing for IPA Gateway Reviews. The primary use cases are:

- **Pre-gate readiness check** (`assess_gate_readiness`): run in the weeks before
  a scheduled gate review to identify blocking issues, low-scoring dimensions, and
  recommended actions while there is still time to address them.
- **Readiness trend analysis** (`get_gate_readiness_history`, `compare_gate_readiness`):
  demonstrate to the IPA or to a governance board that readiness has improved following
  a previous NOT READY or AT RISK assessment.
- **Cross-module health scanning** (`scan_for_red_flags`): obtain a rapid, single-call
  summary of all active risk signals across the project without running ten or more
  individual tools.

All outputs are advisory. The gate readiness score is an indicator intended to
support pre-gate preparation and governance discussion. It is not a substitute for
a formal IPA Gate Review.

---

## How the Score is Calculated

The composite readiness score (0.0–1.0) is a weighted average of eight dimension
scores. Each dimension draws on data from one or more assurance modules already
populated in the AssuranceStore.

### The eight dimensions

| Dimension | What it measures | Key data sources |
|---|---|---|
| Artefact Readiness | Currency of evidence documents; closure rate of open review actions | Review actions store (P3), assurance workflows (P9) |
| Data Quality | NISTA compliance trend; AI extraction confidence trends | Validation results, assurance metrics |
| Assumption Health | Proportion of assumptions within tolerance; critical drift rate | Assumptions store (P11) |
| Risk Management | High/critical risk score; stale risk rate; mitigation coverage | Risk register (pm-risk) |
| Benefits Realisation | Benefits health score; at-risk count; stale measurement rate | Benefits register (pm-brm) |
| Governance Maturity | ARMM maturity score; override decision patterns | ARMM assessments (P12) |
| Financial Health | Cost performance metrics; EAC variance | Cost data (pm-financial) |
| Change Control | Change pressure score; unapproved change count | Change log (pm-change) |

### Gate-specific weighting

Dimension weights vary by gate to reflect the IPA's expectations at each lifecycle
stage. The weights are not published in this model card as they may be refined between
releases. Key directional observations:

- At Gate 1 (SOC), Benefits Realisation and Assumption Health have lower weight than
  at later gates; Artefact Readiness is most important.
- At Gate 3 (FBC), Benefits Realisation and Financial Health carry the highest weights,
  reflecting the Treasury's detailed scrutiny of benefit-cost ratios at FBC.
- At Gate 4 (Readiness for Service), Artefact Readiness and Change Control increase
  in weight as the project approaches live operation.
- PAR (Project Assessment Review) applies equal weights across all dimensions.

### Readiness classification

The composite score maps to a readiness label:

| Score range | Readiness label | What it means |
|---|---|---|
| 0.75–1.00 | READY | The project's data picture supports gate progression. No blocking issues. |
| 0.55–0.74 | CONDITIONALLY READY | Ready subject to resolving specific issues identified in the assessment. |
| 0.35–0.54 | AT RISK | Significant gaps; remedial action required before gate. |
| 0.00–0.34 | NOT READY | Blocking issues present or severe data gaps. |

**Note on data coverage cap**: if fewer than four of the eight dimensions have data
available to score, the assessment is capped at CONDITIONALLY READY regardless of
the composite score. This prevents a project appearing READY when the platform simply
has insufficient data to form a reliable view.

---

## Known Limitations and Failure Modes

### The score reflects the data, not the project

The most important limitation is that the composite score measures the quality and
completeness of the data held in the AssuranceStore — not the underlying delivery
health of the project. A project with disciplined data governance and a full
AssuranceStore will score higher than a project in better delivery health that
has not maintained its data.

This is not a defect in the algorithm; it is a structural feature of any data-driven
assessment. The implication is that the score is most informative when the data has
been maintained consistently over time, and least informative at the start of a
project's engagement with the platform when much of the store is empty.

### The score is not comparable across project types without normalisation

A £5m business-as-usual improvement project and a £500m major programme have very
different expectations for benefits complexity, risk profile, and change pressure.
The assessment algorithm does not normalise for project scale or complexity.
A small project with a simple benefits structure may score lower on Benefits
Realisation simply because it has fewer benefits to register, not because its
benefits management is weaker. Comparative use of the score across projects should
account for this.

### Blocking issues are rule-based, not contextual

Blocking issues are triggered by specific data conditions: critical assumption drift
above a threshold, action closure rate below a threshold, governance score below a
floor. The rules do not have access to contextual information — for instance, a
critical assumption that has drifted but has a documented, approved mitigation plan
may still trigger a blocking issue. Practitioners should review each blocking issue
against the actual project situation before treating it as unresolved.

### Recommended actions are generic

The `recommended_actions` output is generated from a lookup table of pre-defined
recommendations mapped to each low-scoring dimension. The text is deliberately generic
to be applicable across project types. IPA reviewers will expect project-specific
action plans with named owners and due dates — the recommended actions from this
tool are a starting point, not a complete response.

### The score does not assess artefact quality

The Artefact Readiness dimension assesses whether evidence documents have been
referenced in the platform's data and whether review actions have been closed. It does
not assess the quality of the artefacts themselves. A gate readiness score with a
high Artefact Readiness score does not imply that the business case, risk register,
or benefits realisation plan will satisfy an IPA reviewer's scrutiny — only that
they are present and have been referenced.

### IPA reviewers may weight criteria differently

The gate-specific dimension weights applied by this tool are the platform's best
approximation of IPA expectations based on published guidance. Individual IPA
reviewers, gate leads, and review teams apply their own judgement about what matters
most at a given gate for a given project type. The composite score will not always
align with the outcome of a formal IPA Gate Review, and this should be expected.
The tool's purpose is to surface gaps before the review, not to predict the outcome.

### `scan_for_red_flags` reflects a snapshot

The cross-module red flag scanner queries the current state of all modules at the
moment of the call. It does not track changes over time and cannot distinguish
between a red flag that has just appeared and one that has been present for months.
For trend information on specific flag types, use the dedicated module tools
(for example, `get_risk_velocity` for risk trends, `detect_benefits_drift` for
benefits trends).

---

## Out of Scope

- **Formal IPA Gate Reviews**: the gate readiness score does not constitute or
  substitute for a formal IPA Gate Review. Gate reviews are conducted by independent
  IPA-accredited reviewers. This tool prepares for a gate review; it does not replace
  one.
- **Spend approval decisions**: the composite score should not be used as the sole
  basis for a spending approval or investment decision.
- **Performance management of delivery teams**: the tools process project-level data.
  They are not designed to assess the performance of named individuals.
- **Jurisdictions outside UK government project delivery**: the dimension weights and
  readiness thresholds are calibrated against IPA Gateway Review frameworks. Use in
  other contexts has not been evaluated.

---

## Human Oversight Requirements

The following human oversight steps apply when using gate readiness outputs in
governance processes:

1. **Before presenting a gate readiness score to a governance board or SRO**: a
   practitioner with knowledge of the project must review the blocking issues and
   dimension breakdown. The score alone is not sufficient context for a governance
   discussion.

2. **When the readiness label is AT RISK or NOT READY**: the blocking issues and
   low-scoring dimensions must be reviewed against the actual project situation. Some
   blocking issues may be already mitigated in practice but not yet reflected in the
   data. These should be resolved in the store before the assessment is shared.

3. **When comparing assessments to demonstrate improvement**: confirm that the
   improvement in score reflects genuine remedial action, not simply the addition of
   data to the store (which also raises scores). Both are valid — adding missing data
   is itself a governance improvement — but the narrative presented to the IPA should
   be accurate about what has changed.

4. **When the data coverage cap applies** (fewer than four dimensions scored): the
   assessment is structurally limited. Before presenting the assessment, populate the
   missing module data. The gate readiness assessment is only as reliable as the data
   that feeds it.

---

## How to Combine with Human Judgement

### Use the assessment as a structured checklist

The eight-dimension breakdown functions as a structured pre-gate checklist. For each
low-scoring dimension, the `dimension_scores` output identifies which data sources
are missing (`sources_missing`). This tells the project team exactly what to address,
not just that something is wrong.

### The blocking issues list is the highest priority output

Blocking issues cause the readiness to be classified as NOT READY regardless of the
composite score. They should be the first thing reviewed and the first to be resolved.
The `blocking_issues` list identifies each issue with a description and the dimension
it affects. Resolve these before the gate, and run a new assessment to confirm they
have been resolved.

### Use comparison to provide evidence of improvement

When a project has received a NOT READY or AT RISK assessment, governance boards often
ask for evidence that the issues have been addressed before a re-assessment. Running
`compare_gate_readiness` against the stored assessments provides this evidence in a
structured form — resolved blockers are explicitly listed, and dimension-level score
changes are quantified. This is more robust than a qualitative assertion that
improvements have been made.

### The gate readiness assessment is most valuable when run regularly

A single pre-gate assessment run in the week before the review is useful but limited.
Run `assess_gate_readiness` monthly during the final six months before a major gate
to monitor readiness trends over time. This creates a data trail that demonstrates
sustained preparation, which IPA reviewers regard positively. It also gives the project
team time to respond to emerging issues rather than discovering them immediately before
the gate.

### Align the platform's data with what the IPA will see

The IPA reviewers will receive evidence from the project team directly. The gate
readiness assessment is based on what is in the AssuranceStore. Before the review,
confirm that the key evidence documents (business case, risk register, benefits
realisation plan) are reflected in the store and are current. A mismatch between
what the store knows about and what the IPA receives will make the readiness score
less informative.
