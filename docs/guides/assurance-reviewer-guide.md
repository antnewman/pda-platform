# Independent Assurance Reviewer Guide — PDA Platform

## Who this guide is for

You are conducting an IPA Gate Review, a Departmental Assurance Review, a Project Assessment Review, or another independent challenge of a UK government major project. Your job is to test the programme narrative, identify gaps and overoptimism, and produce a credible Delivery Confidence Assessment (DCA) with conditions and recommendations. You are not a supporter of the programme — you are an independent evaluator of whether it is genuinely on track.

This guide shows you how to use the PDA Platform to build an independent, data-driven assessment before and during a review. Claude calls the tools on your behalf and synthesises the results using IPA conventions and language.

---

## Setting up Claude for your role

You need two prompts in place before starting a gate review analysis.

**Step 1 — Set the assurance reviewer system prompt.** Paste the Independent Assurance Reviewer prompt from `docs/prompts/role-system-prompts.md` into Claude's **System Prompt** field. This configures Claude to apply professional scepticism, use the DCA rating scale correctly, assess against all eight IPA dimensions, and flag overoptimism in programme narratives.

**Step 2 — Run the Full Gate Readiness Analysis research prompt.** For a comprehensive pre-review assessment, use Research Prompt 1 from `docs/prompts/research-prompts.md` as your user message. Substitute the project ID and run it. Claude will work through all 13 steps and produce a complete IPA-format gate review report.

This combination — assurance reviewer system prompt plus the gate readiness research prompt — is the most powerful configuration for pre-review preparation.

---

## What the platform can do for you

- Run an independent 13-step gate readiness analysis aligned to IPA conventions, producing a draft DCA with dimension-level ratings and evidence citations
- Detect confidence divergence: dimensions where the programme's stated confidence materially exceeds what the objective data supports
- Identify evidence gaps: missing artefacts, stale documents, and dimensions where the evidence is insufficient to support a rating
- Flag assumption drift: cost, schedule, or benefits assumptions that have moved from their approved basis without being converted to risks
- Quantify risk velocity: which risks are accelerating, and whether the programme team has acknowledged and mitigated them
- Apply reference class context: where does this programme's cost or schedule position sit relative to comparable historical projects?
- Generate pre-mortem challenge questions calibrated to the gate and project type
- Surface failure patterns from comparable programmes, giving you the specific probe areas most likely to reveal real problems

---

## Your most useful tools

| Tool | What it does for you | When most useful |
|---|---|---|
| `assess_gate_readiness` | Scores readiness against the target gate across all eight dimensions | Core of any pre-review assessment |
| `check_confidence_divergence` | Identifies where stated confidence exceeds evidence | Testing programme narrative, flagging overoptimism |
| `check_artefact_currency` | Flags missing or stale mandatory artefacts | Evidence gap detection, review preparation |
| `get_armm_report` | Returns ARMM maturity level (0–4) with blocking topics | Governance and assurance dimension assessment |
| `run_assurance_workflow` | Full workflow classification — HEALTHY to CRITICAL | Independent health check, narrative challenge |
| `get_assumption_drift` | Tracks which assumptions have moved from their approved basis | Financial regularity, optimism bias detection |
| `get_risk_velocity` | Identifies rapidly accelerating risks | Risk management dimension, overoptimism testing |
| `detect_stale_risks` | Flags risks not reviewed within the expected cycle | Risk register quality, governance finding |
| `run_reference_class_check` | Places cost/schedule position in historical comparable project context | Estimate credibility, optimism bias evidence |
| `generate_premortem_questions` | Generates targeted challenge questions for the gate and project type | Panel preparation, SRO challenge session |
| `get_failure_patterns` | Returns failure mode indicators for comparable project types | Identifying where to probe hardest |
| `search_knowledge_base` | Searches for project-type-specific precedents and failure modes | Domain-specific challenge preparation |
| `get_gate_readiness_history` | Shows readiness trend over the last three assessments | Deterioration detection, trajectory assessment |
| `compare_gate_readiness` | Compares current readiness to previous assessment | Progress testing, identifying declining dimensions |

---

## Your most useful research prompts

| Prompt | Purpose | When to use |
|---|---|---|
| Full Gate Readiness Analysis (Research Prompt 1, 13 steps) | Complete IPA-format pre-review assessment covering all eight dimensions, with conditions and recommendations | Pre-review preparation, 24–48 hours before the review |

This is the primary tool for review preparation. Set the assurance reviewer system prompt, then paste Research Prompt 1 as your user message. Claude will call 12 tools in sequence and produce a formatted gate review report that you can use as your independent baseline going into the review.

---

## Worked examples

### Example 1: Pre-review independent assessment

**Scenario**

You are reviewing Project Gamma at Gate 3 tomorrow. You have access to the platform and want an independent, data-driven pre-review assessment before you see the programme team. You want to know where the real risks are, what the evidence gaps look like, and where you should probe hardest in the review.

**What to ask Claude**

> I am reviewing Project Gamma at Gate 3 tomorrow. Run the full 13-step gate readiness analysis and give me a complete independent pre-review assessment — DCA rating, conditions, evidence gaps, and where I should focus my questioning.

**What Claude does behind the scenes**

Claude runs all 13 steps of the Full Gate Readiness Analysis:

1. `get_project_summary` — context, current phase, gate target, headline flags
2. `assess_gate_readiness` — overall readiness score, top three gaps, unmet mandatory criteria
3. `get_gate_readiness_history` — readiness trend, which dimensions are declining
4. `compare_gate_readiness` — improvements and deteriorations since last assessment
5. `check_artefact_currency` — missing or stale mandatory artefacts
6. `get_risk_register` — High and Very High risks, ownership, mitigation status
7. `get_assumption_drift` — assumptions drifting from approved basis
8. `get_cost_performance` — CPI, EAC versus BAC, contingency position
9. `check_confidence_divergence` — where stated confidence exceeds evidence
10. `get_armm_report` — ARMM maturity level, blocking topics, dimension scores
11. `suggest_mitigations` — AI-suggested mitigations for top unmitigated risks
12. `run_assurance_workflow` — overall workflow health classification
13. Synthesis into a complete IPA Gate Review report

**The output**

Claude produces a formatted gate review report:

**Overall DCA: Amber-Red**

**Executive summary:** Project Gamma presents a credible strategic case and strong leadership. However, the programme has three dimensions rated Amber-Red or Red that are likely to generate conditions at Gate 3: the financial position is under pressure with CPI at 0.88 and contingency 81% consumed; the ARMM assessment is at Level 1 with two blocking topics in Governance and Controls dimensions; and the risk register contains four High risks that have not been reviewed in over 40 days and have no active mitigation. These are not monitoring issues — they are assurance failures that the review team will need to test directly.

**Conditions proposed:**
1. The programme may not proceed to Gate 4 until a funded cost-to-complete is presented to and approved by HM Treasury, with a revised EAC that reflects the current CPI trajectory rather than a recovery assumption.
2. The programme may not proceed until the ARMM maturity assessment reaches Level 2, confirmed by an independent assessor to the Gate Review Chair.

**Evidence gaps:**
- Benefits realisation plan: the artefact is present but was last updated 11 months ago — pre-dating three significant scope changes. Benefits measurement mechanisms are not documented for four of seven benefits.
- Commercial and Procurement dimension: insufficient data to rate — the contract management framework was referenced but not available in the project store.
- People and Capability: no skills gap assessment found; the programme references a capability review that was planned for Q3 but not yet completed.

**Dimension ratings:** All eight rated individually with evidence citations from the tool outputs. Weakest dimensions: Financials (Red), Governance and Assurance (Amber-Red), Risk Management (Amber-Red). Strongest: Strategic Context and Benefits (Amber-Green), Leadership and Stakeholder Management (Amber-Green).

**How to use it**

This report is your independent baseline. Before the review, compare it to the programme's self-assessment. If they are claiming Amber or Amber-Green across the board and your independent assessment is Amber-Red, the divergence itself is a significant finding — not because either side is necessarily wrong, but because it means the programme's internal assurance mechanism is not detecting the same signals as an independent review. That gap needs to be surfaced in your report.

Use the evidence gaps as your evidence request list. Going into the review, tell the programme team you need the benefits realisation plan (updated), the contract management framework, and the capability review output. Their ability to produce these on request is itself a data point on governance quality.

The two proposed conditions give you a clear structure for the debrief. Present them not as a surprise but as findings the programme needs to address — with a credible action plan and a timeline.

---

### Example 2: Testing a programme's self-assessment

**Scenario**

The project team has submitted a self-assessment rating the programme as Amber/Green. You are not convinced. You want the data to tell you whether the Amber/Green rating is justified, and specifically where stated confidence exceeds objective evidence.

**What to ask Claude**

> The project team is claiming Amber/Green for Project Gamma. I am not convinced. Run the confidence divergence check, look at risk velocity, check for stale risks, check for assumption drift, and run a reference class check on their cost and schedule estimates. What does the data actually say?

**What Claude does behind the scenes**

Claude calls five tools:

1. `check_confidence_divergence(project_id="gamma")` — maps stated confidence against objective indicators across all dimensions, flags material divergences
2. `get_risk_velocity(project_id="gamma")` — identifies rapidly accelerating risks the team may not have escalated
3. `detect_stale_risks(project_id="gamma")` — flags risks not reviewed recently, indicating register maintenance failures
4. `get_assumption_drift(project_id="gamma")` — tracks assumptions that have moved from their approved basis without recognition
5. `run_reference_class_check(project_id="gamma", check_type="cost_and_schedule")` — places the programme's cost and schedule estimates in the context of comparable historical projects

**The output**

Claude returns a divergence report:

**Confidence divergence:** Three significant divergences identified.
- Financials: the programme reports Amber-Green on financials. The objective data shows CPI of 0.88, EAC exceeding BAC by 9%, and contingency 81% consumed. No comparable programme at Gate 3 with these metrics has been rated above Amber on the financial dimension. The stated confidence is not supported by the evidence.
- Risk Management: the programme reports Green on risk management. The risk register contains four High risks with no active mitigation and three risks not reviewed in more than 40 days. A Green risk management rating requires an active, current register with mitigations in place for all High risks. This criterion is not met.
- Delivery Approach and Schedule: the programme reports Amber-Green on schedule. The AI forecast places P80 completion 8 weeks beyond the programme's stated planned date. The programme's schedule confidence relies on a recovery assumption that is not documented and has not been approved through change control.

**Accelerating risks:** Two risks have increased in severity by more than one rating level in the past six weeks. R-07 (data quality failure in source systems) has moved from Low to High. The programme's self-assessment does not mention this risk as having deteriorated. R-11 (third-party dependency on a system not yet procured) is now rated Very High — the programme's self-assessment rates this as Amber.

**Assumption drift:** The cost model relies on a labour rate assumption last validated 18 months ago. Market rates for the relevant technical skills have increased materially since then. This assumption has not been converted to a risk and is not reflected in the contingency calculation.

**Reference class context:** The programme's schedule estimate places it at the P35 percentile for comparable Digital/ICT projects at Gate 3 — meaning 65% of comparable projects take longer than this programme is currently forecasting. The cost estimate is at P42. Both estimates are below the P50 (median) for this project type, which is consistent with optimism bias in the baseline.

**How to use it**

The divergence between Amber/Green and what the data shows is now documented with specific evidence for each dimension. In the review, present these findings as questions rather than accusations — the programme team may have information that explains the divergence, and you need to test that. For each divergence, ask: "Your self-assessment rates this dimension Amber/Green. Our independent data shows [specific finding]. What evidence supports your rating?"

The reference class finding on the schedule estimate is particularly useful. A P35 schedule estimate means the programme is more likely than not to overrun — and the programme team needs to either justify why their project will perform better than 65% of comparable projects, or acknowledge that the estimate reflects optimism bias and apply the appropriate adjustment.

Document these divergences in your gate review report regardless of what the programme team says in the review. The purpose of independent assurance is precisely to surface these gaps — and the fact that they exist is a finding about the programme's internal assurance quality, not just about its delivery performance.

---

### Example 3: Preparing challenge questions for the review panel

**Scenario**

You need to prepare a set of targeted challenge questions for the Gate 3 review panel session. The questions should be grounded in failure patterns for this type of project and calibrated to Gate 3 specifically, rather than generic programme management questions.

**What to ask Claude**

> Prepare eight targeted challenge questions for the Gate 3 review panel for Project Gamma. Ground them in failure patterns for Digital/ICT transformation projects and pre-mortem thinking. For each question, tell me what evidence I should be asking to see.

**What Claude does behind the scenes**

Claude calls three tools:

1. `generate_premortem_questions(project_id="gamma", gate="GATE_3")` — generates pre-mortem questions calibrated to Gate 3 and the project's specific risk profile
2. `get_failure_patterns(project_id="gamma", domain="DIGITAL_ICT")` — returns the most common failure mode indicators for Digital/ICT transformation projects at this stage of delivery
3. `search_knowledge_base(query="Gate 3 failure modes Digital ICT government transformation")` — searches the knowledge base for project-type-specific precedents and review findings

**The output**

Claude returns eight calibrated challenge questions with associated evidence requests:

1. **"What is the project's recovery plan if the integration milestone slips by more than four weeks? Who owns the decision to invoke it and at what trigger point?"**
   Evidence to request: a documented contingency plan with named decision authority and trigger conditions. Failure pattern: 67% of Digital/ICT Gate 3 failures involve a critical path dependency with no documented contingency.

2. **"Your schedule estimate places you at the P35 percentile for comparable projects. What specific factors make this project more likely to deliver faster than the median comparable?"**
   Evidence to request: a schedule risk register with quantified optimism bias adjustment, or a Monte Carlo output showing schedule confidence.

3. **"Four High risks in your register have not been reviewed in more than 40 days. Who is responsible for the risk register, and what governance mechanism exists to ensure risks are kept current?"**
   Evidence to request: the risk management framework, the last three risk committee minutes, evidence that the register is a live document rather than a reporting artefact.

4. **"Your benefits realisation plan was last updated 11 months ago. Which of the three scope changes since then have been reflected in the benefits case, and which benefits are now at risk as a result?"**
   Evidence to request: an updated benefits realisation plan or a formal impact assessment of the scope changes on the benefits case.

5. **"The ARMM assessment shows Level 1 maturity with blocking topics in Governance and Controls. What actions have been taken since the last assessment and what is the plan to reach Level 2 before the next gate?"**
   Evidence to request: a time-bound ARMM improvement plan with named owner and executive sponsor.

6. **"Your cost model uses a labour rate assumption last validated 18 months ago. What is the impact of current market rates on the Estimate at Completion, and has the business case been revalidated at current rates?"**
   Evidence to request: an updated cost model with current labour rates applied, or a sensitivity analysis showing the impact.

7. **"What happens to the business case if the cashable efficiency savings benefit is delayed by 12 months? Is the remaining benefits case sufficient to justify continued investment?"**
   Evidence to request: a benefits sensitivity analysis or a minimum viable benefits threshold agreed with the approving authority.

8. **"Who is the Senior Responsible Owner's deputy if they are unavailable during a critical delivery period? Is there a formal SRO succession and handover plan?"**
   Evidence to request: a documented leadership continuity arrangement. Failure pattern: leadership discontinuity is a top-5 factor in programme failures at Gate 3–4 in comparable projects.

**How to use it**

These eight questions are your panel's working agenda. Distribute them before the review session so the panel can focus their individual questioning — assign two or three questions to each panel member based on their areas of expertise.

The evidence requests are what you ask for before or at the start of the review. If the programme cannot produce the listed evidence in the review session, that is a finding in itself — not evidence of failure, but evidence of governance gaps. Frame each request as: "We would like to see [specific document] to satisfy ourselves on this point. Can you make that available?"

After the review, use the questions and the programme's responses as the basis for your condition and recommendation wording. A question that the programme team could not answer credibly becomes a condition; a question where their answer was credible but needs to be followed through becomes a recommendation.

---

## Tips for best results

**Run the pre-review assessment at least 24 hours before the review.** The analysis takes a few minutes, but you need time to read the output carefully, cross-reference it against the programme's self-assessment documents, and identify the two or three findings you want to probe hardest. Going in with your own independent baseline is significantly more effective than going in cold.

**Compare the platform's DCA to the programme's self-assessment before the review.** Confidence divergence is not just a tool output — it is the core analytical act of any independent review. Document the divergences and test each one in the review session.

**Use evidence gaps as your evidence request list.** Any dimension where the platform flags insufficient evidence is a dimension you need to probe directly. If the evidence does not exist in the platform's data, ask for it from the programme team. If they cannot produce it, that is a finding.

**Apply the reference class check to estimates, not just outcomes.** The most common form of overoptimism in government programmes is not falsifying data — it is using P50 estimates without acknowledging that P50 means a 50% chance of overrunning. The reference class check gives you the historical context to challenge this constructively.

**Document your independent baseline before the review.** Save the pre-review assessment output. After the review, compare your pre-review assessment to your post-review findings. The places where they align confirm that the data is reliable. The places where they diverge — where the programme team provided new information that changed your view — are the governance lessons: that information should have been visible before the review, not surfaced only when challenged.

**Conditions must be blocking and specific.** A condition that says "the programme should improve risk management" is not a condition — it is an aspiration. A condition is: "The programme may not proceed to Gate 4 until the risk register has been reviewed and all High risks have documented, active mitigations, confirmed to the Gate Review Chair by [date]." Be precise.

---

## Related guides and prompts

- `docs/guides/first-project.md` — how to connect Claude to the platform and load a project
- `docs/prompts/role-system-prompts.md` — the Independent Assurance Reviewer system prompt and all other role prompts
- `docs/prompts/research-prompts.md` — Full Gate Readiness Analysis (Research Prompt 1)
- `docs/guides/sro-guide.md` — the SRO's perspective, to understand what the programme is accountable for
- `docs/guides/portfolio-manager-guide.md` — for portfolio-level assurance prioritisation
