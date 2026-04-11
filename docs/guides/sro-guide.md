# Senior Responsible Owner Guide — PDA Platform

## Who this guide is for

You are the Senior Responsible Owner (SRO) for a UK government major project or programme. You are personally accountable to a minister, Departmental Investment Committee, or board for successful delivery. Your time is scarce, and the questions you face — at board meetings, Investment Committees, and Treasury reviews — require authoritative, evidence-based answers rather than programme team assurances.

This guide shows you how to use the PDA Platform to get strategic, board-ready analysis fast. You do not operate tools directly. You have a conversation with Claude, which calls the platform's tools on your behalf and synthesises the results into outputs you can use immediately.

---

## Setting up Claude for your role

Before your first session, paste the SRO system prompt into Claude's **System Prompt** field (found in Claude.ai project settings, or the system prompt configuration in Claude Desktop).

Copy the prompt from `docs/prompts/role-system-prompts.md` — the section headed **Senior Responsible Owner (SRO)**. Once set, you do not need to repeat your role in each message. Claude will apply the SRO lens automatically: leading with delivery confidence, framing everything in terms of strategic objectives and ministerial commitments, and telling you what needs a decision now versus what is being monitored.

If you are also using a research prompt (see below), paste the research prompt as your user message after the system prompt is in place.

---

## What the platform can do for you

- Produce a board-ready programme health summary in under a minute, covering delivery confidence, financial position, benefits status, and top risks
- Assess whether your programme is genuinely ready for an IPA Gate Review — and identify what is blocking passage
- Give you an independent read on your financial position, including reference class context on whether your cost variance is normal for this type of project
- Surface benefits at risk before they become a parliamentary or NAO problem
- Generate the narrative and evidence you need to respond to challenge from your finance director, DG, or Treasury
- Flag divergence between what the programme team is telling you and what the data shows
- Identify which conditions a gate reviewer is likely to impose and what needs to be resolved before the review

---

## Your most useful tools

You do not call these tools directly. Claude uses them based on what you ask. This table tells you what is happening behind the scenes and when each tool is most relevant.

| Tool | What it does for you | When most useful |
|---|---|---|
| `summarise_project_health` | Produces a concise executive summary of overall programme health with DCA framing | Board prep, ministerial briefings |
| `compare_project_health` | Compares health across two or more projects in your portfolio | Cross-cutting accountability, spending reviews |
| `get_benefits_health` | Returns the current status of all registered benefits — on track, at risk, off track | Benefits review boards, PAC preparation |
| `assess_gate_readiness` | Scores readiness against the gate being targeted, with gaps and mandatory criteria | Six to eight weeks before a Gate Review |
| `get_portfolio_health` | Aggregates health across a multi-project portfolio | Programme board, DIC submissions |
| `get_cost_performance` | Returns cost position including CPI, EAC, and variance from approved budget | Finance director challenge, HMT bilateral |
| `get_risk_register` | Returns the current risk register with severity, ownership, and mitigation status | Board risk deep-dives, quarterly returns |
| `run_reference_class_check` | Places your cost or schedule position in the context of comparable historical projects | Justifying variance, challenging optimism bias |
| `check_confidence_divergence` | Flags where stated confidence exceeds what the evidence supports | Pre-review assurance, IPA preparation |
| `generate_narrative` | Produces a DCA narrative in the format expected for GMPP quarterly returns | OGP quarterly returns, CDEL submissions |

---

## Your most useful research prompts

For deeper analysis — gate reviews, benefits realisation reviews — use the structured research prompts in `docs/prompts/research-prompts.md`. These guide Claude through a complete multi-tool analysis and produce a formatted report.

| Prompt | Purpose | When to use |
|---|---|---|
| Full Gate Readiness Analysis (13 steps) | Comprehensive IPA-style gate readiness assessment covering all eight dimensions | Six to eight weeks before a Gate Review |
| Benefits Realisation Review | Green Book-aligned review of all registered benefits, with cascade impact analysis | Benefits review boards, NAO/PAC preparation |

Set your SRO system prompt first, then paste the research prompt as your user message with the project ID substituted in.

---

## Worked examples

### Example 1: Board meeting preparation

**Scenario**

You have a board meeting on Thursday. It is Tuesday afternoon. You need a two-minute briefing on Project Alpha that covers the headline position without operational noise.

**What to ask Claude**

> I have a board meeting on Thursday. Give me a two-minute briefing on Project Alpha — overall confidence, benefits position, cost, and the top risks I need to be across.

**What Claude does behind the scenes**

Claude calls four tools in sequence:

1. `summarise_project_health(project_id="alpha")` — establishes overall DCA and programme health narrative
2. `get_benefits_health(project_id="alpha")` — returns benefits status by benefit, flagging any at risk or off track
3. `get_cost_performance(project_id="alpha")` — returns CPI, EAC versus BAC, spend profile, and contingency position
4. `get_risk_register(project_id="alpha")` — returns open risks ranked by severity, with ownership and mitigation status

**The output**

Claude produces an executive summary structured for direct use in a board briefing:

- **Overall DCA:** Amber. Delivery confidence has declined since the last assessment. Schedule is under pressure in the integration workstream; financial position is within tolerance but contingency has reduced.
- **Benefits:** Seven of nine benefits are on track. Two are at risk — digital take-up (adoption lower than forecast) and cashable efficiency savings (dependent on a system integration that is running late).
- **Cost:** Spend is £12.3m against a £14.0m approved budget for this phase. CPI is 0.91 — slightly over budget but within the 10% tolerance threshold. Estimate at Completion is £48.2m against a BAC of £46.5m. Contingency is 62% consumed.
- **Top three risks:** (1) Supplier delivery risk on the integration milestone — currently unmitigated, risk owner has not updated in six weeks. (2) Ministerial timeline pressure creating scope creep in the final delivery phase. (3) Dependency on another department's API that is not yet confirmed for the Q2 date.

**How to use it**

The output tells you what to lead with at the board and what questions to anticipate. The DCA rating is your headline. The two at-risk benefits give you the substance of a benefits discussion if pressed. The cost position tells you whether you are being asked to explain a variance — if CPI is 0.91, expect a finance question and have the narrative ready. The unmitigated supplier risk is the item most likely to generate a challenge: make sure you have a named action and owner to present. If you want to go deeper on any area before Thursday, ask Claude to run the Schedule and Cost Health Review research prompt for the full EV picture.

---

### Example 2: Responding to a finance director challenge

**Scenario**

Your finance director has flagged that Project Beta is over budget and wants an explanation before the next Departmental Investment Committee. You need to understand the variance, whether it is normal for this type of project, and what narrative to present.

**What to ask Claude**

> My finance director is challenging me on Project Beta's cost overrun. What is the actual position, how does it compare to similar projects, and what should I tell them?

**What Claude does behind the scenes**

Claude calls four tools:

1. `get_cost_performance(project_id="beta")` — establishes the precise variance: planned spend versus actual, CPI, EAC versus BAC, contingency consumed
2. `compare_baseline(project_id="beta")` — shows how the cost position has evolved since the approved baseline, identifying which workstreams account for most of the variance
3. `get_change_impact_summary(project_id="beta")` — identifies approved scope changes that have legitimately increased the cost envelope
4. `run_reference_class_check(project_id="beta", check_type="cost")` — places the cost position in the context of comparable projects from the IPA's historical dataset

**The output**

Claude returns an integrated financial picture with three components:

- **The actual position:** Beta is £3.2m over the approved baseline. The overrun is concentrated in the data migration workstream (£2.1m) and in change-controlled scope additions (£1.4m). Net of approved changes, the underlying variance is £1.8m — a 6% overrun on the workstream budget.
- **Reference class context:** For Digital/ICT projects of comparable size and complexity in the UK government estate, cost overruns at this stage of delivery average 8.4%. Beta's 6% underlying variance is below the class average. The reference class check also shows that 70% of comparable projects in this category experience overruns in the data migration phase specifically.
- **Recommended narrative:** The overrun is concentrated in a workstream that historically overruns in comparable programmes. It is within the reference class norm. The programme is managing it through a combination of contingency draw-down and a scoped reduction in the migration approach. The remaining contingency of £2.1m is assessed as sufficient for the residual risk if the revised migration approach is confirmed.

**How to use it**

Take the reference class framing to the DIC. A 6% overrun on a workstream that routinely overruns in comparable programmes is a manageable position — the question the finance director is really asking is whether you are in control of it, not whether it happened. The narrative Claude produces gives you the answer: you understand where the variance came from, it is within historical norms for this project type, and you have a funded path to completion. If the finance director asks about contingency adequacy, you have the remaining balance and the risk context. If they ask whether the business case is still affordable, ask Claude to run a benefits health check to confirm the benefits case is intact despite the cost movement.

---

### Example 3: Gate 3 readiness — six weeks out

**Scenario**

Your programme is scheduled for a Gate 3 Review in six weeks. You want to know whether you are genuinely ready, what the IPA reviewers are likely to find, and what needs to be resolved before the review team arrives.

**What to ask Claude**

> We are going to Gate 3 in six weeks. Run the full gate readiness analysis and tell me whether we are ready and what I need to resolve before the review.

**What Claude does behind the scenes**

Claude runs the Full Gate Readiness Analysis research prompt — all 13 steps:

1. `get_project_summary` — establishes context, current phase, stated gate target
2. `assess_gate_readiness` — overall readiness score, top three gaps, unmet mandatory criteria
3. `get_gate_readiness_history` — readiness trend over the last three assessments
4. `compare_gate_readiness` — which dimensions have improved or deteriorated since last assessment
5. `check_artefact_currency` — missing or stale mandatory artefacts
6. `get_risk_register` — open High and Very High risks, ownership, mitigation status
7. `get_assumption_drift` — assumptions drifting from their approved basis
8. `get_cost_performance` — financial health and whether the business case is still funded
9. `check_confidence_divergence` — dimensions where stated confidence exceeds evidence
10. `get_armm_report` — ARMM maturity score and blocking topics
11. `suggest_mitigations` — AI-suggested mitigations for top risks
12. `run_assurance_workflow` — full workflow health classification (HEALTHY / ATTENTION_NEEDED / AT_RISK / CRITICAL)
13. Synthesis into a complete IPA-format gate review report

**The output**

Claude produces a formatted gate review report with:

- **Overall DCA:** Amber-Red. The programme has genuine strengths in strategic context and leadership, but three dimensions are rated Amber-Red or Red: Governance and Assurance (ARMM maturity at Level 1 — insufficient for Gate 3 passage), Financials (contingency consumed to 78% with a residual risk exposure that is not fully funded), and Delivery Approach and Schedule (schedule is behind baseline and the AI forecast places P80 completion six weeks beyond the current planned date).
- **Conditions:** Two blocking conditions. The programme may not proceed to the next gate until (1) the ARMM maturity assessment is at Level 2 or above, confirmed to the Gate Review Chair; and (2) a funded cost-to-complete is presented to and approved by HM Treasury.
- **Recommended actions:** Five prioritised actions with suggested owners and target dates, including a rapid ARMM improvement sprint, a reforecast of the EAC, and a risk register refresh.
- **Dimension ratings:** All eight dimensions rated individually with evidence grounded in the tool outputs.

**How to use it**

The DCA and conditions tell you whether you should seek to defer the gate. If you have two blocking conditions that cannot be resolved in six weeks, the honest answer is to request a deferral — attending a gate with known blocking conditions and an Amber-Red DCA puts you in a worse position than deferring and resolving them. The recommended actions give you the immediate work plan. Assign each action to a named individual with accountability to you. The dimension ratings tell you where the gate review team will focus their questioning — brief your programme director on the Governance and Assurance and Financials dimensions specifically. If you want to track progress against the conditions in the weeks before the gate, ask Claude to re-run the gate readiness assessment each week and show the change.

---

## Tips for best results

**Be direct about what you need.** The more specific your question, the more targeted Claude's analysis. "Is Project Alpha ready for its gate?" produces a fuller analysis than "How is Project Alpha doing?"

**Name the audience.** Tell Claude who you are preparing for — a finance director, a minister, a PAC committee, an IPA review team. The framing, language, and level of detail will be calibrated accordingly.

**Use project IDs consistently.** The platform stores project data against a project identifier. Use the same identifier every time to ensure Claude is reading from the correct project record. If you are not sure of the project ID, ask Claude to list available projects.

**Ask for the evidence when you need it.** The SRO system prompt keeps outputs at strategic level by default. If you need to see the underlying data — the full risk register, the detailed EV metrics — ask for it explicitly and Claude will surface it.

**Run gate readiness regularly, not just before the gate.** Running the analysis six weeks out gives you time to act. Running it six months out gives you a programme improvement plan. Schedule a monthly gate readiness check as a standing agenda item for your programme board.

**Combine with the benefits review for PAC preparation.** If you are facing a National Audit Office review or Public Accounts Committee hearing, run the Full Gate Readiness Analysis and the Benefits Realisation Review together. The output covers the questions those bodies ask most frequently.

---

## Related guides and prompts

- `docs/guides/first-project.md` — how to connect Claude to the platform and load your first project
- `docs/prompts/role-system-prompts.md` — the SRO system prompt and all other role prompts
- `docs/prompts/research-prompts.md` — Full Gate Readiness Analysis, Benefits Realisation Review, and Schedule and Cost Health Review prompts
- `docs/guides/pm-guide.md` — your Project Manager's guide, for when you need to understand what your delivery team is working with
- `docs/guides/assurance-reviewer-guide.md` — the Independent Assurance Reviewer guide, to understand how gate reviewers will assess your programme
