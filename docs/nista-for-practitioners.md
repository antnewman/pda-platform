# NISTA and GMPP Reporting — A Guide for Project Delivery Professionals

This guide explains the NISTA and GMPP reporting capabilities available in the PDA
Platform. No technical background is needed.

---

## What this module does

Every project on the Government Major Projects Portfolio (GMPP) is required to submit
a quarterly return to the Infrastructure and Projects Authority (IPA) via the
government's project data platform, NISTA. These returns are the primary mechanism
through which the Cabinet Office and Treasury monitor the health of major government
projects. Getting them right matters: they inform Delivery Confidence Assessments,
ministerial briefings, and IPA review decisions.

The `pm-nista` module provides a structured toolchain for preparing, validating, and
submitting quarterly GMPP returns. It covers the full lifecycle of a quarterly return:
generating the report from project data, producing AI-assisted narratives for
mandatory text fields, validating the output against NISTA's data requirements before
submission, and submitting directly to the NISTA API. The module also supports fetching
project metadata from the NISTA master registry to confirm that the project's
registration details are correct before a return is filed.

---

## The NISTA Programme and Project Data Standard

NISTA (the National Infrastructure and Service Transformation Authority system) is the
Cabinet Office's authoritative platform for collecting, validating, and publishing data
on government major projects. From 2024-25, the Cabinet Office introduced a twelve-month
trial of a revised data standard — the Programme and Project Data Standard — which
tightened the field definitions and validation rules for quarterly returns. Projects
entering or already listed on the GMPP must comply with this standard.

The standard matters for three reasons. First, it defines exactly which fields are
mandatory, recommended, and optional for each type of return — missing a mandatory field
will cause an automatic rejection of the submission. Second, it specifies acceptable
value ranges, formats, and enumerated options for each field. Third, it requires that
narrative fields (such as the DCA narrative and cost commentary) meet a minimum quality
threshold — which is where AI-assisted narrative generation is most valuable.

The PDA Platform's pm-nista module is aligned to this standard. The validation tool
applies the same field-level rules that the NISTA platform uses, so you can catch
compliance issues before you submit rather than after.

---

## When to use this module

- When preparing a GMPP quarterly return for submission and you want to generate a
  structured, validated report from your project data file.
- When you need to produce or review the narrative sections of a quarterly return (DCA
  narrative, cost commentary, schedule commentary, benefits commentary, risk commentary)
  and want a consistent first draft with a confidence score to guide review effort.
- When checking a draft return for NISTA compliance before submission — either in the
  standard pre-submission check or as part of a PMO quality assurance process.
- When submitting a validated return directly to the NISTA API, whether to the sandbox
  environment for testing or to production for a live return.
- When verifying the project's NISTA registration details — project code, SRO details,
  department, baseline completion date — before filing a return that references them.

---

## Tools

### generate_gmpp_report

Generates a complete GMPP quarterly report from a project data file. This is the
primary entry point for preparing a quarterly return. The tool reads your project
file — which can be in MS Project, GMPP CSV, or other supported formats — and
produces a structured quarterly report covering all mandatory GMPP data fields.

If `generate_narratives` is set to `true` (the default), the tool also calls the
narrative generator to produce AI-assisted text for the DCA, cost, schedule,
benefits, and risk sections. This requires an `ANTHROPIC_API_KEY` environment
variable to be set. If AI narratives are not needed — for instance, if you are
producing the report structure only and will write the narratives separately — set
`generate_narratives` to `false`.

**Key parameters:**
- `project_file` — path to your project data file.
- `quarter` — the reporting quarter: `Q1`, `Q2`, `Q3`, or `Q4`.
- `financial_year` — in the format `2025-26`.
- `generate_narratives` — whether to generate AI narratives (default: `true`).

**When to use it:** As the first step of preparing a quarterly return. Run this tool
to convert your project data into the structured GMPP format, then use
`validate_gmpp_report` to check it before submission.

**Worked example.**

*Scenario.* You are the PMO lead for Project ASCEND, a major digital transformation
programme at HMRC. The Q3 2025-26 return is due in three weeks. Your project data is
held in a GMPP CSV file that is updated monthly. You want to generate the quarterly
report with narratives.

*What to do.* Ask Claude: "Generate the GMPP quarterly report for Project ASCEND using
the file at `/data/ascend-gmpp-q3.csv`. This is for Q3 2025-26. Please include
AI-generated narratives."

*What Claude does.* Calls `generate_gmpp_report` with the file path, quarter `Q3`,
financial year `2025-26`, and `generate_narratives` set to `true`. The tool parses the
project data, aggregates the GMPP data fields, generates five narrative sections, and
returns the full report with a summary block.

*How to interpret the output.* The summary block shows the DCA rating, the confidence
score for the DCA narrative, any missing fields, and any validation warnings. A
`dca_narrative_confidence` above 0.75 means the narratives are suitable for review
without extensive rewriting; below 0.60, treat them as a structural starting point and
rewrite substantially before submission. The `missing_fields` list tells you which data
fields the parser could not populate from your source file — these will need to be added
manually before validation and submission.

---

### generate_narrative

Generates a single AI-powered narrative section with a confidence score, without
producing the full report. Use this when you need to (re-)generate a specific narrative
section — for instance, if the DCA rating has changed since the initial report
generation, or if you want to test different project context inputs before committing to
a full report run.

The tool supports five narrative types: `dca`, `cost`, `schedule`, `benefits`, and
`risk`. Each narrative is generated using multi-sample AI consensus — the model is
called multiple times and the outputs are compared to produce a confidence score. The
`review_level` field in the output indicates whether human review of the narrative is
routine, recommended, or required.

**Key parameters:**
- `narrative_type` — one of `dca`, `cost`, `schedule`, `benefits`, `risk`.
- `project_context` — a JSON object containing the project data relevant to that
  narrative type. `project_name` is always required; additional fields (such as
  `dca_rating`, `baseline_cost`, `forecast_cost`, `cost_variance_percent`) are used
  when available to produce a more specific narrative.

**When to use it:** When regenerating a single narrative after a data change, when
reviewing whether a narrative meets submission quality standards, or when testing the
confidence score for a specific set of project context data before submitting.

**Worked example.**

*Scenario.* Project ASCEND's DCA rating has moved from AMBER to AMBER/RED since the
initial report generation. The DCA narrative needs to be updated to reflect this change
and must explain the reasons for the deterioration.

*What to do.* Ask Claude: "Regenerate the DCA narrative for Project ASCEND. The DCA
rating is now AMBER/RED. The project has slipped two months on the critical path and
the spend to date is £12m against a baseline of £9.5m at this stage. The department
is HMRC."

*What Claude does.* Calls `generate_narrative` with `narrative_type` set to `dca` and
a `project_context` object containing the project name, DCA rating, department, and
the contextual information provided. The tool generates the narrative with multi-sample
consensus and returns the text, confidence score, review level, and the number of
samples used.

*How to interpret the output.* If the confidence score is 0.72 and the review level is
`RECOMMENDED`, the narrative is usable but the model is not highly consistent across
samples — likely because an AMBER/RED rating with specific cost and schedule context
produces more variable outputs. Review the narrative carefully against the IPA's DCA
guidance and the specific reasons for the rating change before including it in the
return.

---

### validate_gmpp_report

Validates a quarterly report file against the NISTA data standard before submission.
The tool checks mandatory field completeness, field format and value range compliance,
and consistency between related fields. It returns a compliance score (0–100%) and a
categorised list of errors and warnings.

Three strictness levels are available:
- `LENIENT` — checks mandatory fields only; suitable for early-stage validation during
  report preparation.
- `STANDARD` — checks mandatory and recommended fields, plus format and range
  compliance. This is the appropriate level for pre-submission checking.
- `STRICT` — applies all NISTA rules including optional field guidance. Use this if
  your organisation's PMO standard requires fully complete returns.

**Key parameters:**
- `report_file` — path to the quarterly report JSON file.
- `strictness` — `LENIENT`, `STANDARD`, or `STRICT` (default: `STANDARD`).

**When to use it:** Before every submission. Run `validate_gmpp_report` at `STANDARD`
strictness as the final check before calling `submit_to_nista`. A compliance score
below 80% or any errors (as distinct from warnings) should be resolved before
submission.

**Worked example.**

*Scenario.* The ASCEND quarterly report has been generated and narratives have been
reviewed. Before submitting to NISTA production, the PMO wants to confirm the return
is fully compliant.

*What to do.* Ask Claude: "Validate the GMPP report at `/data/ascend-gmpp-q3-final.json`
at STANDARD strictness."

*What Claude does.* Calls `validate_gmpp_report` with the file path and `STANDARD`
strictness. The validator checks each field against the NISTA schema and returns a
compliance score with categorised findings.

*How to interpret the output.* Suppose the tool returns a compliance score of 94% with
two warnings and zero errors. The warnings flag two recommended fields — `project_phase`
and `procurement_route` — that are missing. These do not prevent submission under
`STANDARD` rules but are expected for complete returns. You can either populate them
from your project data and re-validate, or proceed to submission noting that these
fields will appear as gaps in the NISTA data quality report.

---

### submit_to_nista

Submits a validated quarterly return to the NISTA API. Supports both the `sandbox`
environment — for testing the submission pipeline without creating a live record — and
`production` for live returns.

This tool requires NISTA API credentials to be configured as environment variables:
`NISTA_CLIENT_ID` and `NISTA_CLIENT_SECRET`. If your organisation uses mutual TLS
authentication, `NISTA_CERT_PATH` and `NISTA_KEY_PATH` are also required. Contact your
Cabinet Office NISTA liaison to obtain credentials if you do not have them.

**Key parameters:**
- `report_file` — path to the quarterly report JSON file.
- `project_id` — the project identifier (your internal identifier or the NISTA project
  code).
- `environment` — `sandbox` or `production` (default: `sandbox`).

**When to use it:** After `validate_gmpp_report` has confirmed the return is compliant.
Always submit to `sandbox` first to confirm the submission pipeline is working correctly
before submitting to `production`.

**Worked example.**

*Scenario.* The ASCEND Q3 return has been validated and is ready for submission.

*What to do.* Ask Claude: "Submit the ASCEND quarterly return at
`/data/ascend-gmpp-q3-final.json` to NISTA production. The project ID is ASCEND-001."

*What Claude does.* Calls `submit_to_nista` with the file path, project ID, and
`environment` set to `production`. The tool loads the report, authenticates with the
NISTA API, and submits the return. It returns the submission ID, timestamp, and any
validation warnings issued by the NISTA platform.

*How to interpret the output.* A successful submission returns a submission ID and
timestamp. Record the submission ID — it is your proof of submission and is required
if you need to query or correct the return. Validation warnings from the NISTA platform
(as distinct from the local `validate_gmpp_report` checks) are advisory and do not
prevent acceptance of the return, but should be logged for the audit trail.

---

### fetch_nista_metadata

Fetches the project's registration details from the NISTA master registry. Returns the
official NISTA project code, project name, department, category, SRO details, and
baseline dates as held in the NISTA system.

**Key parameters:**
- `project_id` — the NISTA project code or your internal project identifier.
- `environment` — `sandbox` or `production` (default: `sandbox`).

**When to use it:** At the start of a new reporting cycle or when there has been a
change to the project's registered details (new SRO, revised baseline dates, department
restructure). Also useful for confirming the correct NISTA project code before
submission, particularly when the internal project identifier and the NISTA code differ.

**Worked example.**

*Scenario.* A new PMO lead has joined Project ASCEND and wants to confirm the project's
registration details in NISTA — specifically the SRO name and the baseline completion
date — before preparing the next quarterly return.

*What to do.* Ask Claude: "Fetch the NISTA registration details for project ASCEND-001
from the production environment."

*What Claude does.* Calls `fetch_nista_metadata` with `project_id` set to `ASCEND-001`
and `environment` set to `production`. The tool authenticates with the NISTA API and
retrieves the project's master record.

*How to interpret the output.* The output confirms the project's official NISTA project
code, the name as registered (which must match exactly in quarterly returns), the
current SRO and their email, and the baseline completion date. If any of these details
have changed — for instance, the SRO has changed and has not yet been updated in NISTA
— you should contact the Cabinet Office GMPP team to update the master record before
submitting the next return, as discrepancies can flag for manual review.

---

## Common workflows

### Workflow 1: Preparing a quarterly GMPP return

1. At the start of the quarter, run `fetch_nista_metadata` to confirm the project's
   registration details are current — particularly the SRO and baseline dates.
2. Export your latest project data to a GMPP-compatible file format.
3. Run `generate_gmpp_report` with `generate_narratives` set to `true` to produce
   the initial report with AI-assisted narratives.
4. Review all five narrative sections. For any narrative with a confidence score below
   0.70 or a `review_level` of `REQUIRED`, rewrite the section in full using the
   AI-generated text as a structural guide only.
5. For any fields listed in `missing_fields`, populate them manually in the report JSON.
6. Run `validate_gmpp_report` at `STANDARD` strictness. Address any errors; review and
   decide whether to populate fields flagged as warnings.
7. Once the compliance score is 90% or above with zero errors, submit to the `sandbox`
   environment using `submit_to_nista` to confirm the pipeline works.
8. Submit to `production` and record the submission ID.

### Workflow 2: Checking NISTA compliance before submission

This workflow is for PMOs that receive a completed report from the delivery team and
need to quality-assure it before submission.

1. Run `validate_gmpp_report` at `STRICT` strictness to get the most complete picture
   of any gaps.
2. Review the missing recommended and optional fields against the Cabinet Office's
   current data quality expectations — some departments have internal standards above
   the NISTA minimum.
3. For narrative fields, check each section against the DCA rating: the narrative must
   explain the current rating and, where the rating is AMBER or below, must describe
   the specific issues driving it. AI-generated narratives that do not reference the
   specific project situation should be treated as requiring revision.
4. Once compliant at `STANDARD` strictness with zero errors, proceed to submission.

### Workflow 3: Tracking compliance trend over time

NISTA publishes data quality reports that show a project's compliance scores across
reporting periods. The following approach uses the PDA Platform to anticipate those
scores before they are published.

1. After each quarterly submission, save the validation output (compliance score,
   error count, warning count) to your project's return log.
2. Compare the current quarter's compliance score with the previous two quarters. A
   declining trend — even if all individual scores remain above the submission
   threshold — is an early warning that data quality discipline is weakening.
3. For projects that have received a low data quality flag from the Cabinet Office,
   run `validate_gmpp_report` at `STRICT` strictness for the next three returns until
   the flag is cleared.
4. If the `missing_fields` list is growing quarter-on-quarter, this indicates a problem
   with the source data — either the project data file is not being kept current, or
   the data governance process needs strengthening. Address the source before the next
   return.

---

## Limitations and considerations

- The `generate_gmpp_report` tool can only populate fields that are present in your
  source project data file. If your project file does not contain cost actuals, for
  instance, those fields will appear in `missing_fields` and must be added manually.
  The quality of the generated report is directly dependent on the quality of your
  source data.
- AI-generated narratives are first drafts. They are calibrated against the IPA's GMPP
  narrative guidance and the data provided in `project_context`, but they cannot
  substitute for the project team's knowledge of the specific circumstances that explain
  the current DCA rating, cost position, or schedule status. Every narrative must be
  reviewed by a person with detailed knowledge of the project before submission.
- The `validate_gmpp_report` tool applies the NISTA data standard rules as implemented
  in the `pm-data-tools` package. The NISTA platform may apply additional validation
  rules not yet reflected in the local schema. A `STANDARD` compliance score of 100%
  does not guarantee that the NISTA platform will accept the return without warnings.
- NISTA API credentials are required for `submit_to_nista` and `fetch_nista_metadata`.
  These credentials are environment-specific — sandbox credentials do not work in
  production. Contact the Cabinet Office GMPP team to obtain credentials.
- The `sandbox` environment does not reflect live NISTA data. Metadata fetched from
  sandbox and submission IDs generated in sandbox are not visible to the Cabinet Office
  and should not be used as evidence of submission.
- The twelve-month trial of the revised data standard may result in schema changes
  during the trial period. If you encounter unexpected validation errors, check whether
  the NISTA data standard has been updated since the last `pm-data-tools` release.

---

## Related modules

- **pm-validate** — For structural and semantic validation of project data before it
  reaches the GMPP reporting stage. Use `pm-validate` tools to clean and validate your
  source data file before passing it to `generate_gmpp_report`.
- **pm-data** — For loading and querying project data programmatically. The data
  structures produced by `pm-data` tools are compatible with the GMPP aggregator used
  by `generate_gmpp_report`.
- **pm-assure** — For the broader assurance context. The DCA rating and the narrative
  used in a quarterly return should be consistent with the assurance posture recorded
  in the `pm-assure` module's review action and recommendation store.
- **pm-brm** — Benefits narratives in the quarterly return should align with the
  benefits health and realisation data held in the `pm-brm` benefits register. Use
  `get_benefits_health` to verify the benefits picture before generating the benefits
  narrative section.
