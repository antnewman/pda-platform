# Project Manager Guide — PDA Platform

## Who this guide is for

You are the Project Manager responsible for day-to-day delivery of a UK government major project or workstream. You keep the schedule moving, manage cost and resource, resolve blockers, and maintain an accurate picture of progress for your programme board and SRO. You need specific numbers, early warning of problems, and clear action-oriented analysis — not strategic commentary.

This guide shows you how to use the PDA Platform to produce reliable operational analysis. You do not run tools directly. You describe what you need to Claude, and Claude calls the right tools and returns an integrated, actionable output.

---

## Setting up Claude for your role

Paste the PM system prompt into Claude's **System Prompt** field before your first session. Copy it from `docs/prompts/role-system-prompts.md` — the section headed **Project Manager (PM)**.

Once set, Claude will default to the PM lens automatically: RAG ratings per workstream, specific milestone dates, SPI/CPI figures, critical path focus, and a prioritised action list at the end of every assessment. You do not need to ask for these — they are built into how Claude responds when the PM system prompt is active.

For deeper analysis of schedule and cost health, combine the PM system prompt with Research Prompt 3 (Schedule and Cost Health Review) from `docs/prompts/research-prompts.md`.

---

## What the platform can do for you

- Produce a complete project health dashboard — RAG by workstream, EV metrics, critical path status, and top risks — in a single conversation turn
- Detect schedule outliers: tasks with hidden float consumption, unusual durations, or stale progress data that your project team may not have flagged
- Generate an AI-forecast completion date with a confidence interval, giving you an independent read on whether your current plan is realistic
- Identify which risks are accelerating and which have no active mitigation — before they become issues
- Detect stale risk registers and prompt a structured refresh
- Surface resource conflicts: who is over-committed, when the conflict peaks, and which workstreams are affected
- Quantify change pressure on your schedule and budget, so you can see whether approved changes are cumulatively threatening delivery
- Produce board-ready reports with numbers, not narrative, so you walk into your project board with the facts

---

## Reading Verified Autonomy response annotations

When you ask Claude for a schedule forecast, an EV summary, or a risk-register refresh, the response now carries machine-checked trust signals as additional fields. They are short, structured, and give you specific operational information you can act on.

**`_calibration` on schedule and cost forecasts** — When you run `forecast_completion` or `run_schedule_simulation`, the response carries a `_calibration.p50_band` and `_calibration.p80_band` — each with `lower`, `upper`, and `half_width`. These are conformal prediction intervals based on the project's history of forecast-versus-actual residuals. **The band is your planning range, not the point estimate.** A wide P80 half-width (more than 4 weeks on a 6-month forecast) tells you your team's previous forecasts have been materially wrong; budget the upper bound for resource planning, not the headline P80 date. When `_calibration.status` is `NOT_COMPUTED`, the project has no stored residuals yet — start recording (forecast, actual) pairs after each milestone to build calibration history.

**`_groundedness`** — Carries a verdict (`GROUNDED` / `UNGROUNDED`) and a list of `ungrounded_terms` — words that appear in Claude's prose but have no source in your project data. If a risk-register refresh or mitigation suggestion contains ungrounded terms, those are the lines to check before they go into the register.

**`_quality.potential_hallucinations`** — When `true`, do not paste the analysis into your monthly board pack without verification. Ask Claude to regenerate with stricter grounding, or check the suggested mitigations against your operational knowledge before accepting them.

**L5 rejection** — Occasionally a generated risk narrative or AI mitigation comes back as `{"error": "guardrail_rejected", ...}` — a deterministic policy block. The original prose is suppressed by design. Regenerate with cleaner inputs rather than trying to render the rejection envelope.

For the underlying framework see [Verified Autonomy overview](../verified-autonomy-overview.md).

---

## Your most useful tools

| Tool | What it does for you | When most useful |
|---|---|---|
| `assess_health` | Overall project health score with component RAG ratings by dimension | End-of-month health check, board prep |
| `get_critical_path` | Returns the critical path with float, owned tasks, and near-critical paths | Milestone slippage investigation, schedule recovery |
| `detect_outliers` | Flags tasks with unusual duration, zero float, or stale progress data | Schedule quality audit, pre-board review |
| `forecast_completion` | AI-generated completion date forecast (P50 and P80) compared to planned date | Milestone at-risk assessment, replanning |
| `compute_ev_metrics` | SPI, CPI, EAC, TCPI — the full Earned Value picture | Monthly reporting, finance director briefing |
| `get_cost_performance` | Spend profile, CPI trend, contingency position, cost-to-complete | Budget challenge, contingency draw-down approval |
| `get_risk_register` | Full risk register with severity, ownership, and mitigation status | Risk review meetings, board reporting |
| `get_risk_velocity` | Tracks how quickly risks are escalating — identifies accelerating risks | Early warning, pre-board risk review |
| `detect_stale_risks` | Flags risks that have not been reviewed within the expected update cycle | Risk register refresh, ARMM compliance |
| `detect_resource_conflicts` | Identifies double-committed team members or scarce skills | Resource planning, workstream sequencing |
| `analyse_change_pressure` | Quantifies the cumulative schedule and cost impact of approved changes | Change control review, baseline reforecast |
| `compare_baseline` | Schedule and cost variance versus the approved baseline | Variance reporting, rebaseline decisions |
| `suggest_mitigations` | AI-suggested mitigations for your top open risks | Risk register refresh, mitigation planning |
| `evaluate_calibration` | Measures whether the team's previous forecasts predicted actual outcomes — returns Expected Calibration Error (ECE) plus reliability-diagram bins | Quarterly forecasting health check, post-milestone retrospective, validating whether stated SPI/CPI confidence is reliable |

---

## Your most useful research prompts

| Prompt | Purpose | When to use |
|---|---|---|
| Schedule and Cost Health Review (Research Prompt 3) | 11-step integrated analysis covering critical path, EV metrics, outlier detection, resource loading, and risk cross-reference | Monthly health check, milestone slippage review, pre-board preparation |

Set the PM system prompt first, then paste Research Prompt 3 as your user message with your project ID substituted in. Claude will work through all 11 steps and produce a structured schedule and cost health report.

---

## Worked examples

### Example 1: End-of-month health dashboard

**Scenario**

It is the last working day of the month. You need to walk into your project board tomorrow with a complete, accurate picture of where the project stands — schedule, cost, risks, and any stale data problems before the board sees them.

**What to ask Claude**

> It is end of month. Give me a full health dashboard for Project Alpha — RAG by workstream, EV metrics, critical path, top risks, and flag anything in the risk register that is stale.

**What Claude does behind the scenes**

Claude calls six tools in sequence:

1. `assess_health(project_id="alpha")` — overall health score and RAG ratings by workstream
2. `get_critical_path(project_id="alpha")` — critical path tasks, total float, near-critical paths
3. `compute_ev_metrics(project_id="alpha")` — SPI, CPI, EAC, TCPI
4. `get_cost_performance(project_id="alpha")` — spend profile, contingency position, cost-to-complete
5. `get_risk_register(project_id="alpha")` — full risk register, ranked by severity
6. `detect_stale_risks(project_id="alpha")` — risks not reviewed within the expected cycle

**The output**

Claude returns a structured dashboard:

**Overall health: Amber.** Three workstreams are Green, one is Amber (Integration), one is Red (Data Migration).

**EV metrics:**
- SPI: 0.87 — schedule is behind planned progress
- CPI: 0.93 — cost is slightly over plan
- EAC: £52.4m against a BAC of £49.0m — projected overrun of £3.4m
- TCPI: 1.08 — the remaining work requires 8% greater efficiency than the project has achieved to date

**Critical path:** 14 tasks on the critical path. Total float is 12 days. Three near-critical paths have float of 3 days or fewer — any slip on these converts to critical path risk immediately. Two critical path tasks are unowned.

**Top five risks:** Ranked by severity, with the two High risks flagged as the immediate board-level concern. Both have mitigations listed; one has not been updated in 47 days.

**Stale register alert:** Four risks have not been reviewed in more than 30 days. The oldest is 61 days since last update.

**How to use it**

The SPI of 0.87 is your lead number for the board. It tells the story: the project is behind pace, the Data Migration workstream is the primary driver, and the EAC suggests you are heading toward a budget conversation. The two unowned critical path tasks need owners assigned before the board meeting — flag them to the relevant workstream leads today. The stale register is a governance gap: four risks have not been reviewed in over a month. Before the board meeting, email the risk owners and ask for a same-day update, or escalate if they do not respond. If the board asks why the risk register is not current, the answer needs to be better than "we haven't got around to it."

The TCPI of 1.08 is worth understanding before the board: it means you need to be 8% more efficient for the rest of the project to land on budget. That is achievable but requires deliberate action. If anyone at the board asks whether the EAC is realistic, the honest answer is that it is achievable if efficiency improves — which means identifying specifically what will improve it.

---

### Example 2: Milestone at risk — how bad is it?

**Scenario**

You have a strong suspicion that the Q2 milestone will not be met. The integration workstream lead has not given you a straight answer. You need an independent, data-driven view on how bad the slip is before you escalate to the SRO.

**What to ask Claude**

> I think we are going to miss the Q2 milestone. Forecast the completion date, show me what is driving any slip, and tell me what resource constraints are making it worse.

**What Claude does behind the scenes**

Claude calls five tools:

1. `forecast_completion(project_id="alpha")` — AI-generated P50 and P80 completion dates versus the planned Q2 date
2. `compare_baseline(project_id="alpha")` — schedule variance by workstream versus the approved baseline
3. `get_critical_path(project_id="alpha")` — which specific tasks are on the critical path and where float has been consumed
4. `detect_outliers(project_id="alpha")` — tasks with stale progress, zero float, or anomalous durations that may not be visible in the schedule summary
5. `analyse_resource_loading(project_id="alpha")` — resource over-allocations on critical path tasks in the next 90 days

**The output**

Claude returns an integrated slip analysis:

**Forecast completion:** P50 is 14 April — six weeks beyond the Q2 planned date of 28 February. P80 is 3 June, eleven weeks late. The AI forecast is based on current SPI trajectory; it assumes no recovery action. `_calibration.p80_band` reports lower 13 May, upper 24 June (half-width 21 days) at 80% nominal coverage — that is the range you should plan against, not the headline P80 date.

**Drivers of the slip:** The integration workstream accounts for 73% of the schedule variance. Within the integration workstream, three tasks are responsible for the bulk of the delay: API configuration (5 weeks behind), system testing (not yet started, was planned to have started 3 weeks ago), and sign-off by the third-party vendor (no date confirmed). All three sit on the critical path.

**Outlier detection:** Two tasks flagged. One task — "Vendor UAT environment setup" — has been marked as 30% complete for 19 days with no progress update. The other — "Data migration dry run" — has a duration of 47 days, nearly double the comparable tasks in the same workstream.

**Resource constraints:** The integration lead is the named resource on four critical path tasks simultaneously in February. She is also committed to two other department projects during the same period. There is no named deputy. This resource concentration creates a single point of failure that is not visible in the schedule.

**How to use it**

The P50 forecast of 14 April gives you a defensible, evidence-based number to take to the SRO — one that is not the programme team's optimistic narrative. Six weeks of slip on a Q2 milestone is significant enough to require immediate escalation. The resource concentration issue is your most actionable finding: a single person on four critical path tasks with no deputy is a governance failure that the SRO needs to know about and that you can fix.

Before escalating, clarify two things: whether the vendor UAT task at 30% is genuinely stuck or just not updated (ask the task owner today), and whether the data migration dry run can be split or reduced in scope. These are the two places where you might recover a week or two. The realistic revised date to present to the board is the P50 (14 April) with a clear statement of what the recovery plan would need to achieve to pull it back to Q2 — and an honest assessment of whether that is achievable.

---

### Example 3: Risk register refresh

**Scenario**

Your risk register has not been updated in six weeks. You have a project board next week. You need to run a proper risk review, identify which risks have moved, and produce an updated register with AI-suggested mitigations for the risks that have no active mitigation in place.

**What to ask Claude**

> My risk register has not been updated in six weeks. Help me run a proper risk review — which risks are accelerating, which have no mitigation, and suggest mitigations for the top ones that need them.

**What Claude does behind the scenes**

Claude calls four tools:

1. `detect_stale_risks(project_id="alpha")` — identifies all risks not reviewed within the expected cycle, with days since last update
2. `get_risk_velocity(project_id="alpha")` — ranks risks by how quickly their probability or impact is changing — the accelerating risks
3. `get_risk_register(project_id="alpha")` — full register with current ratings, owners, and mitigation status
4. `suggest_mitigations(project_id="alpha")` — AI-generated mitigation suggestions for the top unmitigated risks

**The output**

Claude returns a structured risk review:

**Stale register summary:** 8 of 22 risks have not been reviewed in more than 30 days. The stale risks include two that are currently rated High — these are the immediate governance concern. The register has a stale score of 36% — above the 20% threshold that typically triggers an ARMM finding.

**Accelerating risks (by velocity):** Three risks have shown a significant increase in probability rating over the last two review cycles. Risk R-04 (supplier capacity) has moved from Low-Medium to High in six weeks. Risk R-09 (regulatory approval timeline) has moved from Medium to High-Very High. Risk R-14 (key person dependency) is new and has no baseline probability — it was added to the register with no owner and no mitigation.

**Risks with no active mitigation:** Five risks currently have no mitigation recorded, including two rated High. The AI identifies these as the most urgent gaps.

**AI-suggested mitigations:**
- R-04 (supplier capacity): Trigger contractual milestone review clause. Obtain written confirmation from supplier of capacity commitment through Q3. Identify and pre-qualify a secondary supplier.
- R-09 (regulatory approval): Engage regulatory contact point now to understand the approval timeline. Commission a pre-submission review if available. Build a 4-week buffer into the schedule downstream of the approval milestone.
- R-14 (key person dependency): Document knowledge and decision authority for the named individual. Identify and brief a designated deputy. Consider a retention arrangement if the individual is in a competitive skill area.

**How to use it**

Send the stale risk list to risk owners today with a 48-hour deadline to update their entries before the board. For the two High risks that are stale, do not wait for the owners — call them. R-04 and R-09 are the ones to focus on: they have both accelerated significantly and have no mitigation. The AI-suggested mitigations give you a starting point for the conversation with risk owners; they are not a substitute for the owners' judgement, but they give you something concrete to discuss.

R-14 with no owner is a register quality failure — someone registered it and walked away. Assign an owner in the meeting and record that the AI-suggested mitigation has been reviewed and either adopted or replaced with a documented alternative.

At the board, present the stale register score as a finding you are actively resolving, not a problem you discovered at the last minute. The action plan is the evidence that you are on top of it.

---

### Example 4: A schedule forecast carries a wider conformal band than expected

**Scenario**

You are preparing for next Tuesday's go/no-go on the Phase 3 milestone. You run `run_schedule_simulation` to confirm the P80 delivery date. The simulation returns a P80 of 12 June — comfortably ahead of the 30 June commitment. But the `_calibration.p80_band` carries a half-width of 8 weeks: the band lower is 17 April, upper is 7 August. The simulation says 12 June; the calibrated band says the true outcome will fall somewhere between mid-April and early August with 80% confidence. You need to understand whether to trust the headline number or plan against the band.

**What to ask Claude**

> The P80 from the schedule simulation is 12 June but the calibration band is 17 April to 7 August. Why is the band so wide? Pull the residual history and tell me what is driving it.

**What Claude does behind the scenes**

The wide band signals that the project's past forecasts have been wrong by large margins. Claude reads the calibration history:

1. Inspects the `_calibration` field returned by the simulation
2. Calls the store directly via Claude's analytical tools to retrieve the project's `simulation_residuals` (the (forecast, actual) pairs recorded after each prior milestone)
3. Reports the residual distribution: mean, range, and how many residuals support the current band

**The output**

Claude returns a calibration retrospective:

- **Residual history:** 7 prior schedule forecasts recorded. Mean P80 residual: +43 days (actuals consistently 6 weeks later than forecast). Largest residual: +71 days. Range: -8 days (one early delivery) to +71 days. The mean residual is 6 weeks late, so the conformal band correctly reports a wide upper bound.
- **Pattern:** The team's forecasts have been systematically too optimistic. Of the 7 milestones, 6 delivered later than P80. The optimism is concentrated in workstreams that depend on third-party vendor sign-off — vendor delays account for 4 of the 5 worst residuals.
- **Implication:** The simulation's headline P80 of 12 June reflects today's plan. The conformal band — 17 April to 7 August — reflects what tends to happen to this team's forecasts under the same conditions. The upper bound (7 August) is more than five weeks beyond the 30 June commitment.

**How to use it**

Three operational moves. **First**, replan against the upper band, not the headline. If the upper bound is 7 August and the commitment is 30 June, you have a 5-week gap to close — that is a board-grade item, not a workstream-lead conversation. **Second**, name the failure mode in your replan: vendor sign-off is the dominant residual driver, so the recovery plan needs a named vendor escalation path, not just an internal sprint. **Third**, track the band, not just the point estimate, on every subsequent forecast. The wide band is the platform telling you "this team's forecasts are not yet reliable" — narrowing the band requires either better forecasting (record more (forecast, actual) pairs and run `evaluate_calibration` to see if ECE improves) or genuinely reducing uncertainty in the schedule itself. Until the band narrows, plan against the band.

For the underlying conformal-prediction primitive and the implications for governance, see the L4 section of [Verified Autonomy overview](../verified-autonomy-overview.md).

---

## Tips for best results

**Load your schedule file before running analysis.** Tools like `get_critical_path`, `detect_outliers`, and `forecast_completion` read from the project store. If you have not loaded the project in the current session, call `load_project` first. You can do this by telling Claude: "Load the project from [file path] before running the analysis."

**Give Claude the project ID.** Every time you start a session, tell Claude which project you are working on — for example, "I am working on Project Alpha, project ID alpha-2024." This ensures all tool calls are directed at the right project record.

**Ask for numbers, not narrative.** The PM system prompt is set up to prioritise specific figures over general commentary. If you are getting too much narrative, tell Claude: "Give me the numbers first, then the interpretation."

**Use the end-of-month workflow as a template.** The first worked example is designed to be repeated every month. You can save the prompt text and use it as a standing monthly health check. Over time, the trend data becomes as useful as the point-in-time assessment.

**Ask Claude to flag the escalation-worthy items separately.** At the end of any analysis, ask: "Which of these findings do I need to escalate to the SRO, and which can I manage myself?" Claude will apply the PM lens to separate operational management items from governance escalations.

**For resource conflicts, name the individuals.** The `detect_resource_conflicts` tool works best when it has named resource data. If your schedule file includes named resources on tasks, the conflict detection is significantly more precise.

---

## Related guides and prompts

- `docs/guides/first-project.md` — how to connect Claude to the platform and load your first project
- `docs/prompts/role-system-prompts.md` — the PM system prompt and all other role prompts
- `docs/prompts/research-prompts.md` — Schedule and Cost Health Review (Research Prompt 3)
- `docs/guides/sro-guide.md` — your SRO's guide, to understand what they need from you and when
- `docs/guides/assurance-reviewer-guide.md` — what a gate reviewer will look for in your project data
