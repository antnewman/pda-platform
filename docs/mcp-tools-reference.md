# PDA Platform — MCP Tools Reference

**Version:** 2.0 | **Total tools:** 99 | **Modules:** 14

This reference documents all 99 MCP tools available in the PDA Platform, covering parameter-level detail for each tool. The audience is developers and technical practitioners integrating with or extending the platform.

---

## Contents

- [How to Use This Reference](#how-to-use-this-reference)
- [Module Summary](#module-summary)
- [pm-data — Project Data Loading and Querying](#pm-data--project-data-loading-and-querying)
- [pm-analyse — AI-Powered Analysis](#pm-analyse--ai-powered-analysis)
- [pm-validate — Validation](#pm-validate--validation)
- [pm-nista — GMPP Reporting and NISTA API Integration](#pm-nista--gmpp-reporting-and-nista-api-integration)
- [pm-assure — Assurance Lifecycle](#pm-assure--assurance-lifecycle)
- [pm-brm — Benefits Realisation Management](#pm-brm--benefits-realisation-management)
- [pm-portfolio — Portfolio Intelligence](#pm-portfolio--portfolio-intelligence)
- [pm-ev — Earned Value Analysis](#pm-ev--earned-value-analysis)
- [pm-synthesis — AI Health Summaries](#pm-synthesis--ai-health-summaries)
- [pm-risk — Risk Register and Intelligence](#pm-risk--risk-register-and-intelligence)
- [pm-change — Change Control](#pm-change--change-control)
- [pm-resource — Resource Capacity Planning](#pm-resource--resource-capacity-planning)
- [pm-financial — Financial Management](#pm-financial--financial-management)
- [pm-knowledge — IPA Knowledge Base](#pm-knowledge--ipa-knowledge-base)

---

## How to Use This Reference

### Typical workflow

Most analytical and assurance workflows follow this sequence:

1. **Load the project** using `load_project` (pm-data). This returns a `project_id`.
2. **Query or validate** the project using tools from pm-data, pm-analyse, or pm-validate, passing the `project_id`.
3. **Run assurance or BRM tools** (pm-assure, pm-brm) which persist state to a local SQLite store and accept the same `project_id`.
4. **Generate outputs** — reports, dashboards, narratives — using the relevant export or generate tools.

### The `project_id` parameter

`project_id` is the consistent key across all modules. In pm-data, it is returned by `load_project`. In pm-assure and pm-brm, you supply your own stable string identifier (e.g. `"HMT-PRJ-0042"`) that links records across the SQLite store. Use `create_project_from_profile` to register a project in the assurance store before running assurance tools.

### The `db_path` parameter

All pm-assure and pm-brm tools accept an optional `db_path` parameter pointing to a SQLite file. If omitted, the tools default to `~/.pm_data_tools/store.db`. Supply an explicit path when running multiple projects in isolation, in CI pipelines, or when the default location is not writable.

### Capability codes (Pxx)

Tools in pm-assure and pm-brm are tagged with a capability code (e.g. P1, P13) corresponding to the assurance framework module they implement. These codes appear in each tool's heading.

---

## Module Summary

| Module | Tools | Purpose |
|--------|-------|---------|
| pm-data | 6 | Load project files, query tasks, dependencies, and critical path |
| pm-analyse | 6 | AI-powered risk identification, forecasting, health assessment |
| pm-validate | 4 | Structural, semantic, NISTA, and custom validation |
| pm-nista | 5 | GMPP quarterly reporting and NISTA API submission |
| pm-assure | 27 | Full assurance lifecycle covering P1–P14 |
| pm-brm | 10 | Benefits Realisation Management aligned to IPA/Green Book (P13) |
| pm-portfolio | 5 | Cross-project portfolio aggregation and health rollup |
| pm-ev | 2 | Earned Value metrics (SPI/CPI/EAC/TCPI) and HTML dashboard |
| pm-synthesis | 2 | AI-generated executive health summaries and cross-project comparison |
| pm-risk | 9 | Risk register, heat map, mitigations, velocity tracking, stale detection |
| pm-change | 5 | Change control log, impact analysis, change pressure analysis |
| pm-resource | 5 | Resource loading, conflict detection, portfolio capacity planning |
| pm-financial | 5 | Budget baseline, period actuals, EAC forecasting, spend profile |
| pm-knowledge | 8 | IPA benchmarks, failure patterns, guidance, reference class checks |
| **Total** | **99** | One unified endpoint |

---

## pm-data — Project Data Loading and Querying

Six tools for loading project files from various sources and formats, and querying the resulting project data. All pm-data tools require a `project_id` returned by `load_project`.

---

### `load_project`

**Module:** pm-data

Load a project from a file path or inline content. Supports MS Project, Primavera P6, Jira, Monday.com, Asana, Smartsheet, GMPP, and NISTA formats.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file_path | string | No* | — | Path to the project file on the local filesystem. Use for Claude Desktop or local MCP clients. |
| file_content | string | No* | — | Inline file content. Use base64 encoding for binary formats (`.mpp`); raw text for XML, CSV, and JSON formats. Required when file paths are not accessible (e.g. remote MCP clients). |
| file_name | string | No* | — | Original filename including extension (e.g. `schedule.mpp`). Required when using `file_content` so the parser can detect the format. |
| format | string | No | `auto` | File format hint. One of: `auto`, `mspdi`, `p6_xer`, `jira`, `monday`, `asana`, `smartsheet`, `gmpp`, `nista`. |

\* Either `file_path` or both `file_content` + `file_name` must be provided.

**Returns:** A `project_id` string and a summary of detected tasks, milestones, and resources. Pass the `project_id` to all subsequent pm-data, pm-analyse, and pm-validate tools.

**Example prompt:** "Load the MS Project schedule at `/projects/alpha/schedule.mpp` and give me an overview of what it contains."

---

### `query_tasks`

**Module:** pm-data

Query tasks from a loaded project with optional filters for status, criticality, assignee, and date range.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| filters | object | No | — | Optional filter object. See filter keys below. |
| filters.status | array of strings | No | — | Restrict to tasks with these status values (e.g. `["In Progress", "Not Started"]`). |
| filters.is_critical | boolean | No | — | When `true`, returns only tasks on the critical path. |
| filters.is_milestone | boolean | No | — | When `true`, returns only milestone tasks. |
| filters.assignee | string | No | — | Filter by resource name or assignment identifier. |
| filters.start_after | string (date) | No | — | Return tasks starting after this date. Format: `YYYY-MM-DD`. |
| filters.end_before | string (date) | No | — | Return tasks ending before this date. Format: `YYYY-MM-DD`. |
| limit | integer | No | `100` | Maximum number of tasks to return. |

**Returns:** A list of task objects including ID, name, start/finish dates, duration, float, status, and resource assignments.

**Example prompt:** "Show me all critical path tasks from project PRJ-001 that start after 1 June 2025 and are assigned to Alice."

---

### `get_critical_path`

**Module:** pm-data

Return the critical path for a project and, optionally, near-critical tasks within 5 days of total float.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| include_near_critical | boolean | No | `false` | When `true`, includes tasks with 5 days or fewer of total float alongside the zero-float critical path. |

**Returns:** An ordered list of critical path tasks with float values, durations, and dependency links. If `include_near_critical` is `true`, near-critical tasks are returned in a separate array.

**Example prompt:** "What is the critical path for project PRJ-001? Include any tasks with fewer than 5 days float as well."

---

### `get_dependencies`

**Module:** pm-data

Retrieve predecessor and/or successor relationships for one task or all tasks in a project.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| task_id | string | No | — | Specific task ID to inspect. If omitted, returns the dependency graph for all tasks. |
| direction | string | No | `both` | Relationship direction to return. One of: `predecessors`, `successors`, `both`. |

**Returns:** A list of dependency relationships, each containing source task ID, target task ID, relationship type (FS/FF/SS/SF), and lag value.

**Example prompt:** "Show me all the predecessors and successors for task T-042 in project PRJ-001."

---

### `convert_format`

**Module:** pm-data

Convert a loaded project to a different output format for export or downstream processing.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| target_format | string | Yes | — | Output format. One of: `mspdi`, `json`, `nista_json`, `nista_csv`. |

**Returns:** The converted file content as a string (JSON or CSV) or base64-encoded XML (`mspdi`). Use `nista_json` or `nista_csv` for NISTA submission payloads, then pass the result to `submit_to_nista`.

**Example prompt:** "Convert project PRJ-001 to NISTA JSON format so I can submit it to the NISTA API."

---

### `get_project_summary`

**Module:** pm-data

Retrieve a high-level summary of a loaded project including task counts, date range, critical path length, and detected source format.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |

**Returns:** Summary object containing: total task count, milestone count, critical path length (tasks and duration), project start and finish dates, baseline dates (if present), resource count, and detected source format.

**Example prompt:** "Give me a top-level summary of project PRJ-001 — how many tasks, what's the end date, and how long is the critical path?"

---

## pm-analyse — AI-Powered Analysis

Six tools applying statistical and AI methods to a loaded project. All tools require a `project_id` from `load_project`. Tools that accept a `depth` parameter consume more compute and return more detailed outputs at `"deep"`.

---

### `identify_risks`

**Module:** pm-analyse

Identify project risks across up to eight risk dimensions using an AI-powered risk engine. Returns structured risk records suitable for use with `suggest_mitigations`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| focus_areas | array | No | all areas | Subset of risk dimensions to analyse. Valid values: `schedule`, `cost`, `resource`, `scope`, `technical`, `external`, `organizational`, `stakeholder`. |
| depth | string | No | `standard` | Analysis depth. One of: `quick`, `standard`, `deep`. `deep` adds full dependency chain analysis. |

**Returns:** A list of risk objects, each with: risk ID, dimension, title, description, likelihood, impact, composite score, and suggested owner. Risk IDs can be passed to `suggest_mitigations`.

**Related tools:** Pass risk IDs to `suggest_mitigations`. Use `assess_health` for an aggregated health view.

**Example prompt:** "Identify all schedule and resource risks in project PRJ-001 using a deep analysis."

---

### `forecast_completion`

**Module:** pm-analyse

Forecast the project completion date using one of five methods, with optional confidence intervals and scenario generation.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| method | string | No | `ml_ensemble` | Forecasting method. One of: `earned_value`, `monte_carlo`, `reference_class`, `simple_extrapolation`, `ml_ensemble`. |
| confidence_level | number | No | `0.80` | Statistical confidence level for the interval. Range: `0.50`–`0.95`. |
| scenarios | boolean | No | `true` | When `true`, generates optimistic, likely, and pessimistic scenario forecasts. |
| depth | string | No | `standard` | Affects Monte Carlo iteration count. One of: `quick`, `standard`, `deep`. |

**Returns:** Forecast completion date, confidence interval bounds, method-specific metrics (e.g. SPI/CPI for earned value, P10/P50/P90 for Monte Carlo), and scenario forecasts if requested.

**Example prompt:** "Forecast when project PRJ-001 will complete using Monte Carlo at 80% confidence, and show me the optimistic, likely, and pessimistic scenarios."

---

### `detect_outliers`

**Module:** pm-analyse

Detect anomalous tasks using statistical analysis across duration, progress, float, and date dimensions. Useful for identifying data quality issues or tasks requiring immediate attention.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| sensitivity | number | No | `1.0` | Detection sensitivity. Range: `0.5` (fewer, high-confidence anomalies) to `2.0` (more anomalies, higher false-positive rate). |
| focus_areas | array | No | all areas | Dimensions to check. Subset of: `duration`, `progress`, `float`, `dates`. |

**Returns:** A list of outlier task objects, each with: task ID, name, anomaly type, observed value, expected range, and a severity rating.

**Example prompt:** "Run outlier detection on project PRJ-001 and flag any tasks with unusual durations or progress values."

---

### `assess_health`

**Module:** pm-analyse

Produce a multi-dimensional health assessment across schedule, cost, scope, resource, and quality dimensions with optional trend analysis.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| include_trends | boolean | No | `true` | When `true`, includes trend direction (improving / stable / declining) for each dimension. |
| weights | object | No | `0.2` each | Custom weighting for health dimensions. Keys: `schedule`, `cost`, `scope`, `resource`, `quality`. Values must sum to `1.0`. |

**Returns:** Overall health score (0.0–1.0), per-dimension scores with RAG ratings, trend directions (if requested), and the top three issues driving the health score.

**Example prompt:** "Assess the health of project PRJ-001, weighting schedule at 40% and cost at 30%, with the remainder split equally across scope, resource, and quality."

---

### `suggest_mitigations`

**Module:** pm-analyse

Generate structured mitigation strategies for identified risks, with effectiveness ratings and implementation steps.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| risk_ids | array | No | — | Specific risk IDs from `identify_risks` to target. If omitted, generates mitigations for all identified risks. |
| focus_areas | array | No | — | Limit mitigations to specific risk dimensions. Subset of: `schedule`, `cost`, `resource`, `scope`, `technical`, `external`. |
| depth | string | No | `standard` | Mitigation detail level. One of: `quick`, `standard`, `deep`. |

**Returns:** A list of mitigation strategy objects, each with: targeted risk ID, strategy title, description, estimated effectiveness rating, implementation steps, and resource implications.

**Related tools:** Run `identify_risks` first to obtain risk IDs.

**Example prompt:** "Suggest mitigations for the schedule risks identified in project PRJ-001, using a deep analysis."

---

### `compare_baseline`

**Module:** pm-analyse

Compare the current project state against a stored baseline to surface schedule, duration, and cost variances, classified by severity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| baseline_type | string | No | `current` | Which baseline to compare against. One of: `current`, `original`, `approved`. |
| threshold | number | No | `0` | Minimum variance percentage to include in results. `0` returns all variances; set higher (e.g. `5`) to suppress noise. |

**Returns:** A variance report listing tasks with start, finish, and duration deviations, cost variance (if baseline cost data is present), severity classifications (minor / moderate / significant / critical), and aggregate project-level variance statistics.

**Example prompt:** "Compare project PRJ-001 against its approved baseline and show me only variances greater than 5%."

---

## pm-validate — Validation

Four tools for validating project data at structural, semantic, regulatory (NISTA), and custom rule levels. All require a `project_id` from `load_project`.

---

### `validate_structure`

**Module:** pm-validate

Validate the structural integrity of project data, checking for orphan tasks, circular dependencies, duplicate IDs, and other data model errors.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| checks | array | No | `["all"]` | Specific checks to run, or `["all"]` to run the full suite. Valid check names: `orphan_tasks`, `circular_dependencies`, `invalid_references`, `duplicate_ids`, `hierarchy_integrity`, `date_consistency`, `assignment_validity`. |

**Returns:** A validation result object with: pass/fail status per check, a list of issues (each with task ID, check name, severity, and description), and an overall pass/fail verdict.

**Example prompt:** "Validate the data structure of project PRJ-001 and flag any circular dependencies or orphan tasks."

---

### `validate_semantic`

**Module:** pm-validate

Validate business rules and scheduling logic, including negative float, resource overallocation, constraint violations, and baseline consistency.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| rules | array | No | `["all"]` | Specific rules to check, or `["all"]` to run the full suite. Valid rule names: `schedule_logic`, `negative_float`, `resource_overallocation`, `constraint_violations`, `cost_consistency`, `baseline_variance`, `milestone_dates`. |
| thresholds | object | No | — | Custom threshold values to override defaults for specific rules (e.g. overallocation percentage, maximum acceptable negative float). |

**Returns:** A rule-by-rule result set with violation details, affected task IDs, and severity ratings.

**Example prompt:** "Check project PRJ-001 for resource overallocation and negative float violations."

---

### `validate_nista`

**Module:** pm-validate

Validate a project against the NISTA Programme and Project Data Standard. Essential for UK government projects required to submit to the Infrastructure and Projects Authority.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| schema_version | string | No | `1.0` | NISTA schema version to validate against. |
| strictness | string | No | `standard` | Validation strictness level. One of: `lenient`, `standard`, `strict`. `strict` enforces all optional fields as required. |

**Returns:** A NISTA compliance report with: overall compliance score (0–100%), field-level pass/fail results, a list of missing or non-compliant data elements, and recommended remediation actions.

**Related tools:** Use `convert_format` with `target_format: "nista_json"` to prepare data for `submit_to_nista` after validation passes.

**Example prompt:** "Run a strict NISTA validation on project PRJ-001 and tell me what I need to fix before submitting to the NISTA API."

---

### `validate_custom`

**Module:** pm-validate

Execute user-defined validation rules against a project, supporting organisation-specific requirements not covered by the standard validators.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier returned by `load_project`. |
| rules | array | Yes | — | List of custom rule definition objects. Each rule object must define the field(s) to inspect, the condition logic, and the error message to surface on failure. |

**Returns:** A list of custom rule results, each with the rule name, pass/fail status, affected task IDs, and the custom error message where the rule fails.

**Example prompt:** "Validate project PRJ-001 against our departmental rules: no task may exceed 20 days duration, and all tasks must have an assigned owner."

---

## pm-nista — GMPP Reporting and NISTA API Integration

Five tools for generating GMPP quarterly returns, producing AI narratives, submitting to the NISTA API, and retrieving NISTA metadata.

---

### `generate_gmpp_report`

**Module:** pm-nista

Generate a complete GMPP quarterly report from a project file, optionally enriched with AI-generated narratives.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_file | string | Yes | — | Path to the source project file (MS Project, GMPP CSV, or other supported format). |
| quarter | string | Yes | — | Reporting quarter. One of: `Q1`, `Q2`, `Q3`, `Q4`. |
| financial_year | string | Yes | — | Financial year in format `YYYY-YY` (e.g. `2025-26`). |
| generate_narratives | boolean | No | `true` | When `true`, generates AI narratives for DCA, cost, schedule, benefits, and risk sections. Requires `ANTHROPIC_API_KEY` environment variable. |

**Returns:** A GMPP quarterly report JSON object conforming to the NISTA schema, ready for submission via `submit_to_nista`. If narratives are generated, each section includes confidence scores.

**Related tools:** Validate the output with `validate_gmpp_report` before calling `submit_to_nista`.

**Example prompt:** "Generate the Q2 2025-26 GMPP quarterly report for the project file at `/data/prj-alpha.mpp`, including AI narratives."

---

### `generate_narrative`

**Module:** pm-nista

Generate an AI-powered narrative for a specific GMPP section with a confidence score, suitable for inclusion in a quarterly return.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| narrative_type | string | Yes | — | Section to generate. One of: `dca`, `cost`, `schedule`, `benefits`, `risk`. |
| project_context | object | Yes | — | Project context data. See sub-fields below. |
| project_context.project_name | string | Yes | — | Full project name. |
| project_context.department | string | No | — | Sponsoring department or organisation. |
| project_context.dca_rating | string | No | — | Current Delivery Confidence Assessment rating (e.g. `Amber`, `Red/Amber`). |
| project_context.baseline_cost | number | No | — | Approved baseline whole-life cost (£). |
| project_context.forecast_cost | number | No | — | Current forecast whole-life cost (£). |
| project_context.cost_variance_percent | number | No | — | Percentage variance between baseline and forecast cost. |

**Returns:** A narrative string, confidence score (0.0–1.0), and flagged uncertainty areas where confidence is low.

**Example prompt:** "Write a GMPP cost narrative for the Horizon Programme, which has an Amber DCA and is currently 8% over its baseline cost."

---

### `submit_to_nista`

**Module:** pm-nista

Submit a GMPP quarterly return to the NISTA API. Supports sandbox and production environments.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| report_file | string | Yes | — | Path to the quarterly report JSON file produced by `generate_gmpp_report`. |
| project_id | string | Yes | — | Project identifier (NISTA project code or internal ID). |
| environment | string | No | `sandbox` | Target API environment. One of: `sandbox`, `production`. Always test in `sandbox` before submitting to `production`. |

**Returns:** NISTA API response including submission reference number, validation status, and any rejection reasons if the submission fails.

**Related tools:** Run `validate_gmpp_report` before submitting to catch errors early.

**Example prompt:** "Submit the quarterly report at `/reports/q2-2025-prj-alpha.json` to the NISTA sandbox for project NISTA-0042."

---

### `fetch_nista_metadata`

**Module:** pm-nista

Retrieve project metadata from the NISTA master registry, including official project details, IPA classifications, and submission history.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | NISTA project code or internal project identifier. |
| environment | string | No | `sandbox` | Registry environment to query. One of: `sandbox`, `production`. |

**Returns:** NISTA master registry record including: project name, department, IPA review point stage, current DCA rating, approved budget, and submission history.

**Example prompt:** "Fetch the NISTA metadata for project NISTA-0042 from the production registry."

---

### `validate_gmpp_report`

**Module:** pm-nista

Validate a GMPP quarterly report JSON file against NISTA schema requirements before submission.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| report_file | string | Yes | — | Path to the quarterly report JSON file to validate. |
| strictness | string | No | `STANDARD` | Validation strictness. One of: `LENIENT`, `STANDARD`, `STRICT`. |

**Returns:** Validation result with: pass/fail status, list of schema violations (field path, error type, description), completeness score, and readiness verdict for submission.

**Example prompt:** "Validate the GMPP report at `/reports/q2-2025-prj-alpha.json` before I submit it to NISTA."

---

## pm-assure — Assurance Lifecycle

Twenty-seven tools covering the full assurance lifecycle, from artefact currency checks (P1) to gate readiness assessments (P14). Most tools persist state to a SQLite store identified by `project_id` and `db_path`.

Use `create_project_from_profile` to register a project in the store before running assurance tools. Use `export_dashboard_data` or `export_dashboard_html` to produce summary outputs.

---

### `nista_longitudinal_trend`

**Module:** pm-assure | **Capability:** P2

Retrieve the history of NISTA compliance scores for a project, the trend direction, and any active threshold breaches.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A time-series of NISTA compliance scores, computed trend direction (improving / stable / declining), and a list of active threshold breaches with breach date and severity.

**Example prompt:** "Show me the NISTA compliance trend for project NISTA-0042 and flag any active threshold breaches."

---

### `track_review_actions`

**Module:** pm-assure | **Capability:** P3

Extract action items from a project review document, persist them, and detect any recurring issues from prior review cycles.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| review_text | string | Yes | — | Full text of the project review document. |
| review_id | string | Yes | — | Unique identifier for this review cycle (e.g. `"IPA-REVIEW-2025-Q2"`). |
| project_id | string | Yes | — | Project identifier in the assurance store. |
| min_confidence | number | No | `0.60` | Confidence threshold below which extracted actions are flagged for human review. Range: `0.0`–`1.0`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A list of extracted actions (each with text, owner, due date if detectable, and confidence score), recurrence flags for actions seen in prior cycles, and a count of actions requiring human review.

**Related tools:** Use `review_action_status` to check the current status of tracked actions.

**Example prompt:** "Extract all actions from this IPA review document for project PRJ-001 and flag any that have appeared in previous reviews."

---

### `review_action_status`

**Module:** pm-assure | **Capability:** P3

Return the current status of all tracked review actions for a project.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** All persisted actions for the project, each with: action text, review cycle of origin, current status (open / in-progress / closed), owner, due date, and recurrence flag.

**Related tools:** Use alongside `track_review_actions`.

**Example prompt:** "What is the current status of all tracked review actions for project PRJ-001?"

---

### `check_artefact_currency`

**Module:** pm-assure | **Capability:** P1

Check whether project artefacts are stale or have been anomalously refreshed relative to a gate deadline.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| artefacts | array | Yes | — | List of artefact objects to check. Each object must include: `id` (string), `type` (string, e.g. `"business_case"`), `last_modified` (ISO-8601 datetime string). |
| gate_date | string | Yes | — | ISO-8601 date of the upcoming gate deadline (e.g. `"2025-09-30"`). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Per-artefact currency status (current / stale / anomalously refreshed), days since last modification, and a recommended action for each artefact. Also flags artefacts updated suspiciously close to the gate date.

**Example prompt:** "Check whether the business case, risk register, and schedule for project PRJ-001 are current ahead of the Gate 2 review on 30 September 2025."

---

### `check_confidence_divergence`

**Module:** pm-assure | **Capability:** P4

Detect when AI extraction confidence samples diverge or consensus declines across review cycles, indicating increasing data uncertainty.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confidence divergence report including: variance trend across cycles, current consensus score, divergence severity, and the specific extraction areas showing the greatest spread.

**Example prompt:** "Check whether AI extraction confidence has been diverging across recent review cycles for project PRJ-001."

---

### `recommend_review_schedule`

**Module:** pm-assure | **Capability:** P5

Generate an adaptive review scheduling recommendation based on aggregated P1–P4 assurance signals.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| last_review_date | string | No | — | ISO-8601 date of the most recent completed review. |
| artefacts | array | No | — | Artefact list (same format as `check_artefact_currency`) for an inline P1 currency check. |
| gate_date | string | No | — | ISO-8601 date of the next gate, used to anchor scheduling recommendations. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A recommended next review date, review intensity level (light-touch / standard / intensive), rationale based on current assurance signals, and a suggested review agenda focus areas.

**Example prompt:** "Based on the current assurance signals for project PRJ-001, when should we schedule the next review and how intensive should it be?"

---

### `log_override_decision`

**Module:** pm-assure | **Capability:** P6

Record a structured governance override decision with rationale and approver details for audit trail purposes.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| decision_type | string | Yes | — | Category of override decision (e.g. `"gate_progression"`, `"risk_acceptance"`, `"cost_variation"`). |
| rationale | string | Yes | — | Full written justification for the override. |
| approver | string | Yes | — | Name and/or role of the approving authority. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation of the logged decision with a generated decision ID, timestamp, and the persisted record for audit trail purposes.

**Related tools:** Use `analyse_override_patterns` to identify systemic override trends.

**Example prompt:** "Log a gate progression override decision for project PRJ-001, approved by the SRO, with the rationale that strategic urgency outweighs the incomplete OBC."

---

### `analyse_override_patterns`

**Module:** pm-assure | **Capability:** P6

Analyse the history of override decisions for a project to surface patterns, frequency trends, and potential systemic governance issues.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Override frequency by decision type, trend analysis (increasing / stable / decreasing), identification of recurring decision categories, and a governance health indicator.

**Related tools:** Use alongside `log_override_decision`.

**Example prompt:** "Analyse the override decision history for project PRJ-001 and tell me if there are any concerning patterns."

---

### `ingest_lesson`

**Module:** pm-assure | **Capability:** P7

Register a structured lesson learned in the knowledge engine, making it searchable by future projects.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| title | string | Yes | — | Concise lesson title. |
| description | string | Yes | — | Full lesson description, including context, what happened, and the recommendation. |
| category | string | No | — | Lesson category (e.g. `"procurement"`, `"technology"`, `"stakeholder_management"`). |
| tags | array | No | — | List of keyword strings for search indexing. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation with the generated lesson ID for future cross-referencing.

**Related tools:** Use `search_lessons` to retrieve lessons by keyword or semantic query.

**Example prompt:** "Ingest a lessons learned entry for project PRJ-001: the procurement process took twice as long as planned because the ITT was issued without legal sign-off."

---

### `search_lessons`

**Module:** pm-assure | **Capability:** P7

Search the lessons learned knowledge base by keyword or semantic query, optionally scoped to a specific project.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | — | Search query string. Supports keyword and semantic search. |
| project_id | string | No | — | Limit results to lessons from a specific project. If omitted, searches across all projects. |
| limit | integer | No | `10` | Maximum number of results to return. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A ranked list of matching lessons, each with: lesson ID, title, description, project of origin, category, tags, and a relevance score.

**Example prompt:** "Search the lessons learned database for anything related to procurement delays."

---

### `log_assurance_activity`

**Module:** pm-assure | **Capability:** P8

Log an assurance activity with effort hours, outcome, and confidence data to support overhead analysis.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| activity_type | string | Yes | — | Type of assurance activity (e.g. `"document_review"`, `"interview"`, `"data_validation"`, `"narrative_generation"`). |
| effort_hours | number | Yes | — | Hours spent on this activity. |
| outcome | string | No | — | Description of the activity outcome or findings. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation with the generated activity ID and a running total of effort logged for this project.

**Related tools:** Use `analyse_assurance_overhead` to summarise effort distribution.

**Example prompt:** "Log that I spent 3.5 hours reviewing the business case documents for project PRJ-001."

---

### `analyse_assurance_overhead`

**Module:** pm-assure | **Capability:** P8

Analyse the distribution of assurance effort across activity types, identify potential waste, and measure confidence outcomes per activity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Effort breakdown by activity type (hours and percentage), identification of high-effort/low-confidence activities, benchmark comparisons, and overhead reduction recommendations.

**Related tools:** Use alongside `log_assurance_activity`.

**Example prompt:** "Analyse the assurance overhead for project PRJ-001 and tell me which activities are consuming the most time relative to their value."

---

### `run_assurance_workflow`

**Module:** pm-assure | **Capability:** P9

Execute a deterministic multi-step assurance workflow that sequences P1–P8 capabilities with inter-step data passing.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| workflow_id | string | No | — | Named workflow to execute. If omitted, runs the default P1–P8 sequence. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A workflow execution record with: steps executed, outputs from each step, inter-step data flows, overall success/failure status, and a consolidated findings summary.

**Related tools:** Use `get_workflow_history` to review past executions.

**Example prompt:** "Run the full default assurance workflow for project PRJ-001."

---

### `get_workflow_history`

**Module:** pm-assure | **Capability:** P9

Retrieve past assurance workflow execution records for a project, enabling comparison across runs.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A list of past workflow executions, each with: execution ID, timestamp, workflow ID, steps executed, overall status, and key findings summary.

**Related tools:** Use alongside `run_assurance_workflow`.

**Example prompt:** "Show me the history of all assurance workflows run for project PRJ-001."

---

### `classify_project_domain`

**Module:** pm-assure | **Capability:** P10

Classify a project into a Cynefin complexity domain (Simple, Complicated, Complex, Chaotic) and receive a tailored assurance profile for that domain.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Cynefin domain classification with confidence score, classification rationale, and a recommended assurance profile specifying appropriate review cadence, methods, and emphasis areas for the detected domain.

**Related tools:** Use `reclassify_from_store` to re-run classification after new data is ingested without supplying project inputs again.

**Example prompt:** "Classify project PRJ-001 into a Cynefin domain and recommend an appropriate assurance approach."

---

### `reclassify_from_store`

**Module:** pm-assure | **Capability:** P10

Re-run domain classification using data already held in the assurance store, without requiring re-submission of project inputs.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Updated Cynefin classification with any changes from the previous classification highlighted, including the reason for reclassification if the domain has shifted.

**Related tools:** Use after ingesting new lessons, risks, or assurance data to update the classification.

**Example prompt:** "Re-run the domain classification for project PRJ-001 using the latest data in the store."

---

### `ingest_assumption`

**Module:** pm-assure | **Capability:** P11

Register a new assumption with its baseline value for ongoing drift tracking.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| title | string | Yes | — | Concise assumption title. |
| description | string | Yes | — | Full description of the assumed state. |
| baseline_value | string | No | — | The original assumed state or value at time of registration. |
| owner | string | No | — | Name or role of the assumption owner. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation with the generated `assumption_id`, which is required for subsequent validation and cascade impact calls.

**Related tools:** Use `validate_assumption` to record checks against this assumption. Use `get_assumption_drift` to view drift status. Use `get_cascade_impact` to understand downstream effects.

**Example prompt:** "Register an assumption for project PRJ-001: we assume the land acquisition will complete by March 2026 at an estimated cost of £2.4m."

---

### `validate_assumption`

**Module:** pm-assure | **Capability:** P11

Record a validation check against an existing assumption, updating its status and tracking drift from baseline.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| assumption_id | string | Yes | — | ID of the assumption returned by `ingest_assumption`. |
| current_value | string | Yes | — | The currently observed state or value of the assumption. |
| is_still_valid | boolean | Yes | — | `true` if the assumption remains valid; `false` if it has been invalidated. |
| notes | string | No | — | Contextual notes on the validation check. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Updated assumption record with drift status (none / minor / moderate / significant), validation history entry, and a flag if the assumption has been invalidated (triggering cascade impact review).

**Related tools:** Use `get_cascade_impact` if an assumption is invalidated to understand downstream risk.

**Example prompt:** "Validate assumption ASM-007: the land acquisition is now expected to cost £3.1m, which exceeds the baseline. Mark it as no longer valid."

---

### `get_assumption_drift`

**Module:** pm-assure | **Capability:** P11

Retrieve all assumptions for a project with their current drift status and full validation history.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A list of all registered assumptions, each with: title, baseline value, current value, drift severity, validity status, owner, and a chronological validation history.

**Example prompt:** "Show me the drift status of all assumptions for project PRJ-001."

---

### `get_cascade_impact`

**Module:** pm-assure | **Capability:** P11

Identify all risks, benefits, and decisions that are downstream of a specific assumption in the dependency network.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| assumption_id | string | Yes | — | ID of the assumption returned by `ingest_assumption`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A dependency graph of all items linked to the assumption, including: dependent risks (with IDs and titles), dependent benefits (with IDs and titles), and any decisions recorded against the assumption. Each item includes its depth from the source assumption.

**Example prompt:** "If assumption ASM-007 is invalidated, what risks and benefits are affected downstream?"

---

### `create_project_from_profile`

**Module:** pm-assure

Create a project record in the assurance store from a structured profile. Run this before using any pm-assure or pm-brm tools on a new project.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Stable project identifier to use across the assurance store. |
| profile | object | Yes | — | Structured project profile data (e.g. project name, department, IPA stage, SRO, budget, start date, end date). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation that the project record has been created in the store, ready for use by all pm-assure and pm-brm tools.

**Example prompt:** "Register project PRJ-001 in the assurance store with the profile details from our project initiation document."

---

### `export_dashboard_data`

**Module:** pm-assure

Export a structured JSON payload containing all assurance data for a project, suitable for rendering in a custom dashboard.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A JSON object containing: assurance scores per capability (P1–P14), workflow history, assumption drift summary, override decision count, lessons learned count, NISTA compliance trend, and gate readiness scores.

**Related tools:** Use `export_dashboard_html` to produce a rendered, self-contained HTML version.

**Example prompt:** "Export all assurance dashboard data for project PRJ-001 as JSON."

---

### `export_dashboard_html`

**Module:** pm-assure

Generate a self-contained HTML assurance dashboard for a project, with no external dependencies.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A self-contained HTML string that can be written to a file and opened in any browser. Includes all assurance metrics, charts, and summaries with no external CSS or JavaScript dependencies.

**Example prompt:** "Generate an HTML assurance dashboard for project PRJ-001 that I can share with the project board."

---

### `get_armm_report`

**Module:** pm-assure | **Capability:** P12

Generate a full Agent Readiness Maturity Model (ARMM) assessment across 4 dimensions, 28 topics, and 251 criteria.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Full ARMM report with: maturity scores per dimension and topic, pass/fail status per criterion, overall ARMM maturity level, priority improvement areas, and a recommended capability development roadmap.

**Example prompt:** "Run a full ARMM assessment for project PRJ-001 and identify the highest-priority maturity gaps."

---

### `assess_gate_readiness`

**Module:** pm-assure | **Capability:** P14

Run a full gate readiness assessment synthesising data from all assurance modules (P1–P12). Returns a composite readiness score, an 8-dimension breakdown with gate-specific weighting, blocking issues, and prioritised recommendations.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| gate | string | Yes | — | IPA review point. One of: `GATE_0`, `GATE_1`, `GATE_2`, `GATE_3`, `GATE_4`, `GATE_5`, `PAR`. See gate descriptions below. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Gate reference:**

| Gate | IPA Stage |
|------|-----------|
| `GATE_0` | Opportunity Framing |
| `GATE_1` | Strategic Outline Case (SOC) |
| `GATE_2` | Outline Business Case (OBC) |
| `GATE_3` | Full Business Case (FBC) |
| `GATE_4` | Readiness for Service |
| `GATE_5` | Operations Review |
| `PAR` | Project Assessment Review |

**Returns:** Composite readiness score (0.0–1.0), per-dimension scores weighted for the specified gate, a list of blocking issues that must be resolved before progression, and prioritised recommendations.

**Related tools:** Use `get_gate_readiness_history` to view progression over time. Use `compare_gate_readiness` to compare two assessments.

**Example prompt:** "Assess Gate 2 readiness for project PRJ-001 and tell me what blocking issues need to be resolved before the OBC review."

---

### `get_gate_readiness_history`

**Module:** pm-assure | **Capability:** P14

Retrieve past gate readiness assessments for a project to track progression over time.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| gate | string | No | — | Filter to a specific gate type. Same values as `assess_gate_readiness`. If omitted, returns assessments for all gates. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A chronological list of gate readiness assessments, each with: assessment ID, gate type, timestamp, composite score, dimension scores, and blocking issue count.

**Example prompt:** "Show me the history of all Gate 2 readiness assessments for project PRJ-001 so I can see how we've improved."

---

### `compare_gate_readiness`

**Module:** pm-assure | **Capability:** P14

Compare two gate readiness assessments to quantify improvement or regression — score delta, improved/degraded dimensions, and resolved/new blocking issues.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| assessment_id_before | string | Yes | — | ID of the earlier assessment (from `get_gate_readiness_history` or `assess_gate_readiness`). |
| assessment_id_after | string | Yes | — | ID of the later assessment. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Score delta (positive = improvement), per-dimension comparison (improved / unchanged / degraded), list of blocking issues resolved between assessments, list of new blocking issues introduced, and an overall progression verdict.

**Related tools:** Use `get_gate_readiness_history` to find assessment IDs.

**Example prompt:** "Compare the Gate 2 readiness assessments from last month and this month for project PRJ-001 and show me what has improved."

---

## pm-brm — Benefits Realisation Management

Ten tools implementing a full Benefits Realisation Management lifecycle, aligned to IPA, HM Treasury Green Book, Ward & Daniel, MSP, and P3M3 frameworks. All tools persist state to the assurance store. This module corresponds to assurance capability P13.

Use `ingest_benefit` to register benefits before using measurement, forecasting, or dependency tools.

---

### `ingest_benefit`

**Module:** pm-brm | **Capability:** P13

Register a benefit or dis-benefit with full IPA/Green Book-compliant metadata. Supports multi-axis classification across financial type, recipient type, and explicitness.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| title | string | Yes | — | Clear, concise benefit name. |
| description | string | Yes | — | Narrative meeting the MSP DOAM test: Described, Observable, Attributable, Measurable. |
| financial_type | string | Yes | — | Green Book financial classification. One of: `CASH_RELEASING`, `NON_CASH_RELEASING`, `QUANTIFIABLE`, `QUALITATIVE`. |
| recipient_type | string | Yes | — | IPA recipient classification. One of: `GOVERNMENT`, `PRIVATE_SECTOR`, `WIDER_UK_PUBLIC`. |
| is_disbenefit | boolean | No | `false` | Set to `true` to register a dis-benefit (negative outcome). |
| baseline_value | number | No | — | Current performance level before the change intervention. |
| baseline_date | string | No | — | ISO-8601 date when the baseline was established. |
| target_value | number | No | — | Desired end-state performance level. |
| target_date | string | No | — | ISO-8601 deadline for achieving the target value. |
| measurement_kpi | string | No | — | Specific KPI used to track realisation (e.g. `"Average processing time (days)"`). |
| measurement_frequency | string | No | `QUARTERLY` | How often the benefit is measured. One of: `MONTHLY`, `QUARTERLY`, `ANNUALLY`. |
| indicator_type | string | No | `LAGGING` | Whether the KPI is a leading or lagging indicator. One of: `LEADING`, `LAGGING`. |
| explicitness | string | No | `QUANTIFIABLE` | Ward & Daniel explicitness classification. One of: `FINANCIAL`, `QUANTIFIABLE`, `MEASURABLE`, `OBSERVABLE`. |
| owner_sro | string | No | — | Senior Responsible Owner name or role. |
| benefits_owner | string | No | — | Operational owner responsible post-BAU transition. |
| ipa_lifecycle_stage | string | No | `IDENTIFY_QUANTIFY` | IPA Benefits Management lifecycle stage. One of: `DEFINE_SUCCESS`, `IDENTIFY_QUANTIFY`, `VALUE_APPRAISE`, `PLAN_REALISE`, `REVIEW`. |
| interim_targets | array | No | — | Time-phased interim targets. Each item: `{"date": "YYYY-MM-DD", "value": number}`. |
| contributing_projects | array | No | — | IDs of other projects contributing to this benefit. |
| associated_assumptions | array | No | — | Assumption IDs from `ingest_assumption` linked to this benefit. |
| associated_risks | array | No | — | Risk register IDs linked to this benefit. |
| business_case_ref | string | No | — | Reference to the business case section where this benefit is documented. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation with the generated `benefit_id`, which is required for measurement, forecasting, and dependency mapping calls.

**Example prompt:** "Register a new cash-releasing benefit for project PRJ-001: reduction in manual processing time from 15 days to 3 days by March 2027, measured quarterly, owned by the Head of Operations."

---

### `track_benefit_measurement`

**Module:** pm-brm | **Capability:** P13

Record a measurement against a registered benefit. Automatically computes realisation percentage, drift from baseline, trend direction, and drift severity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| benefit_id | string | Yes | — | Benefit ID returned by `ingest_benefit`. |
| value | number | Yes | — | The measured value at this point in time. |
| source | string | No | `MANUAL` | Data source for this measurement. One of: `MANUAL`, `EXTERNAL_API`, `DERIVED`. |
| notes | string | No | — | Contextual notes on this measurement (e.g. caveats, data quality issues). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Updated benefit record with: realisation percentage, drift from baseline (absolute and percentage), trend direction (improving / stable / declining), drift severity classification, and progress against any interim targets.

**Related tools:** Run `ingest_benefit` first to obtain a `benefit_id`. Use `detect_benefits_drift` for a portfolio-level drift view.

**Example prompt:** "Record a measurement for benefit BEN-003: average processing time is now 8 days as of Q2 2025."

---

### `get_benefits_health`

**Module:** pm-brm | **Capability:** P13

Portfolio-level benefits health assessment covering realisation rates, at-risk benefits, stale measurements, and leading indicator warnings.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| status_filter | string | No | — | Filter to benefits at a specific lifecycle status. One of: `IDENTIFIED`, `PLANNED`, `REALIZING`, `ACHIEVED`, `EVAPORATED`, `CANCELLED`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Overall benefits health score (0.0–1.0), count and percentage of benefits on/off track, list of at-risk benefits with reasons, benefits with stale or missing measurements, leading indicator warnings, and a portfolio-level realisation rate.

**Example prompt:** "Give me a health assessment of all benefits for project PRJ-001 and flag any that are at risk."

---

### `map_benefit_dependency`

**Module:** pm-brm | **Capability:** P13

Create nodes and a typed edge in the benefits dependency directed acyclic graph (DAG). Supports six node types and validates acyclicity before persisting.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| source_node_id | string | Yes | — | ID of the source node in the dependency relationship. |
| target_node_id | string | Yes | — | ID of the target node in the dependency relationship. |
| edge_type | string | Yes | — | Relationship type. One of: `DEPENDS_ON`, `CONTRIBUTES_TO`, `ENABLES`. |
| source_node | object | No | — | Inline node creation. Required fields: `node_type` (one of: `STRATEGIC_OBJECTIVE`, `END_BENEFIT`, `INTERMEDIATE_BENEFIT`, `BUSINESS_CHANGE`, `ENABLER`, `PROJECT_OUTPUT`), `title`. |
| target_node | object | No | — | Inline node creation (same fields as `source_node`). |
| assumption_id | string | No | — | Link this edge to an assumption tracker entry from `ingest_assumption`. |
| risk_id | string | No | — | Link this edge to a risk register entry. |
| notes | string | No | — | Notes on the nature of this dependency relationship. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Confirmation of the created edge with node and edge IDs. Returns an error if the new edge would introduce a cycle in the DAG.

**Related tools:** Use `get_benefit_dependency_network` to view the full graph.

**Example prompt:** "Map a dependency in project PRJ-001: the 'Digital Case Management' project output enables the 'Reduced Processing Time' intermediate benefit."

---

### `get_benefit_dependency_network`

**Module:** pm-brm | **Capability:** P13

Return the full or filtered benefits dependency graph, including all nodes with types and statuses, and all edges with relationship types.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| node_type_filter | string | No | — | Return only nodes of this type. One of: `STRATEGIC_OBJECTIVE`, `END_BENEFIT`, `INTERMEDIATE_BENEFIT`, `BUSINESS_CHANGE`, `ENABLER`, `PROJECT_OUTPUT`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Graph object with: array of node objects (ID, type, title, realisation status), array of edge objects (source ID, target ID, edge type, linked assumption/risk IDs), and summary statistics (node count by type, edge count by type).

**Example prompt:** "Show me the full benefits dependency network for project PRJ-001, filtered to end benefits and intermediate benefits only."

---

### `forecast_benefit_realisation`

**Module:** pm-brm | **Capability:** P13

Project forward from the current measurement trajectory using linear extrapolation. Returns the projected value at the target date and the estimated probability of achieving the target.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| benefit_id | string | Yes | — | Benefit ID returned by `ingest_benefit`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Projected value at the benefit's target date, estimated probability of achieving the target value (0.0–1.0), trajectory chart data points, and a confidence rating for the forecast based on measurement data volume and consistency.

**Related tools:** Run `track_benefit_measurement` at least twice to obtain a meaningful trajectory before forecasting.

**Example prompt:** "Forecast whether benefit BEN-003 is likely to achieve its target of 3-day processing time by March 2027 based on current trajectory."

---

### `detect_benefits_drift`

**Module:** pm-brm | **Capability:** P13

Time-series analysis detecting statistically significant deviations from planned realisation profiles across all benefits in a project. Returns drift severity per benefit, sorted worst-first.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| severity_filter | string | No | — | Return only benefits at or above this drift severity. One of: `NONE`, `MINOR`, `MODERATE`, `SIGNIFICANT`, `CRITICAL`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Ranked list of benefits with drift analysis, each including: benefit ID, title, drift severity, current vs. planned realisation percentage, deviation from planned trajectory, and recommended action.

**Example prompt:** "Detect all benefits for project PRJ-001 with significant or critical drift from their planned realisation profiles."

---

### `get_benefits_cascade_impact`

**Module:** pm-brm | **Capability:** P13

Propagate a change through the benefits dependency DAG and return all downstream nodes affected, with their types and depth from the source node.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| node_id | string | Yes | — | ID of the starting node from which to propagate impact. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** A depth-first list of all downstream nodes, each with: node ID, title, node type, realisation status, and depth from the source node. Useful for understanding the ripple effect of a project output change or benefit invalidation.

**Related tools:** Use `map_benefit_dependency` to build the network before running cascade analysis.

**Example prompt:** "If the 'Digital Case Management' output is delayed, what downstream benefits and objectives are affected?"

---

### `generate_benefits_narrative`

**Module:** pm-brm | **Capability:** P13

Generate an IPA-compliant benefits assurance narrative for gate reviews. Uses multi-sample AI consensus with confidence scoring. Requires the `ANTHROPIC_API_KEY` environment variable.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| gate_number | integer | No | — | IPA gate number (0–5). `0` = Opportunity Framing, `1` = SOC, `2` = OBC, `3` = FBC, `4` = Work to Realise, `5` = Benefits Review. If omitted, generates a general narrative. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Gate-appropriate narrative text, consensus confidence score (0.0–1.0), flagged uncertainty areas, and a suggested review point for sections with low confidence.

**Example prompt:** "Write an IPA-compliant Gate 2 benefits assurance narrative for project PRJ-001 for inclusion in the OBC review pack."

---

### `assess_benefits_maturity`

**Module:** pm-brm | **Capability:** P13

Score benefits management maturity against P3M3-aligned criteria at levels 1–5. Evaluates data completeness, process maturity, dependency mapping quality, and measurement tracking rigour.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier in the assurance store. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite assurance store. |

**Returns:** Overall maturity level (1–5), per-criterion scores with evidence and gap analysis, priority improvement recommendations ranked by impact, and a maturity roadmap showing what is required to reach the next level.

**Example prompt:** "Assess the benefits management maturity for project PRJ-001 and tell me what we need to do to reach P3M3 Level 3."

---

## pm-portfolio — Portfolio Intelligence

Five tools for cross-project portfolio aggregation, health rollup, and systemic risk detection. All tools accept a `project_ids` array (list of project identifier strings) and an optional `db_path`.

---

### `get_portfolio_health`
**Module:** pm-portfolio

Aggregate delivery confidence across multiple projects. Returns overall portfolio DCA distribution (count and percentage at each rating), the worst-performing projects, portfolio-level trend, and a plain-English executive summary.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers to include in the portfolio. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** DCA distribution (Green/Amber-Green/Amber/Amber-Red/Red counts), ranked project list by delivery confidence, portfolio trend direction, and executive summary narrative.

**Example prompt:** "Give me a portfolio health summary across projects ALPHA, BETA, and GAMMA for the investment committee."

---

### `get_portfolio_gate_readiness`
**Module:** pm-portfolio

Return gate readiness scores and upcoming gate dates for all projects in the portfolio. Ranks projects from most to least ready for their next gate.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Per-project gate readiness score (0.0–1.0), target gate, readiness status, blocking issues, and a ranked portfolio view.

**Example prompt:** "Which of my projects are most at risk of failing their next gate review?"

---

### `get_portfolio_brm_overview`
**Module:** pm-portfolio

Aggregate benefits realisation status across the portfolio. Returns total approved benefits value, percentage on track/at risk/off track, and projects with the greatest benefit exposure.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Portfolio-level benefit totals, at-risk benefit value, per-project benefit confidence summary.

**Example prompt:** "What is the total value of benefits at risk across the portfolio?"

---

### `get_portfolio_armm_summary`
**Module:** pm-portfolio

Return ARMM (Agent Readiness Maturity Model) maturity distribution across the portfolio. Identifies projects at each maturity level (0–4) and surfaces common blocking topics.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** ARMM maturity distribution, average maturity score, common blocking topics across projects.

**Example prompt:** "What is the AI readiness maturity of our project portfolio?"

---

### `get_portfolio_assumptions_risk`
**Module:** pm-portfolio

Identify assumptions that are drifting across multiple projects simultaneously. Surfaces systemic assumption risk — shared external dependencies or common planning assumptions that, if wrong, would affect the whole portfolio.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Assumptions drifting across multiple projects, drift severity, and whether shared drift patterns indicate a systemic portfolio-level risk.

**Example prompt:** "Are any assumptions drifting across multiple projects simultaneously — is there a shared dependency we're all relying on?"

---

## pm-ev — Earned Value Analysis

Two tools for Earned Value Management analysis. EV tools require PV (Planned Value), EV (Earned Value), and AC (Actual Cost) data to be supplied or ingested from the project's financial records.

---

### `compute_ev_metrics`
**Module:** pm-ev

Compute the full Earned Value metric set from PV, EV, and AC inputs. Returns SPI, CPI, SV, CV, EAC, ETC, VAC, and TCPI with plain-English interpretation of each metric.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| planned_value | number | Yes | — | Budgeted cost of work scheduled (BCWS) to date. |
| earned_value | number | Yes | — | Budgeted cost of work performed (BCWP) to date. |
| actual_cost | number | Yes | — | Actual cost of work performed (ACWP) to date. |
| budget_at_completion | number | Yes | — | Total approved project budget (BAC). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** SPI, CPI, SV (Schedule Variance), CV (Cost Variance), EAC (Estimate at Completion), ETC (Estimate to Complete), VAC (Variance at Completion), TCPI (To-Complete Performance Index), with interpretation flags (e.g. `cpi_alert: true` when CPI < 0.9).

**Example prompt:** "Compute Earned Value metrics for Project Alpha: PV=£2.4m, EV=£2.1m, AC=£2.6m, BAC=£8m."

---

### `generate_ev_dashboard`
**Module:** pm-ev

Generate a self-contained HTML Earned Value dashboard with S-curves (planned vs actual vs earned value over time), key metric cards, and trend indicators. Suitable for inclusion in board packs or reporting portals.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| output_path | string | No | — | File path to write the HTML file. If omitted, returns HTML as a string. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Self-contained HTML string or file path confirmation. The dashboard includes S-curves, SPI/CPI gauge charts, EAC vs BAC comparison, and a TCPI indicator.

**Example prompt:** "Generate an Earned Value dashboard for Project Beta and save it to `/reports/ev-dashboard.html`."

---

## pm-synthesis — AI Health Summaries

Two tools for AI-generated executive health summaries. These tools draw on data from all other modules to produce synthesised, narrative outputs. Requires `ANTHROPIC_API_KEY` to be set.

---

### `summarise_project_health`
**Module:** pm-synthesis

Generate an AI executive health summary for a project, synthesising data from schedule, risk, financial, benefits, and assurance modules. Output is calibrated for a non-technical audience.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| audience | string | No | `SRO` | Target audience for tone and content calibration. One of: `SRO`, `PMO`, `BOARD`. |
| sections | array of strings | No | all | Specific sections to include. Options: `schedule`, `cost`, `risk`, `benefits`, `assurance`, `recommendations`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Structured executive summary with overall confidence rating, section-by-section assessment, key findings, and prioritised recommended actions. Includes a data completeness indicator showing which modules had sufficient data.

**Example prompt:** "Produce a board-ready health summary for Project Alpha, focusing on schedule, cost, and benefits."

---

### `compare_project_health`
**Module:** pm-synthesis

Compare health summaries across multiple projects and produce a ranked comparative analysis. Useful for portfolio reviews, investment committees, and assurance prioritisation.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers to compare (minimum 2, maximum 10). |
| comparison_dimensions | array of strings | No | all | Dimensions to compare. Options: `schedule`, `cost`, `risk`, `benefits`, `assurance`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Ranked project list by overall health, dimension-by-dimension comparison table, narrative identifying which projects are leading/lagging and why, and recommendations for where to focus assurance resource.

**Example prompt:** "Compare the health of projects ALPHA, BETA, and GAMMA and tell me which needs the most urgent attention."

---

## pm-risk — Risk Register and Intelligence

Nine tools for risk management aligned to IPA/MoR taxonomy. All risk tools use the AssuranceStore SQLite database via the optional `db_path` parameter.

**Risk scoring:** `risk_score = likelihood × impact`. Verbal ratings: LOW (1–6), MEDIUM (7–12), HIGH (13–19), CRITICAL (20–25).

**Likelihood scale:** 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain.

**Impact scale:** 1=Negligible, 2=Minor, 3=Moderate, 4=Major, 5=Catastrophic.

---

### `ingest_risk`
**Module:** pm-risk

Register a new risk in the project risk register. Computes `risk_score` automatically from likelihood × impact.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| title | string | Yes | — | Concise risk title. |
| description | string | No | — | Narrative explaining the risk, its cause, and potential consequences. |
| category | string | No | `DELIVERY` | IPA-aligned category. One of: `DELIVERY`, `FINANCIAL`, `STRATEGIC`, `LEGAL`, `REPUTATIONAL`, `TECHNICAL`, `RESOURCE`. |
| likelihood | integer | No | `3` | Likelihood score 1–5. |
| impact | integer | No | `3` | Impact score 1–5. |
| owner | string | No | — | Risk owner name or role. |
| target_date | string | No | — | Target date for mitigation. Format: `YYYY-MM-DD`. |
| proximity | string | No | — | How close the risk is to materialising. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Risk ID, computed risk_score, verbal rating, and confirmation.

**Example prompt:** "Log a new TECHNICAL risk for Project Alpha: our key integration supplier has indicated they may not be able to resource the contract. Likelihood 4, Impact 4."

---

### `update_risk_status`
**Module:** pm-risk

Update the status of an existing risk (OPEN → MITIGATED → CLOSED) and optionally update its likelihood, impact, or notes.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| risk_id | string | Yes | — | Risk identifier returned by `ingest_risk`. |
| status | string | Yes | — | New status. One of: `OPEN`, `MITIGATED`, `CLOSED`, `ACCEPTED`. |
| notes | string | No | — | Notes on the status change. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Updated risk record.

**Example prompt:** "Mark risk RSK-042 as MITIGATED — the supplier has confirmed resourcing."

---

### `get_risk_register`
**Module:** pm-risk

Retrieve the full risk register for a project with optional filters by status, category, and minimum score.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| status_filter | string | No | `OPEN` | Filter by status. One of: `OPEN`, `MITIGATED`, `CLOSED`, `ACCEPTED`, `ALL`. |
| category_filter | string | No | — | Filter by category (e.g. `FINANCIAL`). |
| min_score | integer | No | — | Return only risks with risk_score ≥ this value. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Sorted risk list (highest score first) with full risk details, summary statistics, and count by category.

**Example prompt:** "Show me all open HIGH and CRITICAL risks for Project Beta."

---

### `get_risk_heat_map`
**Module:** pm-risk

Generate a 5×5 probability-impact heat map for a project's open risks. Groups risks by likelihood/impact cell.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** 5×5 heat map grid with risk counts per cell, risk distribution summary, and risks in the CRITICAL zone (top-right quadrant).

**Example prompt:** "Show me the risk heat map for Project Alpha — I need to present it to the project board."

---

### `ingest_mitigation`
**Module:** pm-risk

Log a mitigation action for an existing risk. Tracks planned, in-progress, and completed mitigations separately from the risk itself.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| risk_id | string | Yes | — | Risk identifier. |
| project_id | string | Yes | — | Project identifier. |
| action | string | Yes | — | Description of the mitigation action. |
| owner | string | No | — | Person or role responsible for this mitigation. |
| target_date | string | No | — | Target completion date. Format: `YYYY-MM-DD`. |
| status | string | No | `PLANNED` | Mitigation status. One of: `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`. |
| residual_likelihood | integer | No | — | Expected likelihood after mitigation (1–5). |
| residual_impact | integer | No | — | Expected impact after mitigation (1–5). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Mitigation ID, residual risk score (if residuals supplied), confirmation.

**Example prompt:** "Log a mitigation for risk RSK-042: engage a backup supplier by 30 June. Owner: Commercial Manager."

---

### `get_mitigation_progress`
**Module:** pm-risk

Return all mitigation actions for a project, grouped by risk, with progress tracking and overdue flagging.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Per-risk mitigation summary (count, completion rate, overdue actions), portfolio totals, and a list of all overdue mitigations requiring attention.

**Example prompt:** "Which risk mitigations are overdue on Project Beta?"

---

### `get_portfolio_risks`
**Module:** pm-risk

Aggregate risks across multiple projects to identify shared risk themes, systemic exposures, and cross-project risk concentration.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| min_score | integer | No | `6` | Minimum risk_score to include. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Aggregated risk count by category and score band, projects with highest risk concentration, risks appearing as HIGH/CRITICAL across multiple projects (systemic risk indicators).

**Example prompt:** "Which risk categories appear most frequently across the portfolio? Are there systemic risks we should be managing centrally?"

---

### `get_risk_velocity`
**Module:** pm-risk

Analyse how individual risk scores are changing over successive review cycles. Returns risks categorised as accelerating (score increasing), decelerating (score decreasing), stable, or with insufficient history.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| min_history_entries | integer | No | `2` | Minimum history entries required to compute velocity. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Risks grouped by velocity (accelerating/decelerating/stable/insufficient-data), with current score, score at first entry, total delta, and recent delta. Accelerating risks sorted by current score (worst first).

**Example prompt:** "Which risks on Project Alpha are accelerating? I want to know which ones are getting worse before the score formally changes."

---

### `detect_stale_risks`
**Module:** pm-risk

Identify compliance-not-management patterns in the risk register. Returns a stale register score (0–100) and categorised lists of risks that have not been updated recently, risks whose scores have not changed across multiple cycles, and high-scoring risks with no active mitigation.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| stale_days | integer | No | `28` | Days without update before a risk is considered stale. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Stale register score (0=fully active, 100=completely stale), counts by staleness type, categorised risk lists, plain-English interpretation, and recommended actions.

**Example prompt:** "Is our risk register being actively managed or just maintained for compliance? Give me a stale register assessment."

---

## pm-change — Change Control

Five tools for structured change control, impact analysis, and change pressure detection. All tools use the AssuranceStore via optional `db_path`.

---

### `log_change_request`
**Module:** pm-change

Log a new change request with type classification, impact assessment, and governance routing.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| title | string | Yes | — | Concise change request title. |
| description | string | No | — | Detailed description of the proposed change. |
| change_type | string | Yes | — | Change category. One of: `SCOPE`, `COST`, `SCHEDULE`, `RISK`, `GOVERNANCE`. |
| cost_impact | number | No | — | Estimated cost impact in project currency (positive = cost increase). |
| schedule_impact_days | integer | No | — | Estimated schedule impact in calendar days (positive = delay). |
| requestor | string | No | — | Person or team requesting the change. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Change request ID, status (PENDING), and confirmation.

**Example prompt:** "Log a SCOPE change request for Project Beta: adding user authentication module. Estimated cost impact £85,000, schedule impact 3 weeks."

---

### `update_change_status`
**Module:** pm-change

Move a change request through the governance lifecycle: PENDING → APPROVED or REJECTED → IMPLEMENTED or WITHDRAWN.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| change_id | string | Yes | — | Change request identifier. |
| status | string | Yes | — | New status. One of: `PENDING`, `APPROVED`, `REJECTED`, `IMPLEMENTED`, `WITHDRAWN`. |
| decision_rationale | string | No | — | Rationale for the approval or rejection decision. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Updated change request record with status history.

**Example prompt:** "Mark change request CHG-017 as APPROVED. Rationale: user authentication is in scope per the original business case requirements."

---

### `get_change_log`
**Module:** pm-change

Retrieve the full change log for a project with optional filters by status and change type.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| status_filter | string | No | `ALL` | Filter by status. One of: `PENDING`, `APPROVED`, `REJECTED`, `IMPLEMENTED`, `WITHDRAWN`, `ALL`. |
| change_type_filter | string | No | — | Filter by change type (e.g. `SCOPE`). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Change log entries sorted by date, with summary statistics (count by status, total cost and schedule impact of approved changes).

**Example prompt:** "Show me all approved changes to Project Alpha and their total impact on cost and schedule."

---

### `get_change_impact_summary`
**Module:** pm-change

Aggregate the total cost and schedule impact of all approved and implemented changes since baseline. Useful for explaining variance between the approved baseline and current position.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Total approved cost impact (£), total approved schedule impact (days), count of changes by type, and a breakdown showing how much of the current cost/schedule variance is attributable to approved changes vs unexplained variance.

**Example prompt:** "How much of Project Beta's £1.2m cost overrun is attributable to approved change requests?"

---

### `analyse_change_pressure`
**Module:** pm-change

Detect scope instability by analysing the volume, rate, and pattern of change requests. High change pressure is a leading indicator of requirements instability and delivery risk.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| window_days | integer | No | `90` | Analysis window in days. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Change request rate (per month), dominant change types, trend (increasing/stable/decreasing), a change pressure score (LOW/MEDIUM/HIGH/CRITICAL), and interpretation linking the pattern to known delivery risks.

**Example prompt:** "Is the volume of change requests on Project Gamma increasing? I'm worried about scope creep before Gate 3."

---

## pm-resource — Resource Capacity Planning

Five tools for resource demand analysis, conflict detection, and portfolio-level capacity planning.

---

### `log_resource_plan`
**Module:** pm-resource

Record the planned resource profile for a project — roles, headcount, and monthly demand.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| resource_data | object | Yes | — | Resource plan data including roles, FTE, and time periods. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Resource plan ID and confirmation.

**Example prompt:** "Log the resource plan for Project Alpha: 2 business analysts, 3 developers, 1 architect from January to June 2026."

---

### `analyse_resource_loading`
**Module:** pm-resource

Analyse resource utilisation across the project schedule. Returns utilisation by role, identifies over-allocated periods, and flags workstreams where resource demand exceeds available supply.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Utilisation by role and period, over-allocation flags, peak demand periods, and a resource health assessment.

**Example prompt:** "Show me the resource loading for Project Beta — are there any over-allocation peaks in the next three months?"

---

### `detect_resource_conflicts`
**Module:** pm-resource

Identify specific instances where the same resource (person or role) is committed to multiple tasks or projects simultaneously beyond their available capacity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** List of conflicts with resource name/role, conflicting tasks or projects, dates, and over-commitment severity. Flags conflicts on the critical path separately as highest priority.

**Example prompt:** "Are there any resource conflicts on Project Alpha that could affect the critical path?"

---

### `get_critical_resources`
**Module:** pm-resource

Identify resources (people or roles) whose absence would critically impact delivery — single points of failure in the resource plan.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** List of critical resources with dependency score, tasks that depend on them, and recommended risk mitigations (succession planning, knowledge transfer, backup identification).

**Example prompt:** "Who are the critical resources on Project Gamma — if any of them left tomorrow, which deliverables would be most at risk?"

---

### `get_portfolio_capacity`
**Module:** pm-resource

Aggregate resource demand across all projects in the portfolio and compare against declared organisational supply. Identifies months where aggregate demand exceeds capacity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_ids | array of strings | Yes | — | List of project identifiers. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Monthly demand/supply comparison by role, over-capacity months, projects contributing most to peak demand, and portfolio capacity health rating.

**Example prompt:** "Do we have enough capacity across the portfolio to support all three projects starting in Q1 2026?"

---

## pm-financial — Financial Management

Five tools for financial baseline setting, actuals tracking, forecasting, and cost performance analysis. All tools use the AssuranceStore via optional `db_path`.

---

### `set_financial_baseline`
**Module:** pm-financial

Set the approved financial baseline for a project. Should be called at Gate 3 (Investment Decision) when the Full Business Case is approved.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| budget_at_completion | number | Yes | — | Total approved budget (BAC) in project currency. |
| baseline_date | string | Yes | — | Date the baseline was approved. Format: `YYYY-MM-DD`. |
| spend_profile | object | No | — | Optional monthly planned spend profile as `{"YYYY-MM": amount}`. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Baseline ID and confirmation.

**Example prompt:** "Set the financial baseline for Project Alpha at £4.2m, approved on 15 March 2025."

---

### `log_financial_actuals`
**Module:** pm-financial

Record actual spend for a specific reporting period.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| period | string | Yes | — | Reporting period. Format: `YYYY-MM`. |
| actual_spend | number | Yes | — | Actual spend in this period. |
| cumulative_spend | number | No | — | Cumulative actual spend to end of period. |
| notes | string | No | — | Notes on spend (e.g. explanation of variance). |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Actuals record ID, period-to-date variance vs planned, cumulative variance vs baseline.

**Example prompt:** "Log March 2025 actuals for Project Beta: £340,000 spent this month, £980,000 cumulative."

---

### `get_cost_performance`
**Module:** pm-financial

Retrieve cost performance analysis comparing actuals against baseline. Returns CPI, cost variance, EAC projection, and trend assessment.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** CPI (Cost Performance Index), cost variance (£ and %), current EAC vs BAC, projected overrun/underspend, trend direction (improving/stable/deteriorating), and interpretation.

**Example prompt:** "What is the cost performance position for Project Alpha? Is the current trajectory sustainable?"

---

### `log_cost_forecast`
**Module:** pm-financial

Record an updated Estimate at Completion (EAC) with rationale. Maintains a forecast history for trend analysis and governance transparency.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| estimate_at_completion | number | Yes | — | Updated total cost forecast (EAC). |
| forecast_date | string | Yes | — | Date of this forecast. Format: `YYYY-MM-DD`. |
| rationale | string | No | — | Explanation of why the EAC has changed from the previous forecast. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Forecast ID, variance from BAC, variance from previous EAC, confirmation.

**Example prompt:** "Update the cost forecast for Project Gamma to £5.1m (up from £4.8m). The increase is due to the approved scope change for user authentication."

---

### `get_spend_profile`
**Module:** pm-financial

Return the planned versus actual spend profile over time, showing where spend is ahead of or behind the baseline plan.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_id | string | Yes | — | Project identifier. |
| db_path | string | No | `~/.pm_data_tools/store.db` | Path to the SQLite store. |

**Returns:** Monthly planned vs actual spend table, cumulative S-curve data (suitable for charting), front-loaded/back-loaded assessment, and narrative on spend profile health.

**Example prompt:** "Show me the spend profile for Project Beta — is it front-loaded or back-loaded compared to the approved plan?"

---

## pm-knowledge — IPA Knowledge Base

Eight tools providing access to pre-loaded authoritative knowledge about UK government project delivery: IPA benchmark statistics, evidence-based failure patterns, guidance references, and analytical tools for reference class forecasting and pre-mortem analysis.

**Data sources:** IPA Annual Reports 2019–2024, NAO reports, HM Treasury guidance, Cabinet Office Controls, Government Functional Standard GovS002.

---

### `list_knowledge_categories`
**Module:** pm-knowledge

List all categories of pre-loaded knowledge available in the knowledge base. Use for discovery before calling other knowledge tools.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| *(none)* | — | — | — | No parameters required. |

**Returns:** Knowledge categories with descriptions, available project types, failure pattern domains, and guidance topics.

**Example prompt:** "What knowledge does the platform have available about government project delivery?"

---

### `get_benchmark_data`
**Module:** pm-knowledge

Retrieve statistical benchmark data for a specific project type and metric, sourced from IPA Annual Reports.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_type | string | Yes | — | Project type cohort. One of: `IT_AND_DIGITAL`, `INFRASTRUCTURE`, `DEFENCE`, `HEALTH_AND_SOCIAL_CARE`, `CROSS_GOVERNMENT`. |
| metric | string | Yes | — | Metric to retrieve. One of: `cost_overrun`, `schedule_slip`, `dca_distribution`, `common_overrun_drivers`, `optimism_bias_reference`, `all`. |

**Returns:** Benchmark statistics (mean, median, P80) with source citation, sample size, and interpretation notes.

**Example prompt:** "What is the typical cost overrun for UK government IT projects?"

---

### `get_failure_patterns`
**Module:** pm-knowledge

Retrieve evidence-based failure patterns identified by IPA and NAO research. Each pattern includes description, early warning indicators, and mitigation strategies.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| domain | string | No | `ALL` | Filter by project domain. One of: `ALL`, `IT_AND_DIGITAL`, `INFRASTRUCTURE`, `DEFENCE`, `HEALTH_AND_SOCIAL_CARE`. |
| gate | string | No | `ANY` | Filter by gate stage relevance. One of: `GATE_0` through `GATE_5`, or `ANY`. |

**Returns:** Matching failure patterns with ID, name, frequency, impact severity, description, indicators, mitigation, and IPA/NAO source reference.

**Example prompt:** "What are the most common failure patterns for IT projects at Gate 3?"

---

### `get_ipa_guidance`
**Module:** pm-knowledge

Retrieve IPA, HM Treasury, or Cabinet Office guidance references on a specific topic with key thresholds and principles.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| topic | string | Yes | — | Guidance topic. One of: `optimism_bias`, `green_book`, `cabinet_office_controls`, `ipa_annual_report`, `gmpp_reporting`, `benefits_management`, `schedule_management`, `project_delivery_functional_standard`, `all`. |

**Returns:** Guidance summary, key thresholds/principles, and source URL.

**Example prompt:** "What does HM Treasury guidance say about optimism bias — what uplift should we apply to our IT cost estimate?"

---

### `search_knowledge_base`
**Module:** pm-knowledge

Full-text search across all knowledge: benchmark data, failure patterns, and guidance references.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | — | Search query — keyword, phrase, or question. |
| category | string | No | `all` | Restrict to a category. One of: `benchmark_data`, `failure_patterns`, `ipa_guidance`, `all`. |

**Returns:** Top 10 ranked results with category, relevance score, and preview. Use when unsure which specific tool to call.

**Example prompt:** "Find everything in the knowledge base about supplier risk and lock-in."

---

### `run_reference_class_check`
**Module:** pm-knowledge

Compare a submitted cost or schedule estimate against the IPA benchmark distribution for comparable completed projects. Returns the approximate percentile, an optimism bias risk flag if below P50, and a recommended P80 provision.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_type | string | Yes | — | Project type cohort for benchmark selection. One of: `IT_AND_DIGITAL`, `INFRASTRUCTURE`, `DEFENCE`, `HEALTH_AND_SOCIAL_CARE`, `CROSS_GOVERNMENT`. |
| estimate_type | string | Yes | — | What is being estimated. One of: `cost_overrun` (as % above baseline), `schedule_slip` (as months). |
| submitted_value | number | Yes | — | The estimate to check. For `cost_overrun`: percentage (e.g. `10` = 10% overrun expected). For `schedule_slip`: months. |

**Returns:** Approximate percentile, optimism bias flag, benchmark distribution (median/P80/mean), recommended minimum and P80 provision, and plain-English interpretation.

**Example prompt:** "Our project team estimates a 5% cost contingency is sufficient for this IT programme. Is that realistic compared to similar government projects?"

---

### `get_benchmark_percentile`
**Module:** pm-knowledge

Position any metric value within the IPA benchmark distribution for comparable projects. Transforms an abstract number into a context-rich, percentile-ranked interpretation.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_type | string | Yes | — | Project type cohort. One of: `IT_AND_DIGITAL`, `INFRASTRUCTURE`, `DEFENCE`, `HEALTH_AND_SOCIAL_CARE`, `CROSS_GOVERNMENT`. |
| metric | string | Yes | — | Metric to benchmark. One of: `cost_overrun`, `schedule_slip`, `dca_green_rate`. |
| value | number | Yes | — | The value to position in the distribution. |

**Returns:** Distribution position description, benchmark statistics, and plain-English interpretation.

**Example prompt:** "Our IT project has a 15% cost overrun so far. Is that above or below average for projects of this type?"

---

### `generate_premortem_questions`
**Module:** pm-knowledge

Generate structured pre-mortem challenge questions for an IPA gate review. Questions are drawn from a library keyed to gate stage and known cognitive failure modes (optimism bias, groupthink, escalation of commitment, bad news suppression).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| gate | string | Yes | — | IPA gate being reviewed. One of: `GATE_0`, `GATE_1`, `GATE_2`, `GATE_3`, `GATE_4`, `GATE_5`, `ANY`. |
| risk_flags | array of strings | No | `[]` | Risk flags for targeted questions. One or more of: `optimism_bias`, `benefits_unowned`, `schedule_no_float`, `supplier_dependency`, `stale_risks`, `sro_capacity`. |
| max_questions | integer | No | `8` | Maximum questions to return. |

**Returns:** Structured question set with source (gate-specific or universal), target area, and failure mode each question addresses. Includes usage guidance for gate review facilitation.

**Example prompt:** "Generate pre-mortem questions for our Gate 3 review. Flag questions about optimism bias and supplier dependency — both are relevant for this project."

---

*Reference generated: 10 April 2026. For tool implementation details see the module source directories. For schema definitions see `docs/data-model-reference.md`.*
