# IPA Knowledge Base — A Guide for Practitioners

This guide explains the knowledge base capabilities available in the PDA
Platform. No technical background is needed. The module is designed for
assurance professionals, gate reviewers, SROs, and PMO leads who want to
ground their assessments in authoritative evidence rather than instinct and
experience alone.

---

## What this module does

One of the most persistent weaknesses in UK government project assurance is the
absence of an evidence base. Gate reviewers challenge estimates and plans based
on professional experience, but that experience is not always systematic or
explicit. Optimism bias — the well-documented tendency for project teams to
underestimate cost, schedule, and risk — persists in part because the
historical data needed to challenge optimistic estimates is not readily
accessible in the room.

The pm-knowledge module addresses this. It pre-loads authoritative data
drawn from IPA Annual Reports covering 2019 to 2024, NAO performance
assessments, HM Treasury Green Book guidance, and Cabinet Office controls
frameworks. This data is available as structured benchmarks, failure patterns,
and guidance references — accessible in seconds during a review rather than
requiring a separate research exercise.

The module also provides two analytical tools that are particularly powerful
for gate reviews: `run_reference_class_check` compares a submitted cost or
schedule estimate against the historical distribution for comparable projects,
flagging optimism bias where the estimate sits below the median of what
comparable projects actually experienced; and `generate_premortem_questions`
produces structured challenge questions for a gate review, derived from known
failure modes and targeted to the specific gate being reviewed.

Together, these tools allow practitioners to turn gut-feel assurance into
evidence-grounded assurance.

---

## When to use it

- At any gate review where you want to challenge a cost or schedule estimate
  against what comparable government projects have actually experienced.
- When preparing pre-mortem questions for a Gate 0 through Gate 5 review.
- When an observed indicator on a project — for example, a stale risk register,
  an SRO with multiple concurrent responsibilities, or a single-supplier
  delivery model — triggers a question about whether this matches a known
  failure pattern.
- When producing an assurance recommendation and needing a citation to
  authoritative IPA, Green Book, or Cabinet Office guidance rather than an
  unsupported assertion.
- When onboarding assurance reviewers who are less familiar with IPA
  methodology and need quick access to the evidential basis for common
  assurance challenges.

---

## The benchmark data

The benchmark data covers five project type categories, each with statistics
sourced from IPA Annual Reports 2019 to 2024:

| Project Type | Cost overrun (mean / median / P80) | Schedule slip | DCA distribution |
|---|---|---|---|
| IT_AND_DIGITAL | Mean 27%, Median 18%, P80 55% | Significant | Available |
| INFRASTRUCTURE | Mean 22%, Median 14%, P80 45% | Significant | Available |
| DEFENCE | Mean 35%, Median 25%, P80 70% | Significant | Available |
| HEALTH_AND_SOCIAL_CARE | Mean 20%, Median 13%, P80 42% | Moderate | Available |
| CROSS_GOVERNMENT | Composite across all types | All types | Optimism bias uplifts |

The P80 figure is particularly useful for assurance: it tells you the cost
overrun level that 80% of comparable completed projects stayed below. If a
project is estimating zero contingency against a project type where the P80
overrun is 55%, that is a material finding.

The DCA distribution data shows the typical spread of Delivery Confidence
Assessment ratings across the GMPP portfolio — providing a reference point
for whether a project's current DCA is typical or exceptional for its stage
and type.

---

## The failure patterns

The module contains eight evidence-based failure patterns identified by IPA
and NAO research:

| Pattern | Core description |
|---|---|
| Optimism bias | Systematic underestimation of cost, schedule, and risk in business cases |
| SRO capacity | SRO stretched across multiple major programmes, reducing strategic oversight |
| Requirements too late | Requirements not stabilised before delivery commitments are made |
| Benefits unowned | No named Benefits Owner responsible for realisation post-go-live |
| Stale risk register | Risk register not updated in the past 90 days — risks not being actively managed |
| Schedule float consumed | Critical path float used up early, leaving no buffer for late-stage delivery |
| Single supplier | Sole-source or dominant supplier with no viable alternative at key delivery stages |
| Governance complexity | Multiple overlapping governance forums creating confusion about decision authority |

Each pattern includes: a description of what the failure mode looks like in
practice; early warning indicators that practitioners can look for; mitigation
strategies that have been effective; and the IPA or NAO source reports that
document the pattern.

---

## Tools

### list_knowledge_categories

**What it does.** Returns the full index of what is available in the knowledge
base: benchmark data categories, failure pattern domains and gate stages, and
guidance topics. Use this first when you are not sure what is available.

**Key parameters.** None required.

**When to use it.** Use at the start of a knowledge base session to orient
yourself. Particularly useful when onboarding a new assurance reviewer who
needs to understand the scope of what the platform knows.

---

### get_benchmark_data

**What it does.** Returns statistical benchmark data for a specified project
type and metric. The output includes mean, median, and P80 values for cost
overrun or schedule slip; the DCA distribution across the GMPP portfolio for
that project type; common overrun drivers; or the HM Treasury Green Book
optimism bias uplifts.

**Key parameters.**
- `project_type` (required): one of IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE,
  HEALTH_AND_SOCIAL_CARE, or CROSS_GOVERNMENT.
- `metric` (required): one of `cost_overrun`, `schedule_slip`,
  `dca_distribution`, `common_overrun_drivers`, `optimism_bias_reference`,
  or `all` for the complete benchmark profile.

**When to use it.** Use when you need to contextualise a project's cost or
schedule position against the broader GMPP evidence base. Use with
`optimism_bias_reference` when challenging whether a business case has applied
the correct Green Book optimism bias uplift.

---

### get_failure_patterns

**What it does.** Returns failure patterns with indicators and mitigations,
filtered by project domain and gate stage.

**Key parameters.**
- `domain` (optional): filter to a specific domain, or ALL for patterns
  applicable across all project types.
- `gate` (optional): filter to patterns most relevant at a specific gate stage.
  Use GATE_0 for business case challenge, GATE_1 for initial delivery readiness,
  GATE_2 for procurement, GATE_3 for delivery, GATE_4 for readiness to service,
  GATE_5 for benefits realisation.

**When to use it.** Use when an observed project indicator — for example,
benefits not yet assigned to a named owner — triggers a question about whether
this matches a pattern of failure documented in IPA research. The mitigation
strategies provide a starting point for recommendations.

---

### get_ipa_guidance

**What it does.** Returns a summary of IPA, HM Treasury, or Cabinet Office
guidance on a specified topic, including key principles, thresholds, and the
source URL for citation.

**Key parameters.**
- `topic` (required): one of `optimism_bias`, `green_book`,
  `cabinet_office_controls`, `ipa_annual_report`, `gmpp_reporting`,
  `benefits_management`, `schedule_management`,
  `project_delivery_functional_standard`, or `all`.

**When to use it.** Use when making a recommendation that needs to cite
authoritative guidance rather than assurance team opinion. Particularly useful
when an SRO pushes back on an assurance finding — having the Green Book or
Cabinet Office controls guidance to hand strengthens the case significantly.

---

### search_knowledge_base

**What it does.** Full-text search across all knowledge in the platform:
benchmark data, failure patterns, and IPA guidance. Returns ranked results
with the most relevant entries first.

**Key parameters.**
- `query` (required): a keyword, phrase, or question in plain English. For
  example: "supplier dependency", "benefits owner", "schedule float", or
  "what does IPA say about optimism bias in IT projects".
- `category` (optional): restrict the search to `benchmark_data`,
  `failure_patterns`, `ipa_guidance`, or `all`.

**When to use it.** Use when you are not sure which specific tool to call, or
when you want to find everything in the knowledge base relevant to a specific
topic. This is the right starting point when approaching an unfamiliar issue
or when you want to make sure you have not missed a relevant benchmark or
guidance reference.

---

### run_reference_class_check

**What it does.** Compares a submitted cost or schedule estimate against the
IPA benchmark distribution for comparable completed government projects. Returns
the approximate percentile at which the estimate sits, flags optimism bias if
the estimate is below the P50 (median) of comparable projects, and provides
a recommended adjusted value.

**Key parameters.**
- `project_type` (required): IT_AND_DIGITAL, INFRASTRUCTURE, DEFENCE,
  HEALTH_AND_SOCIAL_CARE, or CROSS_GOVERNMENT.
- `estimate_type` (required): `cost_overrun` (the expected overrun above the
  approved baseline, expressed as a percentage) or `schedule_slip` (expected
  slippage beyond the planned completion date, in months).
- `submitted_value` (required): the estimate being checked. For cost_overrun,
  enter the percentage (e.g. 10 for a 10% contingency allowance). For
  schedule_slip, enter the number of months of contingency in the plan.

**When to use it.** Use at any business case review or gate review where a
cost estimate or schedule plan is being challenged. This is the most powerful
tool in the knowledge base for counteracting optimism bias: it replaces
"I think this estimate looks low" with "this estimate sits at the 23rd
percentile of what comparable IT and digital projects have actually
experienced." That is a materially stronger position.

If the submitted estimate is below P50, the tool flags this as potential
optimism bias and provides the P50 and P80 values as reference points for a
revised estimate.

---

### get_benchmark_percentile

**What it does.** Takes a current performance metric value and positions it
in the IPA benchmark distribution for comparable projects. Transforms an
abstract number into a context-rich interpretation.

**Key parameters.**
- `project_type` (required).
- `metric` (required): one of `cost_overrun` (%), `schedule_slip` (months),
  or `dca_green_rate` (%).
- `value` (required): the current metric value.

**When to use it.** Use when you have a metric value — from EV analysis, from
the project's own cost report, or from a gate readiness assessment — and you
want to understand whether it is typical or exceptional for this type of
project. For example: "Our IT project currently has a 22% cost overrun — is
that normal?" This tool answers that question by positioning the 22% in the
distribution of outcomes from comparable completed projects.

---

### generate_premortem_questions

**What it does.** Generates a set of structured pre-mortem challenge questions
for a gate review. Pre-mortem analysis involves imagining that the project has
failed and asking what caused it — an evidence-based technique for counteracting
optimism bias and groupthink in governance forums. Returns five to ten targeted
questions drawn from a library keyed to gate stage and known risk patterns.

**Key parameters.**
- `gate` (required): GATE_0 through GATE_5, or ANY for gate-agnostic
  questions.
- `risk_flags` (optional): a list of specific risk flags to add targeted
  questions for. Options are: `optimism_bias`, `benefits_unowned`,
  `schedule_no_float`, `supplier_dependency`, `stale_risks`, `sro_capacity`.
  Use these when the project already shows indicators of a specific failure
  pattern.
- `max_questions` (optional, default 8): the maximum number of questions to
  return.

**When to use it.** Use in preparation for any gate review, as part of
building the review pack. The questions are not intended to be presented to
the project team in advance — they are the challenge questions that the
gate review panel should be asking. They turn what can become a status
confirmation exercise into a genuine stress test of the project's resilience.

If the project has already been assessed using pm-assure and pm-risk, use the
findings from those assessments to select the appropriate risk flags — this
ensures the pre-mortem questions are targeted at the actual vulnerabilities
identified in the data, not at a generic checklist.

---

## Common workflows

### Workflow 1: Reference class check at a gate review

1. Before the review, identify the project type and the cost or schedule
   contingency in the plan.
2. Run `run_reference_class_check` with the project type, estimate type, and
   submitted value.
3. Note the percentile result and whether the tool flags optimism bias.
4. Run `get_benchmark_data` with `metric: optimism_bias_reference` for the
   CROSS_GOVERNMENT type to retrieve the Green Book uplift guidance applicable
   to this project category.
5. Use both outputs to frame a challenge at the gate review: present the
   percentile finding and the recommended adjusted value as the evidence-based
   starting point for the discussion.

### Workflow 2: Building a pre-mortem for a gate review

1. Run any outstanding pm-assure and pm-risk assessments to identify the
   project's current risk indicators.
2. Map the identified risks to the available risk flags: `optimism_bias`,
   `benefits_unowned`, `schedule_no_float`, `supplier_dependency`,
   `stale_risks`, `sro_capacity`.
3. Run `generate_premortem_questions` with the appropriate gate and the
   identified risk flags.
4. Review the generated questions. Remove any that are not relevant to this
   specific project. Add project-specific questions where needed.
5. Use the final list as the review panel's challenge framework.

### Workflow 3: Investigating a supplier dependency issue

1. Run `search_knowledge_base` with the query "supplier dependency".
2. Review the results, which will include the relevant failure pattern
   (single supplier), any applicable benchmark data, and guidance references.
3. Run `get_failure_patterns` filtered to the project's domain and the
   relevant gate to get the full indicators and mitigations for the
   supplier dependency pattern.
4. Run `get_ipa_guidance` with `topic: cabinet_office_controls` to retrieve
   the relevant controls framework guidance on supplier management.
5. Combine the failure pattern indicators, the mitigation strategies, and the
   guidance citation into a structured assurance finding.

---

## Worked examples

### Example 1: Using run_reference_class_check at Gate 1 to challenge a cost estimate

**Scenario.** You are an independent assurance reviewer at an IPA Gate 1
review for a large digital transformation programme. The project team has
presented an updated cost estimate with a 12% contingency allowance above the
approved baseline. The business case was approved on the basis of this
contingency level. You want to assess whether this is realistic.

**What to do.** Ask Claude to run `run_reference_class_check` with
`project_type: IT_AND_DIGITAL`, `estimate_type: cost_overrun`, and
`submitted_value: 12`.

**What Claude does.** It compares the 12% contingency against the IPA
benchmark distribution for completed IT and digital government projects.
The result shows this estimate sits at approximately the 32nd percentile —
meaning 68% of comparable completed projects experienced a cost overrun
greater than 12%. The P50 is approximately 18% and the P80 is approximately
55%. The tool flags this as a potential optimism bias finding.

**How to interpret the output.** The 12% contingency is not a safe assumption:
the majority of comparable projects exceeded it. The recommended adjusted
value at P50 is 18%. As the assurance reviewer, you can now make a specific,
evidenced finding: "The submitted contingency of 12% sits at the 32nd
percentile of outcomes for comparable IT and digital projects. A contingency
of at least 18% (P50) would be required for this estimate to be consistent
with the median performance of comparable projects. We recommend the project
team revisit this assumption before the business case proceeds to Gate 2."
This is substantially stronger than "the contingency looks low."

---

### Example 2: Generating pre-mortem questions before a Gate 3 review

**Scenario.** You are preparing a Gate 3 review pack for a large infrastructure
project. Prior assessment has identified that: the risk register has not been
updated in four months; the main contractor is a sole-source supplier with no
ready alternative; and schedule float on the critical path has dropped to zero.
You want to make sure the review panel is asking the right challenge questions.

**What to do.** Ask Claude to run `generate_premortem_questions` with
`gate: GATE_3` and `risk_flags: ["stale_risks", "supplier_dependency",
"schedule_no_float"]`.

**What Claude does.** It draws from the question library for Gate 3 delivery
reviews and adds targeted questions for the three specified risk flags. The
output includes questions such as: "If the project fails to complete on time,
what is the single most likely cause — and what evidence do you have that this
risk has been actively managed in the past 90 days?" and "If the main
contractor were to experience a performance failure at this stage, what
contingency exists and how quickly could it be activated?"

**How to interpret the output.** These questions are not status checks — they
are structured stress tests designed to surface whether the project team has
genuinely engaged with these failure modes or whether they have been noted
and set aside. Use them as the review panel's primary challenge agenda.
A project team that cannot answer them clearly and specifically has a risk
management gap.

---

### Example 3: Using search_knowledge_base to find everything relevant to a supplier dependency issue

**Scenario.** You are a PMO lead who has identified that a programme contains
three projects all dependent on a single shared technology supplier. One of
those projects is approaching a gate review and you want to understand the
full evidential picture — what IPA says about single-supplier risk, what the
failure indicators look like, and what mitigations are typically effective.

**What to do.** Ask Claude to run `search_knowledge_base` with the query
"single supplier dependency" and `category: all`.

**What Claude does.** It searches across benchmark data, failure patterns, and
guidance references simultaneously and returns the most relevant entries. The
results include the single supplier failure pattern with full indicators and
mitigations; any benchmark data on supplier-related overrun drivers for the
relevant project type; and the Cabinet Office controls guidance on supplier
management and commercial risk.

**How to interpret the output.** Start with the failure pattern. The indicators
tell you what to look for in the project data: has the team formally assessed
the contractual consequences of supplier failure? Is there a documented
contingency plan? Has a market assessment been completed to verify that an
alternative supplier could be brought in if required? The mitigations give you
the recommended actions. The guidance citation provides the authoritative
basis for raising this as a formal assurance finding rather than an informal
concern.

---

## Limitations and considerations

- The benchmark data is sourced from IPA Annual Reports 2019 to 2024 and is
  the most comprehensive publicly available dataset for UK government projects
  of this type. However, it reflects the population of GMPP projects and may
  not precisely match niche project types. Use the benchmark data to inform
  assurance judgements, not to override them.
- The reference class check uses the submitted value as a percentage above
  baseline (for cost) or months of slippage (for schedule). It cannot account
  for project-specific factors that may make a higher or lower contingency
  appropriate — for example, a genuinely novel technology with higher inherent
  uncertainty, or a project with an unusually strong delivery track record.
  The benchmark is a starting point for the challenge, not a mechanical rule.
- The pre-mortem questions are drawn from a structured library. They are
  designed to be good, targeted challenge questions — but they are not a
  substitute for a review panel that reads the project documentation and
  brings professional judgement to the session.
- Guidance references include the source URL for each document. These URLs
  reflect the most recent published versions as of the data loading date.
  Always verify you are citing the current version of Green Book or Cabinet
  Office controls guidance.

---

## Related modules

- **pm-assure**: use alongside pm-knowledge to ground assurance findings in
  both project-specific data (from pm-assure) and historical evidence (from
  pm-knowledge).
- **pm-risk**: use the risk register data to identify specific risk flags for
  `generate_premortem_questions`.
- **pm-brm**: cross-reference the benefits_unowned failure pattern against
  pm-brm data to determine whether the project actually has named Benefits
  Owners assigned.
- **pm-ev**: use EV metrics (CPI, SPI) as inputs to `get_benchmark_percentile`
  to contextualise the project's cost and schedule performance against the
  GMPP evidence base.
- **pm-gate-readiness**: gate readiness assessment findings provide the
  starting point for identifying which risk flags to pass to
  `generate_premortem_questions`.
