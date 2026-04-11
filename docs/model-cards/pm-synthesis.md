# Model Card: pm-synthesis AI Tools

This model card describes the AI-powered components within the `pm-synthesis` module of PDA Platform. It is intended for information governance teams, senior responsible owners (SROs), programme management offices (PMOs), and others who need to understand what AI is doing when the platform generates executive summaries and cross-project comparisons.

---

## Model Details

- **Foundation model**: Anthropic Claude accessed via the Anthropic API (`ANTHROPIC_API_KEY`).
- **Version**: The model version is pinned in the `agent-task-planning` package. See `packages/agent-task-planning/pyproject.toml` for the current pin.
- **Integration layer**: The `agent-task-planning` package provides provider abstraction and structured output handling. The underlying model is called via the `anthropic` Python SDK.
- **Purpose**: Generating executive health summaries and cross-project comparisons by prompting Claude with structured project data retrieved from the AssuranceStore and from the pm-data, pm-risk, pm-financial, pm-brm, and pm-assure modules.

---

## Intended Use

The AI components in `pm-synthesis` are designed for use by programme delivery professionals preparing materials for senior governance audiences. The primary use cases are:

- **Executive health summaries** (`generate_executive_summary`): given structured data drawn from all connected platform modules, the model produces a narrative summary of project delivery health — covering schedule, risk, financial position, benefits, and assurance status — calibrated to the specified audience (SRO, PMO, or BOARD).
- **Cross-project comparison** (`compare_project_health`): given multiple projects' structured data, the model identifies patterns, contrasts, and portfolio-level themes across projects for use in portfolio reviews and investment committee discussions.

All outputs are advisory. They are intended to support human drafting and review, not to replace the judgement of the responsible officer signing off governance documents.

---

## Out-of-Scope Uses

The following uses are outside the intended scope of these tools and should be avoided:

- **Sole basis for major investment decisions**: AI-generated summaries are a starting point for analysis, not a substitute for financial appraisal, business case review, or the deliberative judgement of an investment committee.
- **Unreviewed submission to formal governance documents**: outputs must be reviewed and approved by a named responsible person before inclusion in board papers, gate review packs, or investment committee submissions.
- **Assessment of personally sensitive information**: the tools process project-level structured data. No personal data, performance assessments of named individuals, or commercially sensitive information outside the platform's data stores should be submitted.
- **Jurisdictions and frameworks outside UK government project delivery**: the module is calibrated for GMPP-aligned and IPA-framework projects. Use in other delivery contexts has not been evaluated.

---

## Training Data

Not applicable. PDA Platform uses a pre-trained foundation model (Anthropic Claude) via API. No fine-tuning or additional training has been performed using project delivery data. The model's training data, training methodology, and data governance are Anthropic's responsibility and are documented in Anthropic's published model cards.

---

## Evaluation

### Confidence Scoring

The confidence score returned by `generate_executive_summary` reflects two distinct factors:

1. **Data completeness**: the proportion of connected modules that have populated data for the project. A project with no financial data, no risk register, and no benefits data will receive a lower confidence score even if schedule data shows delivery on track.
2. **Delivery performance signals**: the platform's assessment of whether the underlying data indicates delivery health or concern.

Users should check the data completeness indicator before interpreting confidence scores. A low score may indicate a data gap rather than a delivery problem, and the two should be treated differently.

Confidence scores have not been externally validated against a ground truth dataset of UK government programme summaries.

### Audience Calibration

The `audience` parameter (SRO / PMO / BOARD) adjusts the level of detail and framing of the output. BOARD outputs are shorter and more strategic; PMO outputs include greater operational detail. This is a prompt-level instruction — the underlying model's analytical capability does not change by audience parameter. Teams should verify that the level of detail produced is appropriate for their specific audience before use.

---

## Limitations

- **Output quality depends on data completeness**: sparse or missing data in the platform's stores produces generic outputs that restate inputs without adding analytical value. Teams should populate all relevant modules before using synthesis tools for governance preparation.
- **Hallucinated specifics**: AI-generated narratives may contain plausible-sounding but inaccurate specifics if the underlying data is ambiguous or contradictory. All narrative text should be verified against source data before submission.
- **No access to external information**: the model has access only to structured data held in the platform's AssuranceStore and connected modules. It cannot access external documents, emails, SharePoint files, correspondence, or systems of record outside the platform.
- **Conflicting data across modules**: if financial data contradicts schedule data, or risk data contradicts assurance outputs, the model may produce internally inconsistent narratives rather than surfacing the conflict explicitly. Practitioners should cross-check summaries against module-level outputs.
- **Portfolio comparison depth**: `compare_project_health` on large portfolios (ten or more projects) may produce surface-level thematic comparison rather than deep per-project analysis. For large portfolios, consider generating individual summaries first and using the comparison tool to identify themes.
- **API dependency**: all AI-powered tools require a valid `ANTHROPIC_API_KEY` environment variable. Tools fail gracefully if the key is absent, but AI-dependent features are unavailable.

---

## Ethical Considerations

- **No PII processed**: the tools are designed to process structured project-level data. No personal data or named individuals should be submitted. The system has no mechanism to enforce this at the API boundary; responsibility for data minimisation rests with the user.
- **Advisory outputs**: all narrative outputs are explicitly advisory. The platform documentation consistently describes synthesis outputs as requiring human review before use in formal documents.
- **Labelling requirement**: AI-generated text used in formal governance documents should be clearly labelled as AI-assisted in those documents. This is both good governance practice and a condition of appropriate use.
- **Auditability**: every AI-generated summary stored in the AssuranceStore includes the tool name, timestamp, project identifier, audience parameter, and confidence score, enabling retrospective audit of AI-influenced governance materials.

---

## Human Oversight Requirements

All outputs intended for formal governance use — including board papers, gate review packs, and investment committee submissions — must be reviewed and approved by a named responsible person before submission. The reviewing officer should:

- Verify that the narrative accurately reflects the underlying data
- Check the data completeness indicator and assess whether gaps affect the reliability of the summary
- Apply professional judgement where the AI narrative conflicts with their knowledge of the project
- Clearly label the document as AI-assisted where AI-generated text has been used

AI-generated text should not be submitted to formal governance forums without this review step.

---

## Appropriate Use Boundary

`pm-synthesis` is suitable for: drafting executive summaries for practitioner review; preparing briefing materials for portfolio review sessions; identifying cross-project themes for investment committee preparation; reducing the time required to produce first-draft governance documents.

`pm-synthesis` is not suitable as the sole basis for: major investment decisions; gate approval or rejection; performance management conclusions; or any formal governance output that has not been reviewed and signed off by a responsible officer.

---

## Caveats

- Deployments on Render's free tier may experience cold start latency of several seconds on the first request after a period of inactivity. This affects response time but not output quality.
- The `agent-task-planning` package is under active development. The specific model version may change between releases. Significant changes will be noted in the package changelog.
- Synthesis outputs are generated as single-pass completions. Unlike some other platform tools, `pm-synthesis` does not currently use multi-sample consensus scoring. The confidence score is data-driven rather than model-consistency-driven.
